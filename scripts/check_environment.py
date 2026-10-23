"""Collect only non-identifying environment facts needed for project setup."""
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

root = Path(__file__).resolve().parents[1]
facts = {
    "checked_at": datetime.now(ZoneInfo("Europe/London")).isoformat(),
    "operating_system": platform.system(),
    "architecture": platform.machine(),
    "python_version": platform.python_version(),
    "virtual_environment_active": sys.prefix != sys.base_prefix,
    "disk_free_gib": round(shutil.disk_usage(root).free / (1024**3), 1),
    "commands_on_path": {name: bool(shutil.which(name)) for name in ["python3", "git", "docker", "ollama", "uv"]},
}
if platform.system() == "Darwin":
    for name, key in [("chip", "machdep.cpu.brand_string"), ("memory_bytes", "hw.memsize")]:
        result = subprocess.run(["/usr/sbin/sysctl", "-n", key], text=True, capture_output=True)
        value = result.stdout.strip() if result.returncode == 0 else None
        facts[name] = int(value) if key == "hw.memsize" and value else value
    facts["common_app_locations"] = {
        name: Path(path).exists()
        for name, path in {"Docker": "/Applications/Docker.app", "Ollama": "/Applications/Ollama.app"}.items()
    }
try:
    facts["pypdf_version"] = importlib.metadata.version("pypdf")
except importlib.metadata.PackageNotFoundError:
    facts["pypdf_version"] = None
target = root / "docs/environment_check.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(facts, indent=2) + "\n")
print(json.dumps(facts, indent=2))

