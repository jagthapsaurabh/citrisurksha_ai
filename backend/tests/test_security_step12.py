"""Upgrade step 12: the runnable security checklist must pass."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_security_checklist_passes():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "security_check.py")],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr
