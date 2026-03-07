#!/usr/bin/env python3
"""Test runner script for goyoonjung-wiki.

This script runs all tests in the correct environment.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run all tests."""
    # Get project root
    project_root = Path(__file__).parent.parent

    # Check if .venv exists
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print("Error: .venv not found. Run 'make venv' first.")
        sys.exit(1)

    # Determine python path
    if sys.platform == "win32":
        python = venv_path / "Scripts" / "python.exe"
    else:
        python = venv_path / "bin" / "python"

    if not python.exists():
        print(f"Error: Python not found at {python}")
        sys.exit(1)

    # Run pytest
    cmd = [
        str(python),
        "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
