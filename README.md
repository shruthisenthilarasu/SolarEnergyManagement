# Solar-Direct Energy Management Simulator

<p align="center">
  <img src="docs/dashboard-screenshot.png" alt="Dashboard showing power flow, battery SOC, and load status" width="800">
</p>

A software simulation of Solar-Direct power systems — models what real control firmware would decide in DC-coupled solar + battery + load setups. Built to demonstrate intelligent routing, priority-based load shedding, and resilience under fault conditions.

---

## What This Does

This simulator models **how power flows** in an off-grid Solar-Direct system: solar panels and batteries supply DC power to prioritized loads (critical → high → deferrable). When supply falls short, the controller sheds the lowest-priority loads first, reserves 20% of the battery for critical loads only, and uses hysteresis to avoid rapid switching. You can run preset scenarios (e.g., remote medical clinic, farm) or custom configs, inject faults (cloud cover, load spikes, panel degradation), and visualize everything in an interactive dashboard.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd solar-direct-simulator
pip3 install -r requirements.txt
```

### 2. Run the dashboard
```bash
python3 -m streamlit run dashboard/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 3. Run the example (CLI)
```bash
python3 examples/run_clinic_scenario.py
```
Runs a 48-hour remote clinic simulation and saves results to `examples/clinic_simulation_results.csv`.

---

## ✨ Features

| Feature | Description |
|--------|-------------|
| ☀️ **Realistic solar curves** | Time-of-day based generation (6am–6pm sine curve) |
| 🔋 **Intelligent battery management** | 20% reserve for critical loads, charge/discharge limits |
| ⚡ **Priority-based load shedding** | Critical (0) → High (1) → Deferrable (2) |
| 🛡️ **Fault injection** | Cloud cover, load spikes, panel degradation |
| 📊 **Interactive dashboard** | Power flow charts, battery SOC, load timeline |
| 📁 **Scenario configs** | JSON-based presets (clinic, farm) or custom builds |

---

## 🏗️ Architecture

```
Solar Panel (DC) ──┐
                   ├──► Power Controller ──► Loads (prioritized)
Battery (DC) ──────┘         │
                        Decision logic:
                    (shed, buffer, switch sources)
```

**Flow each timestep:**
1. Update solar irradiance (diurnal curve + faults)
2. Controller decides routing: solar first, then battery; shed/restore loads by priority
3. Battery charges from excess solar or discharges for shortfall
4. History recorded for visualization

See [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) for full architecture, data flow, and design decisions.

---

## 📺 Example Output

### Console (run_clinic_scenario.py)
```
================================================================================
SOLAR-DIRECT SIMULATOR - REMOTE MEDICAL CLINIC SCENARIO
================================================================================

Scenario Configuration:
  Solar Panel: 2000W
  Battery: 5000Wh (SOC: 80.0%)
  Loads: 3
    - Medical Refrigeration: 200W (CRITICAL)
    - Lighting: 150W (HIGH)
    - HVAC: 800W (DEFERRABLE)

Fault Scenarios:
  ☁️  Cloud cover at hour 8 for 2 hours (70% reduction)
  ⚡ Load spike at hour 14 for 1 hours (Lighting +100W)

================================================================================
STARTING SIMULATION
================================================================================

Starting simulation: 48 hours (2880 timesteps)
Initial battery SOC: 80.0%
--------------------------------------------------------------------------------
[Hour 0] Solar: 0W | Battery: 80.0% | Demand: 200W | Active: 1/3 loads
[Hour 6] Solar: 1000W | Battery: 78.2% | Demand: 1150W | Active: 3/3 loads
[Hour 12] Solar: 2000W | Battery: 85.1% | Demand: 1150W | Active: 3/3 loads
...
--------------------------------------------------------------------------------
Simulation complete!

================================================================================
SIMULATION SUMMARY
================================================================================

Energy Flow:
  Total solar energy delivered:    42.31 Wh
  Total battery discharge:         12.45 Wh
  Total battery charge:            18.22 Wh
  Total demand:                    38.67 Wh

Battery:
  Final SOC:     82.3%
  Min SOC:       75.1%
  Max SOC:       85.2%

Critical Load Uptime: 100.0%
Load Shedding: HVAC shed 47 times
```

### Dashboard
The Streamlit UI shows summary metrics, power flow over time, battery SOC, load status timeline, and an expandable decision log. Export results as CSV.

---

## 🎯 Project Structure

```
solar-direct-simulator/
├── README.md
├── requirements.txt
├── SYSTEM_DESIGN.md
├── docs/
│   └── dashboard-screenshot.png
├── src/
│   ├── components/          # SolarPanel, Battery, Load
│   ├── controller/          # PowerController (routing + shedding)
│   ├── simulation/          # Simulator (time-stepped + faults)
│   └── scenarios/           # Loader + configs (clinic, farm)
├── dashboard/
│   └── app.py               # Streamlit UI
└── examples/
    └── run_clinic_scenario.py
```

---

## 💡 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Solar-first routing** | Solar has no marginal cost; preserve battery for night/low-sun periods |
| **20% battery reserve** | Protects battery longevity and guarantees critical load runtime |
| **Priority-based shedding** | Graceful degradation — shed non-critical before compromising critical loads |
| **Hysteresis (10%)** | Prevents rapid on/off cycling when supply hovers near demand |

---

**Built by Shruthi Senthilraja | [Vroom Power](https://www.vroom-power.com)**
