# System Design: Solar-Direct Energy Management Simulator

## Overview

This document describes the architecture and design of the Solar-Direct Energy Management Simulator — a software model of DC-coupled solar systems with battery storage and intelligent load management.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIMULATION BOUNDARY                                  │
│                                                                              │
│  ┌──────────────┐     ┌─────────────────┐     ┌─────────────────────────┐   │
│  │ Solar Panel  │     │     Battery     │     │         Loads           │   │
│  │              │     │                 │     │  ┌─────┬─────┬─────┐    │   │
│  │ • Irradiance │     │ • SOC           │     │  │ L0  │ L1  │ L2  │    │   │
│  │ • Efficiency │     │ • Charge/       │     │  │Crit │High │Def  │    │   │
│  │ • Degradation│     │   Discharge     │     │  └─────┴─────┴─────┘    │   │
│  └──────┬───────┘     └────────┬────────┘     └────────────┬────────────┘   │
│         │                      │                           │                │
│         │     DC Power Flows   │                           │                │
│         └──────────────────────┼───────────────────────────┘                │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                 │
│                    │   POWER CONTROLLER    │                                 │
│                    │                       │                                 │
│                    │ • Routing decisions   │                                 │
│                    │ • Load shedding       │                                 │
│                    │ • Battery reserve     │                                 │
│                    │ • Hysteresis logic    │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                            │
│                                ▼                                            │
│                    ┌───────────────────────┐                                 │
│                    │     SIMULATOR         │                                 │
│                    │                       │                                 │
│                    │ • Time-stepped loop   │                                 │
│                    │ • Solar curve         │                                 │
│                    │ • Fault injection     │                                 │
│                    │ • History recording   │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                            │
└────────────────────────────────┼────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │   OUTPUT / UI         │
                    │                       │
                    │ • DataFrame (history) │
                    │ • Streamlit dashboard │
                    │ • Example scripts     │
                    └───────────────────────┘
```

---

## Component Diagram

### 1. Components Layer (`src/components/`)

| Component      | Responsibility                                      | Key State / Methods                                              |
|----------------|-----------------------------------------------------|------------------------------------------------------------------|
| **SolarPanel** | Models DC output from irradiance and efficiency     | `current_irradiance`, `efficiency`; `current_output()`, `update_irradiance()`, `apply_degradation()` |
| **Battery**    | Tracks charge, capacity, and rate limits            | `current_charge_wh`, `capacity_wh`; `state_of_charge()`, `charge()`, `discharge()`, `available_charge_capacity()`, `available_discharge_capacity()` |
| **Load**       | Represents a power-consuming load with priority     | `name`, `power_draw_w`, `priority`, `is_active`; `activate()`, `deactivate()`, `current_draw()`, `shed_count()` |

### 2. Controller Layer (`src/controller/`)

| Component          | Responsibility                                        | Key Logic                                                                 |
|--------------------|-------------------------------------------------------|---------------------------------------------------------------------------|
| **PowerController**| Decides power routing and load states each timestep   | Solar-first routing; 20% battery reserve; priority-based shedding; 10% hysteresis to prevent oscillation |

**Decision flow (each timestep):**
1. Compute available power: solar output + battery discharge capacity (above reserve).
2. If demand > supply → shed loads (lowest priority first).
3. If demand < supply and headroom exists → restore previously shed loads (with hysteresis).
4. Route power: solar to loads first; excess solar to battery; shortfall from battery.
5. Return routing decisions and updated load states.

### 3. Simulation Layer (`src/simulation/`)

| Component   | Responsibility                                         | Key Logic                                                                 |
|-------------|--------------------------------------------------------|---------------------------------------------------------------------------|
| **Simulator** | Runs time-stepped simulation and records history     | Solar irradiance curve (6am–6pm sine); fault injection (cloud, spike, degradation); calls controller each step; updates battery; records history |

### 4. Scenarios Layer (`src/scenarios/`)

| Component        | Responsibility                                   |
|------------------|--------------------------------------------------|
| **scenario_loader** | Loads JSON configs → builds SolarPanel, Battery, Loads, Simulator |
| **configs/**     | Preset scenarios (e.g. `remote_clinic.json`, `farm.json`) |

---

## Data Flow

### Per-Timestep Flow

```
1. Simulator advances time (current_hour)
        │
