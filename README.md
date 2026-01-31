# Solar-Direct Energy Management Simulator

A software-based simulation of Solar-Direct power systems demonstrating intelligent DC-coupled power routing, battery management, and load prioritization for resilient, off-grid applications.

Built to showcase understanding of [Vroom Power's](https://www.vroom-power.com) Solar-Direct technology.

## 🚀 Quick Start

### Installation
```bash
cd ~/solar-direct-simulator
pip3 install -r requirements.txt
```

### Run the Dashboard
```bash
python3 -m streamlit run dashboard/app.py
```

This launches an interactive web interface where you can:
- Select preset scenarios (clinic, farm) or create custom configs
- Inject fault scenarios (cloud cover, load spikes)
- Visualize power flows, battery state, and load status
- Review controller decision logs

### Run Example Simulation
```bash
python3 examples/run_clinic_scenario.py
```

## 📊 Features

- ☀️ **Realistic Solar Curves** - Time-of-day based generation
- 🔋 **Intelligent Battery Management** - Reserve capacity for critical loads
- ⚡ **Priority-Based Load Shedding** - Critical → High → Deferrable
- 🛡️ **Fault Injection** - Cloud cover, load spikes, panel failures
- 📊 **Real-Time Visualization** - Interactive Streamlit dashboard

## 🎯 Project Structure
```
solar-direct-simulator/
├── README.md
├── requirements.txt
├── src/
│   ├── components/          # Solar panel, battery, load models
│   ├── controller/          # Intelligent routing logic
│   ├── simulation/          # Time-stepped simulation engine
│   └── scenarios/           # Scenario configs (clinic, farm)
├── dashboard/
│   └── app.py               # Streamlit visualization
└── examples/
    └── run_clinic_scenario.py
```

## 💡 Key Design Decisions

### Why DC-Coupled?
Traditional AC systems require inverters at every stage. Solar-Direct keeps everything DC until the final load, reducing conversion losses and complexity.

### Why Priority-Based Load Shedding?
In off-grid scenarios, intelligent shedding maintains critical operations (medical equipment, communications) while deferring non-critical loads (HVAC, entertainment).

### Why 20% Battery Reserve?
Protects battery longevity and ensures critical loads have guaranteed runtime even during extended solar outages.

---

**Built by Shruthi Senthilraja for Vroom Power**
