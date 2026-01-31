"""
Power Controller
Intelligent routing and load management for Solar-Direct systems.
"""

from typing import Dict, List, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.components.solar_panel import SolarPanel
from src.components.battery import Battery
from src.components.load import Load


class PowerController:
    """
    The brain of the Solar-Direct system.

    Makes real-time decisions about:
    - Power routing (solar → loads, battery → loads)
    - Load shedding (which loads to turn off)
    - Battery management (charging, reserve capacity)

    Philosophy:
    1. Solar-first: Use free solar power whenever available
    2. Battery-second: Tap storage when solar insufficient
    3. Shed loads: Prioritize critical over non-critical
    4. Maintain reserves: Keep battery capacity for critical loads
    """

    def __init__(
        self,
        solar_panel: SolarPanel,
        battery: Battery,
        loads: List[Load],
        critical_reserve_soc: float = 0.20,
        hysteresis_margin: float = 0.10
    ):
        """
        Initialize the power controller.

        Args:
            solar_panel: Solar panel array
            battery: Battery storage system
            loads: List of electrical loads
            critical_reserve_soc: Battery SOC to reserve for critical loads only
            hysteresis_margin: Power margin to prevent oscillation (10% = shed at 90%, restore at 110%)
        """
        self.solar_panel = solar_panel
        self.battery = battery
        self.loads = loads
        self.critical_reserve_soc = critical_reserve_soc
        self.hysteresis_margin = hysteresis_margin

        # Track previous state for hysteresis
        self._previous_shed_loads = set()

    def decide_power_routing(self, timestep_s: float = 60) -> Dict[str, Any]:
        """
        Make power routing decisions for current timestep.

        This is the core decision-making logic of the Solar-Direct system.

        Args:
            timestep_s: Duration of this timestep in seconds (default 60s = 1 minute)

        Returns:
            Decision dictionary with:
                - power_from_solar: Watts from solar
                - power_from_battery: Watts from battery
                - power_to_battery: Watts charging battery
                - active_loads: List of active load names
                - shed_loads: List of shed load names
                - decisions: List of decision reasoning strings
        """
        decisions = []

        # Calculate available power
        solar_output = self.solar_panel.current_output()
        decisions.append(f"Solar output: {solar_output:.1f}W")

        # Calculate critical load demand (priority 0)
        critical_loads = [load for load in self.loads if load.priority == 0]
        critical_demand = sum(load.power_draw_w for load in critical_loads)
        decisions.append(f"Critical load demand: {critical_demand:.1f}W")

        # Calculate total current demand (all active loads)
        total_demand = sum(load.current_draw() for load in self.loads)
        decisions.append(f"Total demand: {total_demand:.1f}W")

        # Check battery state
        battery_soc = self.battery.state_of_charge()
        in_reserve_mode = battery_soc <= self.critical_reserve_soc

        if in_reserve_mode:
            decisions.append(
                f"⚠️  Battery at {battery_soc:.1%} - RESERVE MODE (critical loads only)"
            )

        # Determine available battery power
        if in_reserve_mode:
            # In reserve mode, battery only available for critical loads
            max_battery_discharge = critical_demand
            decisions.append("Battery reserved for critical loads only")
        else:
            # Normal mode - battery available for all loads
            max_battery_discharge = self.battery.max_discharge_rate_w

        # Calculate actual available battery power
        available_battery = min(
            max_battery_discharge,
            (self.battery.available_discharge_capacity() * 3600) / timestep_s
        )

        # Calculate total available power
        total_available = solar_output + available_battery
        decisions.append(f"Total available power: {total_available:.1f}W")

        # Implement load shedding if necessary
        if total_demand > total_available:
            decisions.append(
                f"⚠️  Demand ({total_demand:.1f}W) exceeds supply ({total_available:.1f}W) - "
                "implementing load shedding"
            )
            self._shed_loads(total_available, decisions)
        else:
            # Check if we can restore previously shed loads (hysteresis)
            restore_threshold = total_available * (1 + self.hysteresis_margin)
            if total_demand < restore_threshold:
                self._restore_loads(restore_threshold, decisions)

        # Recalculate demand after shedding/restoring
        total_demand = sum(load.current_draw() for load in self.loads)

        # Route power: solar first, then battery
        power_from_solar = min(solar_output, total_demand)
        power_from_battery = max(0, total_demand - solar_output)

        # If solar exceeds demand, charge battery
        excess_solar = max(0, solar_output - total_demand)
        power_to_battery = 0

        if excess_solar > 0 and not in_reserve_mode:
            # Only charge if not in reserve mode (or if below critical reserve)
            max_charge = min(
                excess_solar,
                self.battery.max_charge_rate_w,
                (self.battery.available_charge_capacity() * 3600) / timestep_s
            )
            if max_charge > 0:
                power_to_battery = max_charge
                decisions.append(f"Charging battery with {power_to_battery:.1f}W excess solar")

        # Prepare results
        active_loads = [load.name for load in self.loads if load.is_active]
        shed_loads = [load.name for load in self.loads if not load.is_active]

        return {
            "power_from_solar": power_from_solar,
            "power_from_battery": power_from_battery,
            "power_to_battery": power_to_battery,
            "active_loads": active_loads,
            "shed_loads": shed_loads,
            "decisions": decisions,
            "battery_soc": battery_soc,
            "total_demand": total_demand,
            "total_available": total_available
        }

    def _shed_loads(self, available_power: float, decisions: List[str]) -> None:
        """
        Shed loads starting with lowest priority until demand <= supply.

        Args:
            available_power: Total power available (solar + battery)
            decisions: List to append decision reasoning to
        """
        # Sort loads by priority (lowest priority = shed first)
        sorted_loads = sorted(self.loads, key=lambda l: l.priority, reverse=True)

        current_demand = sum(load.current_draw() for load in self.loads)

        for load in sorted_loads:
            if current_demand <= available_power:
                break

            if load.is_active:
                load.deactivate()
                current_demand -= load.power_draw_w
                decisions.append(
                    f"🔴 SHED: {load.name} ({load.priority_label()}, {load.power_draw_w}W)"
                )
                self._previous_shed_loads.add(load.name)

    def _restore_loads(self, available_power: float, decisions: List[str]) -> None:
        """
        Restore previously shed loads if sufficient power available (with hysteresis).

        Args:
            available_power: Total power available with hysteresis margin
            decisions: List to append decision reasoning to
        """
        # Sort loads by priority (highest priority = restore first)
        sorted_loads = sorted(self.loads, key=lambda l: l.priority)

        current_demand = sum(load.current_draw() for load in self.loads)

        for load in sorted_loads:
            if not load.is_active and load.name in self._previous_shed_loads:
                potential_demand = current_demand + load.power_draw_w

                if potential_demand <= available_power:
                    load.activate()
                    current_demand = potential_demand
                    decisions.append(
                        f"🟢 RESTORE: {load.name} ({load.priority_label()}, {load.power_draw_w}W)"
                    )
                    self._previous_shed_loads.remove(load.name)

    def get_critical_loads(self) -> List[Load]:
        """Get all critical priority loads."""
        return [load for load in self.loads if load.priority == 0]

    def get_total_demand(self) -> float:
        """Get current total power demand from active loads."""
        return sum(load.current_draw() for load in self.loads)

    def __repr__(self) -> str:
        return (
            f"PowerController("
            f"solar={self.solar_panel.current_output():.1f}W, "
            f"battery_soc={self.battery.state_of_charge():.1%}, "
            f"loads={len(self.loads)}, "
            f"demand={self.get_total_demand():.1f}W)"
        )