2. Solar irradiance updated (diurnal curve + faults)
        │
3. Faults applied (cloud cover, load spike, panel failure)
        │
4. PowerController.decide_power_routing(timestep_s)
        │
        ├── Reads: solar.current_output(), battery.state_of_charge(), loads[].current_draw()
        ├── Logic: shed/restore loads, compute power_from_solar, power_from_battery, power_to_battery
        └── Returns: decision dict (power flows, active_loads, shed_loads, decisions)
        │
5. Simulator applies decision: battery.charge() or battery.discharge()
        │
6. History row appended (timestamp, solar_output, battery_soc, power flows, load states)
        │
7. Repeat until duration_hours reached
```

### Scenario Loading Flow

```
JSON config
    │
    ├── solar section   → SolarPanel(max_output_w, efficiency)
    ├── battery section → Battery(capacity_wh, initial_charge_wh, max_charge_rate_w, max_discharge_rate_w)
    ├── loads section   → [Load(name, power_draw_w, priority), ...]
    ├── simulation      → timestep_s, start_hour, duration_hours
    └── faults          → inject_cloud_cover(), inject_load_spike(), inject_panel_failure()
    │
    ▼
Simulator instance (ready to run)
```

---

## Key Design Decisions

### 1. Solar-First Routing

**Decision:** Use solar output for loads first; only use battery when solar is insufficient.

**Rationale:** Solar has no marginal cost. Battery is a finite resource and should be preserved for night and low-solar periods.

### 2. 20% Battery Reserve

**Decision:** Reserve 20% of battery capacity exclusively for critical loads (priority 0).

**Rationale:** Protects battery longevity (depth of discharge limits) and guarantees runtime for life-safety loads (e.g. medical refrigeration) during extended outages.

### 3. Priority-Based Load Shedding

**Decision:** Shed loads in order of priority: deferrable (2) first, then high (1), then critical (0) only when unavoidable.

**Rationale:** Graceful degradation. Non-critical loads are shed before compromising critical infrastructure.

### 4. Hysteresis for Load Restoration

**Decision:** Require ~10% extra available power before re-enabling a shed load.

**Rationale:** Prevents rapid on/off cycling when supply hovers near demand, which would stress hardware and annoy users.

### 5. Time-Stepped Simulation

**Decision:** Discrete 1-minute timesteps; no continuous-time modeling.

**Rationale:** Simple, deterministic, and sufficient for control logic validation. Enables straightforward history logging and analysis.

### 6. Fault Injection via Method Calls

**Decision:** Faults are injected via `inject_cloud_cover()`, `inject_load_spike()`, `inject_panel_failure()`; applied each timestep in `_apply_faults()`.

**Rationale:** Scenario configs can define faults declaratively; simulator applies them without hardcoding. Easy to add new fault types.

---

## Module Dependencies

```
dashboard/app.py
    └── src.scenarios.scenario_loader (load_scenario, get_scenario_info)
    └── src.components.*
    └── src.simulation.simulator

examples/run_clinic_scenario.py
    └── src.scenarios.scenario_loader (load_scenario)

src/scenarios/scenario_loader.py
    └── src.components.*
    └── src.simulation.simulator

src/simulation/simulator.py
    └── src.components.*
    └── src.controller.power_controller

src/controller/power_controller.py
    └── src.components.*
```

---

## Outputs

| Output                 | Format          | Description                                      |
|------------------------|-----------------|--------------------------------------------------|
| Simulation history     | pandas DataFrame| Per-timestep power flows, SOC, load states       |
| Console summary        | Text            | Energy totals, battery stats, shedding events    |
| CSV export             | File            | Downloadable from Streamlit dashboard            |
| Streamlit visualizations | Interactive   | Power flow chart, SOC, load timeline             |

---

## Extension Points

- **New fault types:** Add `inject_*()` and handling in `_apply_faults()`.
- **New sources:** Extend PowerController to accept grid/generator; update routing logic.
- **New scenarios:** Add JSON configs under `src/scenarios/configs/`.
- **Alternative UIs:** Reuse Simulator and PowerController; swap dashboard for CLI, API, or Jupyter.
