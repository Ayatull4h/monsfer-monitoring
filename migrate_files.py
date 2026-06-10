"""
Script to copy new simulation files from semarang/plamongan indah/ to 3KOM/07plamongan_indah/
"""
import shutil
from pathlib import Path

src_spectrum = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\semarang\plamongan indah\spectrum")
src_wifi = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\semarang\plamongan indah\wifi")
src_health = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\semarang\plamongan indah\health")

dst_spectrum = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\3KOM\07plamongan_indah\spectrum")
dst_wifi = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\3KOM\07plamongan_indah\wifi")
dst_health = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\3KOM\07plamongan_indah\health")

dst_spectrum.mkdir(parents=True, exist_ok=True)
dst_wifi.mkdir(parents=True, exist_ok=True)
dst_health.mkdir(parents=True, exist_ok=True)

copied = 0
for f in src_spectrum.glob("07001_MONITORING_2026-05-*"):
    dst = dst_spectrum / f.name
    if not dst.exists():
        shutil.copy2(f, dst)
        print(f"Copied spectrum: {f.name}")
        copied += 1

for f in src_wifi.glob("07001_WIFI_2026-05-*"):
    dst = dst_wifi / f.name
    if not dst.exists():
        shutil.copy2(f, dst)
        print(f"Copied wifi: {f.name}")
        copied += 1

for f in src_health.glob("07001_HEALTH_2026-05-*"):
    dst = dst_health / f.name
    if not dst.exists():
        shutil.copy2(f, dst)
        print(f"Copied health: {f.name}")
        copied += 1

print(f"\nTotal files copied: {copied}")
print(f"Spectrum files now in 3KOM: {len(list(dst_spectrum.glob('*.csv')))}")
