import subprocess
import sys

commands = [
    [sys.executable, "scripts/retrain_baseline_model.py"],
    [sys.executable, "scripts/retrain_enriched_model.py"],
]

for cmd in commands:
    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

print("\nAll models trained successfully.")