"""
Example: Run Remote Clinic Scenario
Demonstrates a complete simulation run with the clinic scenario.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scenarios.scenario_loader import load_scenario


def main():
    """Run the remote clinic scenario and display results."""

    print("\n" + "=" * 80)
    print("SOLAR-DIRECT SIMULATOR - REMOTE MEDICAL CLINIC SCENARIO")
    print("=" * 80 + "\n")

    # Load scenario
    scenario_path = Path(__file__).parent.parent / "src" / "scenarios" / "configs" / "remote_clinic.json"

    print(f"Loading scenario from: {scenario_path}")
    simulator = load_scenario(str(scenario_path))

    print("\nScenario Configuration:")
    print(f"  Solar Panel: {simulator.solar_panel.max_output_w}W")
    print(f"  Battery: {simulator.battery.capacity_wh}Wh (SOC: {simulator.battery.state_of_charge():.1%})")
    print(f"  Loads: {len(simulator.loads)}")
    for load in simulator.loads:
        print(f"    - {load.name}: {load.power_draw_w}W ({load.priority_label()})")

    print("\nFault Scenarios:")
    if hasattr(simulator, 'faults') and simulator.faults:
        for fault in simulator.faults:
            if fault['type'] == 'cloud_cover':
                print(f"  ☁️  Cloud cover at hour {fault['start']/3600:.0f} "
                      f"for {(fault['end']-fault['start'])/3600:.0f} hours "
                      f"({fault['reduction']:.0%} reduction)")
            elif fault['type'] == 'load_spike':
                print(f"  ⚡ Load spike at hour {fault['start']/3600:.0f} "
                      f"for {(fault['end']-fault['start'])/3600:.0f} hours "
                      f"({fault['load_name']} +{fault['spike_power']}W)")
    else:
        print("  None configured")

    print("\n" + "=" * 80)
    print("STARTING SIMULATION")
    print("=" * 80 + "\n")

    # Run simulation
    df = simulator.run(duration_hours=48)

    # Additional analysis
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS")
    print("=" * 80 + "\n")

    # Find critical moments
    print("Critical Moments:")

    # Lowest battery SOC
    min_soc_idx = df['battery_soc'].idxmin()
    min_soc_row = df.loc[min_soc_idx]
    print(f"\n  Lowest Battery SOC:")
    print(f"    Time: Hour {min_soc_row['hour_of_day']:.1f}")
    print(f"    SOC: {min_soc_row['battery_soc']:.1%}")
    print(f"    Solar: {min_soc_row['solar_output_w']:.0f}W")
    print(f"    Demand: {min_soc_row['total_demand']:.0f}W")

    # Shedding events
    shedding_events = df[df['num_shed_loads'] > 0]
    if len(shedding_events) > 0:
        print(f"\n  Load Shedding Events: {len(shedding_events)}")
        print(f"    First event at hour {shedding_events.iloc[0]['hour_of_day']:.1f}")
        print(f"    Loads shed: {shedding_events.iloc[0]['shed_loads']}")
    else:
        print("\n  ✅ No load shedding required - system maintained all loads!")

    # Save results
    output_path = Path(__file__).parent / "clinic_simulation_results.csv"
    df.to_csv(output_path, index=False)
    print(f"\n📄 Results saved to: {output_path}")

    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
