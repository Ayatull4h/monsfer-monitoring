"""
Helper script to start the Monitoring UI server.
Run this from: c:\Users\3KOM\monsfer_project_final\monsfer-server\MONITORING_UI\
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

venv_python = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'venv', 'Scripts', 'python.exe'
)

if not os.path.exists(venv_python):
    venv_python = sys.executable

print(f"Starting Monitoring UI with: {venv_python}")
print(f"Working dir: {os.getcwd()}")

subprocess.run([venv_python, 'app.py'], check=True)
