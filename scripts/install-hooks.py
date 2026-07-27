#!/usr/bin/env python3
"""Enable this repository's local Git hooks for the current checkout."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT, check=True)
print("Enabled local Git hooks: .githooks")
