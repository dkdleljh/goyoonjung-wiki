#!/usr/bin/env python3
"""Configuration Loader.
- Reads `config.yaml` from the project root.
- Returns a dictionary of settings.
- Falls back to defaults if file is missing.
"""

import os
import yaml
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE / 'config.yaml'

def load_config():
    if not CONFIG_PATH.exists():
        print(f"Warning: Config file not found at {CONFIG_PATH}. Using defaults.")
        return {}
        
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

if __name__ == "__main__":
    # Test
    conf = load_config()
    print("Loaded Config keys:", list(conf.keys()))
