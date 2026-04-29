#!/usr/bin/env python3
"""Workspace orchestrator: run the configurator GUI or perform maintenance tasks.

Usage:
  python orchestrator.py         # runs GUI
  python orchestrator.py --wipe  # wipes MCP memory files
"""
import argparse
import sys
from pathlib import Path

def run_gui():
    # import the GUI module and run its main
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from vens.configurator import gui as gui_mod
    gui_mod.main()

def wipe_memory():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from vens.mempalace_adapter import wipe_memories
    n = wipe_memories()
    print(f"Removed {n} memory files")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wipe', action='store_true', help='Wipe MCP memory files')
    args = p.parse_args()
    if args.wipe:
        wipe_memory()
    else:
        run_gui()

if __name__ == '__main__':
    main()
