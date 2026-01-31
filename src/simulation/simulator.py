"""
Simulation Engine
Time-stepped simulation of Solar-Direct power systems with fault injection.
"""

import math
import sys
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.components.solar_panel import SolarPanel
from src.components.battery import Battery
from src.components.load import Load
from src.controller.power_controller import PowerController


class Simulator:
    """
    Time-stepped simulator for Solar-Direct energy management.

    Features:
    - Realistic solar irradiance curves (based on time of day)
    - Fault injection (cloud cover, load spikes, panel failures)
    - Comprehensive history tracking
    - Statistical analysis
    """

    def __init__(
        self,
        solar_panel: SolarPanel,
        battery: Battery,
        loads: List[Load],
        timestep_s: int = 60,
        start_hour: int = 0
    ):
        """
        Initialize the simulator.

        Args:
            solar_panel: Solar panel array
            battery: Battery storage
            loads: List of loads
            timestep_s: Simulation timestep in seconds (default 60s = 1 minute)
            start_hour: Starting hour of day (0-23)
        """
        self.solar_panel = solar_panel
        self.battery = battery
        self.loads = loads
        self.timestep_s = timestep_s
        self.start_hour = start_hour

        self.controller = PowerController(solar_panel, battery, loads)

        # History tracking
        self.history: List[Dict[str, Any]] = []
        self.current_time = 0  # seconds since start

    def calculate_solar_irradiance(self, hour_of_day: float) -> float:
        """
        Calculate realistic solar irradiance based on time of day.

        Uses a sine curve to model sun position:
        - Night (hour 0-6, 18-24): 0.0
        - Dawn/dusk: Gradual increase/decrease
        - Peak (hour 12): 1.0

        Args:
            hour_of_day: Hour of day (0.0 to 24.0)

        Returns:
            Irradiance level (0.0 to 1.0)
        """
        # Sunrise at 6am, sunset at 6pm (simplified)
        sunrise_hour = 6.0
        sunset_hour = 18.0

        if hour_of_day < sunrise_hour or hour_of_day > sunset_hour:
            return 0.0

        # Calculate position in day (0 to pi)
        day_position = (hour_of_day - sunrise_hour) / (sunset_hour - sunrise_hour)

        # Sine curve for realistic solar intensity
        irradiance = math.sin(day_position * math.pi)

        return max(0.0, min(1.0, irradiance))

    def inject_cloud_cover(
        self,
        start_time_s: int,
        duration_s: int,
        reduction_factor: float = 0.7
    ) -> None:
        """
        Schedule a cloud cover event.

        Args:
            start_time_s: When to start (seconds from simulation start)
            duration_s: How long it lasts (seconds)
            reduction_factor: How much to reduce solar (0.7 = 70% reduction)
        """
        if not hasattr(self, 'faults'):
            self.faults = []

        self.faults.append({
            'type': 'cloud_cover',
            'start': start_time_s,
            'end': start_time_s + duration_s,
            'reduction': reduction_factor
        })

    def inject_load_spike(
        self,
        start_time_s: int,
        load_name: str,
        spike_power_w: float,
        duration_s: int
    ) -> None:
        """
        Schedule a temporary load spike.

        Args:
            start_time_s: When to start (seconds from simulation start)
            load_name: Which load to spike
            spike_power_w: Additional power draw
            duration_s: How long it lasts
        """
        if not hasattr(self, 'faults'):
            self.faults = []

        self.faults.append({
            'type': 'load_spike',
            'start': start_time_s,
            'end': start_time_s + duration_s,
            'load_name': load_name,
            'spike_power': spike_power_w
        })

    def inject_panel_failure(
        self,
        start_time_s: int,
        degradation: float = 0.5
    ) -> None:
        """
        Schedule a panel degradation event.

        Args:
            start_time_s: When to occur
            degradation: How much to degrade (0.5 = 50% loss)
        """
        if not hasattr(self, 'faults'):
            self.faults = []

        self.faults.append({
            'type': 'panel_failure',
            'start': start_time_s,
            'degradation': degradation
        })

    def _apply_faults(self) -> List[str]:
        """
        Apply any active faults at current simulation time.

        Returns:
            List of fault descriptions
        """
        active_faults = []

        if not hasattr(self, 'faults'):
            return active_faults

        for fault in self.faults:
            if fault['type'] == 'cloud_cover':
                if fault['start'] <= self.current_time < fault['end']:
                    # Reduce solar irradiance
                    current_irradiance = self.solar_panel.current_irradiance
                    reduced_irradiance = current_irradiance * (1 - fault['reduction'])
                    self.solar_panel.update_irradiance(reduced_irradiance)
                    active_faults.append(
                        f"☁️  Cloud cover active ({fault['reduction']:.0%} reduction)"
                    )

            elif fault['type'] == 'load_spike':
                if fault['start'] <= self.current_time < fault['end']:
                    # Find and spike the load
                    for load in self.loads:
                        if load.name == fault['load_name']:
                            if not hasattr(load, '_original_power'):
                                load._original_power = load.power_draw_w
                            load.power_draw_w = load._original_power + fault['spike_power']
                            active_faults.append(
                                f"⚡ Load spike: {fault['load_name']} "
                                f"+{fault['spike_power']}W"
                            )
                            break
                elif self.current_time >= fault['end']:
                    # Restore original power
                    for load in self.loads:
                        if load.name == fault['load_name'] and hasattr(load, '_original_power'):
                            load.power_draw_w = load._original_power
                            delattr(load, '_original_power')

            elif fault['type'] == 'panel_failure':
                if self.current_time == fault['start']:
                    self.solar_panel.apply_degradation(fault['degradation'])
                    active_faults.append(
                        f"⚠️  Panel failure: {fault['degradation']:.0%} degradation"
                    )

        return active_faults

    def run(self, duration_hours: int) -> pd.DataFrame:
        """
        Run the simulation for specified duration.

        Args:
            duration_hours: How many hours to simulate

        Returns:
            DataFrame with complete simulation history
        """
        duration_s = duration_hours * 3600
        num_steps = int(duration_s / self.timestep_s)

        print(f"Starting simulation: {duration_hours} hours ({num_steps} timesteps)")
        print(f"Initial battery SOC: {self.battery.state_of_charge():.1%}")
        print("-" * 80)

        for step in range(num_steps):
            # Calculate current hour of day
            current_hour = (self.start_hour + (self.current_time / 3600)) % 24

            # Update solar irradiance based on time of day
            base_irradiance = self.calculate_solar_irradiance(current_hour)
            self.solar_panel.update_irradiance(base_irradiance)

            # Apply any active faults
            active_faults = self._apply_faults()

            # Make power routing decision
            decision = self.controller.decide_power_routing(self.timestep_s)

            # Execute the decision (update battery state)
            if decision['power_to_battery'] > 0:
                self.battery.charge(decision['power_to_battery'], self.timestep_s)
            elif decision['power_from_battery'] > 0:
                self.battery.discharge(decision['power_from_battery'], self.timestep_s)

            # Record history
            self.history.append({
                'timestamp': self.current_time,
                'hour_of_day': current_hour,
                'solar_irradiance': self.solar_panel.current_irradiance,
                'solar_output_w': self.solar_panel.current_output(),
                'battery_soc': self.battery.state_of_charge(),
                'battery_charge_wh': self.battery.current_charge_wh,
                'power_from_solar': decision['power_from_solar'],
                'power_from_battery': decision['power_from_battery'],
                'power_to_battery': decision['power_to_battery'],
                'total_demand': decision['total_demand'],
                'total_available': decision['total_available'],
                'active_loads': ','.join(decision['active_loads']),
                'shed_loads': ','.join(decision['shed_loads']),
                'num_active_loads': len(decision['active_loads']),
                'num_shed_loads': len(decision['shed_loads']),
                'active_faults': ','.join(active_faults) if active_faults else 'None',
                'decisions': ' | '.join(decision['decisions'])
            })

            # Progress reporting every hour
            if step % (3600 / self.timestep_s) == 0:
                hours_elapsed = self.current_time / 3600
                print(
                    f"[Hour {hours_elapsed:.0f}] "
                    f"Solar: {self.solar_panel.current_output():.0f}W | "
                    f"Battery: {self.battery.state_of_charge():.1%} | "
                    f"Demand: {decision['total_demand']:.0f}W | "
                    f"Active: {len(decision['active_loads'])}/{len(self.loads)} loads"
                )

            # Advance time
            self.current_time += self.timestep_s

        print("-" * 80)
        print("Simulation complete!")

        # Convert to DataFrame
        df = pd.DataFrame(self.history)

        # Print summary statistics
        self._print_summary(df)

        return df

    def _print_summary(self, df: pd.DataFrame) -> None:
        """Print summary statistics from simulation."""
        print("\n" + "=" * 80)
        print("SIMULATION SUMMARY")
        print("=" * 80)

        # Energy statistics
        total_solar_energy = df['power_from_solar'].sum() * (self.timestep_s / 3600)
        total_battery_discharge = df['power_from_battery'].sum() * (self.timestep_s / 3600)
        total_battery_charge = df['power_to_battery'].sum() * (self.timestep_s / 3600)
        total_demand_energy = df['total_demand'].sum() * (self.timestep_s / 3600)

        print(f"\nEnergy Flow:")
        print(f"  Total solar energy delivered:    {total_solar_energy:.2f} Wh")
        print(f"  Total battery discharge:          {total_battery_discharge:.2f} Wh")
        print(f"  Total battery charge:             {total_battery_charge:.2f} Wh")
        print(f"  Total demand:                     {total_demand_energy:.2f} Wh")

        # Battery statistics
        final_soc = df['battery_soc'].iloc[-1]
        min_soc = df['battery_soc'].min()
        max_soc = df['battery_soc'].max()

        print(f"\nBattery:")
        print(f"  Final SOC:     {final_soc:.1%}")
        print(f"  Min SOC:       {min_soc:.1%}")
        print(f"  Max SOC:       {max_soc:.1%}")

        # Load statistics
        critical_loads = [load for load in self.loads if load.priority == 0]
        if critical_loads:
            critical_uptime = df[df['shed_loads'].str.contains('|'.join([l.name for l in critical_loads]), na=False) == False].shape[0] / len(df)
            print(f"\nCritical Load Uptime: {critical_uptime:.1%}")

        # Shedding events
        total_shedding_events = df[df['num_shed_loads'] > 0].shape[0]
        print(f"\nLoad Shedding:")
        print(f"  Total timesteps with shedding:    {total_shedding_events}")
        print(f"  Percentage of time:               {(total_shedding_events/len(df)):.1%}")

        for load in self.loads:
            print(f"  {load.name}: shed {load.shed_count()} times")

        print("=" * 80 + "\n")
