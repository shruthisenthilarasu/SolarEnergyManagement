"""
Scenario Loader
Load simulation configurations from JSON files.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.components.solar_panel import SolarPanel
from src.components.battery import Battery
from src.components.load import Load
from src.simulation.simulator import Simulator


def load_scenario(scenario_path: str) -> Simulator:
    """
    Load a simulation scenario from JSON configuration.

    Args:
        scenario_path: Path to JSON scenario file

    Returns:
        Configured Simulator instance
    """
    # Load JSON
    with open(scenario_path, 'r') as f:
        config = json.load(f)

    # Create components
    solar_config = config['solar']
    solar_panel = SolarPanel(
        max_output_w=solar_config['max_output_w'],
        efficiency=solar_config.get('efficiency', 0.20)
    )

    battery_config = config['battery']
    battery = Battery(
        capacity_wh=battery_config['capacity_wh'],
        initial_charge_wh=battery_config['initial_charge_wh'],
        max_charge_rate_w=battery_config['max_charge_rate_w'],
        max_discharge_rate_w=battery_config['max_discharge_rate_w']
    )

    loads = [
        Load(
            name=load_config['name'],
            power_draw_w=load_config['power_draw_w'],
            priority=load_config.get('priority', 2)
        )
        for load_config in config['loads']
    ]

    # Create simulator
    sim_config = config.get('simulation', {})
    simulator = Simulator(
        solar_panel=solar_panel,
        battery=battery,
        loads=loads,
        timestep_s=sim_config.get('timestep_s', 60),
        start_hour=sim_config.get('start_hour', 0)
    )

    # Inject faults if specified
    if 'faults' in config:
        for fault in config['faults']:
            fault_type = fault['type']

            if fault_type == 'cloud_cover':
                start_s = fault['start_hour'] * 3600
                duration_s = fault['duration_hours'] * 3600
                reduction = fault.get('reduction_factor', 0.7)
                simulator.inject_cloud_cover(start_s, duration_s, reduction)

            elif fault_type == 'load_spike':
                start_s = fault['start_hour'] * 3600
                duration_s = fault['duration_hours'] * 3600
                simulator.inject_load_spike(
                    start_s,
                    fault['load_name'],
                    fault['spike_power_w'],
                    duration_s
                )

            elif fault_type == 'panel_failure':
                start_s = fault['start_hour'] * 3600
                degradation = fault.get('degradation', 0.5)
                simulator.inject_panel_failure(start_s, degradation)

    return simulator


def get_scenario_info(scenario_path: str) -> Dict[str, Any]:
    """
    Get metadata about a scenario without loading it.

    Args:
        scenario_path: Path to JSON scenario file

    Returns:
        Dictionary with scenario metadata
    """
    with open(scenario_path, 'r') as f:
        config = json.load(f)

    return {
        'name': config.get('name', 'Unknown'),
        'description': config.get('description', 'No description'),
        'solar_capacity': config['solar']['max_output_w'],
        'battery_capacity': config['battery']['capacity_wh'],
        'num_loads': len(config['loads']),
        'duration_hours': config.get('simulation', {}).get('duration_hours', 24),
        'has_faults': 'faults' in config and len(config['faults']) > 0
    }
