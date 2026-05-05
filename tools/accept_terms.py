#!/usr/bin/env python3
"""
Utility script to accept legal terms and unblock the GUI.
This creates/updates the config file to set terms_accepted = True.
"""
import sys
import os

# Add bspg to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BSPG_PATH = os.path.join(ROOT, "bspg")
if BSPG_PATH not in sys.path:
    sys.path.insert(0, BSPG_PATH)

from bspg.core.config import AppConfig

def main():
    print("Loading app config...")
    config = AppConfig()
    
    try:
        config.load()
        print(f"Current terms_accepted status: {config.terms_accepted}")
    except Exception as e:
        print(f"No existing config found or error loading: {e}")
        print("Creating new config...")
    
    print("\nSetting terms_accepted = True...")
    config.terms_accepted = True
    
    try:
        config.save()
        print("✓ Terms accepted! Config saved successfully.")
        print("\nYou can now run the GUI without the blocking overlay:")
        print("  python run_gui.py")
    except Exception as e:
        print(f"✗ Error saving config: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
