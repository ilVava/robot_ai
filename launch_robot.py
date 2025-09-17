#!/usr/bin/env python3
"""
Robot AI Launcher - Simplified Entry Point

This is the main entry point for launching Robot AI in different modes.
"""

import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("🤖 ROBOT AI - Launcher")
        print("=" * 50)
        print("Usage: python3 launch_robot.py [mode]")
        print()
        print("Available modes:")
        print("  autonomous  - Full autonomous exploration")
        print("  test       - Hardware movement test")
        print("  basic      - Basic autonomy test (limited)")
        print()
        print("Examples:")
        print("  python3 launch_robot.py autonomous")
        print("  python3 launch_robot.py test")
        return

    mode = sys.argv[1].lower()

    if mode == "autonomous":
        print("🚀 Launching full autonomous robot exploration...")
        os.system("python3 deployment/launch_autonomous_robot.py")

    elif mode == "test":
        print("🧪 Running hardware movement test...")
        os.system("python3 tests/hardware/test_direct_movement.py")

    elif mode == "basic":
        print("🔍 Running basic autonomy test...")
        os.system("python3 tests/hardware/test_basic_autonomy.py")

    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: autonomous, test, basic")
        return 1

if __name__ == "__main__":
    main()