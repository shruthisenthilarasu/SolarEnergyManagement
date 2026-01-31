#!/usr/bin/env bash
# Run the Remote Clinic scenario (install deps first: pip install -r requirements.txt)
cd "$(dirname "$0")"
export PYTHONPATH=.
python3 examples/run_clinic_scenario.py
