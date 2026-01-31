"""
Streamlit Dashboard for Solar-Direct Simulator
Interactive visualization and control interface.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import sys
import os
from pathlib import Path

# Add parent directory to path - multiple approaches
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

try:
    from src.scenarios.scenario_loader import load_scenario, get_scenario_info
    from src.components.solar_panel import SolarPanel
    from src.components.battery import Battery
    from src.components.load import Load
    from src.simulation.simulator import Simulator
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error(f"Current directory: {os.getcwd()}")
    st.error(f"Python path: {sys.path}")
    st.stop()

# Page config
st.set_page_config(
    page_title="Solar-Direct Energy Management",
    page_icon="☀️",
    layout="wide"
)

# Vroom Power branding colors (approximated from website)
VROOM_PRIMARY = "#FF6B35"  # Orange
VROOM_SECONDARY = "#004E89"  # Blue
VROOM_SUCCESS = "#2A9D8F"  # Teal

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #004E89;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF6B35;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">☀️ Solar-Direct Energy Management Simulator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Intelligent DC-Coupled Power Routing & Load Management</div>', unsafe_allow_html=True)

st.markdown("---")

# Sidebar - Configuration
st.sidebar.header("⚙️ Configuration")

# Scenario selection
scenario_type = st.sidebar.selectbox(
    "Select Scenario",
    ["Remote Medical Clinic", "Agricultural Farm", "Custom"]
)

if scenario_type != "Custom":
    # Load preset scenario
    scenario_file = "remote_clinic.json" if scenario_type == "Remote Medical Clinic" else "farm.json"
    scenario_path = Path(__file__).parent.parent / "src" / "scenarios" / "configs" / scenario_file

    if scenario_path.exists():
        scenario_info = get_scenario_info(str(scenario_path))

        st.sidebar.success(f"**{scenario_info['name']}**")
        st.sidebar.write(f"📄 {scenario_info['description']}")
        st.sidebar.write(f"☀️ Solar: {scenario_info['solar_capacity']}W")
        st.sidebar.write(f"🔋 Battery: {scenario_info['battery_capacity']}Wh")
        st.sidebar.write(f"⚡ Loads: {scenario_info['num_loads']}")
        st.sidebar.write(f"⏱️ Duration: {scenario_info['duration_hours']}h")

        use_preset = True
    else:
        st.sidebar.error(f"Scenario file not found: {scenario_path}")
        use_preset = False
else:
    use_preset = False

    # Custom configuration
    st.sidebar.subheader("Solar Panel")
    solar_capacity = st.sidebar.slider("Solar Capacity (W)", 500, 10000, 2000, 500)

    st.sidebar.subheader("Battery")
    battery_capacity = st.sidebar.slider("Battery Capacity (Wh)", 1000, 20000, 5000, 1000)
    battery_charge_rate = st.sidebar.slider("Charge/Discharge Rate (W)", 500, 5000, 1000, 500)

    st.sidebar.subheader("Simulation")
    duration_hours = st.sidebar.slider("Duration (hours)", 12, 72, 48, 12)
    start_hour = st.sidebar.slider("Start Hour of Day", 0, 23, 0)

# Run simulation button
if st.sidebar.button("▶️ Run Simulation", type="primary"):
    with st.spinner("Running simulation..."):
        # Load or create simulator
        if use_preset:
            simulator = load_scenario(str(scenario_path))
            duration_hours = scenario_info['duration_hours']
        else:
            # Create custom simulator
            solar_panel = SolarPanel(max_output_w=solar_capacity, efficiency=0.20)
            battery = Battery(
                capacity_wh=battery_capacity,
                initial_charge_wh=battery_capacity * 0.8,
                max_charge_rate_w=battery_charge_rate,
                max_discharge_rate_w=battery_charge_rate
            )
            loads = [
                Load("Critical Load", 200, priority=0),
                Load("High Priority Load", 300, priority=1),
                Load("Deferrable Load", 500, priority=2)
            ]
            simulator = Simulator(solar_panel, battery, loads, start_hour=start_hour)

        # Run simulation
        df = simulator.run(duration_hours)

        # Store in session state
        st.session_state['simulation_results'] = df
        st.session_state['simulator'] = simulator

        st.success("✅ Simulation complete!")

# Display results if available
if 'simulation_results' in st.session_state:
    df = st.session_state['simulation_results']
    simulator = st.session_state['simulator']

    # Summary metrics
    st.header("📊 Summary Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_solar = df['power_from_solar'].sum() * (simulator.timestep_s / 3600)
        st.metric("Total Solar Energy", f"{total_solar:.1f} Wh")

    with col2:
        final_soc = df['battery_soc'].iloc[-1]
        st.metric("Final Battery SOC", f"{final_soc:.1%}")

    with col3:
        critical_loads = [load for load in simulator.loads if load.priority == 0]
        if critical_loads:
            critical_names = [l.name for l in critical_loads]
            critical_uptime = df[~df['shed_loads'].str.contains('|'.join(critical_names), na=False)].shape[0] / len(df)
            st.metric("Critical Load Uptime", f"{critical_uptime:.1%}")
        else:
            st.metric("Critical Load Uptime", "N/A")

    with col4:
        shedding_events = df[df['num_shed_loads'] > 0].shape[0]
        st.metric("Load Shedding Events", f"{shedding_events}")

    st.markdown("---")

    # Power Flow Visualization
    st.header("⚡ Power Flow Over Time")

    fig_power = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Power Sources & Demand", "Battery State of Charge"),
        vertical_spacing=0.12,
        row_heights=[0.6, 0.4]
    )

    # Convert timestamp to hours for x-axis
    df['hours'] = df['timestamp'] / 3600

    # Power sources
    fig_power.add_trace(
        go.Scatter(x=df['hours'], y=df['solar_output_w'],
                   name="Solar Output", line=dict(color=VROOM_PRIMARY, width=2),
                   fill='tozeroy'),
        row=1, col=1
    )

    fig_power.add_trace(
        go.Scatter(x=df['hours'], y=df['power_from_battery'],
                   name="Battery Discharge", line=dict(color=VROOM_SECONDARY, width=2),
                   fill='tozeroy'),
        row=1, col=1
    )

    fig_power.add_trace(
        go.Scatter(x=df['hours'], y=df['total_demand'],
                   name="Total Demand", line=dict(color='red', width=2, dash='dash')),
        row=1, col=1
    )

    # Battery SOC
    fig_power.add_trace(
        go.Scatter(x=df['hours'], y=df['battery_soc'] * 100,
                   name="Battery SOC", line=dict(color=VROOM_SUCCESS, width=3),
                   fill='tozeroy'),
        row=2, col=1
    )

    # Add reserve line
    fig_power.add_hline(y=20, line_dash="dot", line_color="red",
                        annotation_text="Critical Reserve (20%)", row=2, col=1)

    fig_power.update_xaxes(title_text="Time (hours)", row=2, col=1)
    fig_power.update_yaxes(title_text="Power (W)", row=1, col=1)
    fig_power.update_yaxes(title_text="SOC (%)", row=2, col=1)

    fig_power.update_layout(height=600, showlegend=True, hovermode='x unified')

    st.plotly_chart(fig_power, use_container_width=True)

    # Load Status Timeline
    st.header("💡 Load Status Timeline")

    col1, col2 = st.columns([3, 1])

    with col1:
        fig_loads = go.Figure()

        # Create a timeline showing active/shed status for each load
        for load in simulator.loads:
            load_status = []
            for _, row in df.iterrows():
                if load.name in row['active_loads']:
                    load_status.append(1)
                else:
                    load_status.append(0)

            priority_label = ["CRITICAL", "HIGH", "DEFERRABLE"][load.priority]

            fig_loads.add_trace(go.Scatter(
                x=df['hours'],
                y=load_status,
                name=f"{load.name} ({priority_label})",
                mode='lines',
                line=dict(width=0),
                stackgroup='one',
                fillcolor=px.colors.qualitative.Set2[load.priority]
            ))

        fig_loads.update_layout(
            height=300,
            xaxis_title="Time (hours)",
            yaxis_title="Active Loads",
            hovermode='x unified',
            showlegend=True
        )

        st.plotly_chart(fig_loads, use_container_width=True)

    with col2:
        st.subheader("Load Summary")
        for load in simulator.loads:
            priority_label = ["🔴 CRITICAL", "🟡 HIGH", "🟢 DEFER"][load.priority]
            st.write(f"**{load.name}**")
            st.write(f"{priority_label}")
            st.write(f"{load.power_draw_w}W")
            st.write(f"Shed: {load.shed_count()} times")
            st.write("---")

    # Decision Log
    with st.expander("📋 View Decision Log (First 100 entries)"):
        decision_log = df[['hours', 'decisions']].head(100)
        for _, row in decision_log.iterrows():
            st.text(f"[Hour {row['hours']:.1f}] {row['decisions']}")

    # Download data
    st.header("💾 Export Data")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Simulation Data (CSV)",
        data=csv,
        file_name="solar_direct_simulation.csv",
        mime="text/csv"
    )

else:
    # Welcome screen
    st.info("👈 Configure your simulation in the sidebar and click **Run Simulation** to begin!")

    st.header("🎯 About This Simulator")

    st.write("""
    This Solar-Direct Energy Management Simulator demonstrates intelligent power routing and load management
    for DC-coupled solar systems with battery storage.

    **Key Features:**
    - ☀️ **Realistic Solar Curves** - Time-of-day based generation
    - 🔋 **Intelligent Battery Management** - Reserve capacity for critical loads
    - ⚡ **Priority-Based Load Shedding** - Critical → High → Deferrable
    - 🛡️ **Fault Injection** - Cloud cover, load spikes, panel failures
    - 📊 **Real-Time Visualization** - Power flows, battery state, load status

    **Preset Scenarios:**
    1. **Remote Medical Clinic** - 24/7 critical equipment uptime
    2. **Agricultural Farm** - High-power irrigation with processing equipment

    Built to showcase understanding of [Vroom Power's](https://www.vroom-power.com) Solar-Direct technology.
    """)

    st.markdown("---")
    st.markdown("*Created by Shruthi Senthilraja | [Unsent Letter Project](https://unsentletterproject.com)*")
