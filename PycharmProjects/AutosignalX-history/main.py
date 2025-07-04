import sys
import subprocess
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
scripts = [
    ("scan.py",          (sys.executable, "scan.py")),
    ("startagy_program.py", (sys.executable, "startagy_program.py")),
    ("st_or_tp.py",      (sys.executable, "st_or_tp.py")),
    ("app.py (Streamlit)", ("streamlit", "run", os.path.join(sys.executable, "app.py"))),
]

for script_name, cmd in scripts:
    print(f"\n=== מריץ: {script_name} ===")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"❌ שגיאה בהרצת {script_name} - יציאה...")
        break
    print(f"✅ הסתיים {script_name}")
