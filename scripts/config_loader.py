#!/usr/bin/env python3
"""Configuration Loader.
- Reads `config.yaml` from the project root.
- Returns a dictionary of settings.
- Custom parser to avoid PyYAML dependency.
"""

import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE / 'config.yaml'

def load_config():
    if not CONFIG_PATH.exists():
        print(f"Warning: Config file not found at {CONFIG_PATH}. Using defaults.")
        return {}
        
    config = {}
    current_section = None
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Check indentation for nested keys
                indent = len(line) - len(line.lstrip())
                
                if ':' in stripped:
                    key, val = stripped.split(':', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    
                    if not val:
                        # Parent key (section)
                        if indent == 0:
                            current_section = key
                            config[current_section] = {}
                        continue
                    
                    if indent > 0 and current_section:
                        # Nested key
                        config[current_section][key] = val
                    else:
                        # Top-level key
                        config[key] = val
                        current_section = None
                        
                elif stripped.startswith('- '):
                    # List item
                    val = stripped[2:].strip().strip('"').strip("'")
                    if current_section:
                        if isinstance(config[current_section], dict):
                            # Convert dict to list if it was initialized as dict (imperfect but works for our case if list follows header)
                            # Actually, for our config:
                            # schedule_keywords:
                            #   - "..."
                            # So current_section points to a key.
                            if not config[current_section]: config[current_section] = []
                        
                        if isinstance(config[current_section], list):
                            config[current_section].append(val)
                            
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}
        
    return config

if __name__ == "__main__":
    conf = load_config()
    for k, v in conf.items():
        print(f"{k}: {v}")
