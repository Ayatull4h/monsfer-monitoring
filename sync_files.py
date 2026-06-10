import shutil
import os
from pathlib import Path

src_dir = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\semarang\plamongan indah\spectrum")
dst_dir = Path(r"c:\Users\3KOM\monsfer_project_final\monsfer-server\userdata\3KOM\07plamongan_indah\spectrum")

dst_dir.mkdir(parents=True, exist_ok=True)

if src_dir.exists():
    for f in src_dir.glob("*.csv"):
        try:
            shutil.copy2(f, dst_dir / f.name)
            print(f"Copied {f.name}")
        except Exception as e:
            print(f"Error copying {f.name}: {e}")
else:
    print("Source directory not found")
