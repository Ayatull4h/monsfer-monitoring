import time
import json
import random
from datetime import datetime
from pathlib import Path
import os
import psutil

BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_DIR = BASE_DIR / "data_upload"
# Station ID: 07 = UPT ID (semarang), 001 = device ID (plamongan indah)
# This matches file_manager.py lookup against userdata.json
STATION_ID = "07001"

def generate_spectrum():
    ts = datetime.now()
    filename = f"{STATION_ID}_MONITORING_{ts.strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, 'w') as f:
        f.write("#STATION_ID\n")
        f.write(f"station_id;{STATION_ID}\n")
        f.write(f"date;{ts.strftime('%Y-%m-%d')}\n")
        f.write(f"time;{ts.strftime('%H:%M:%S')}\n")
        f.write(f"station_name;Plamongan Indah\n")
        f.write("latitude;-7.0291707\n")
        f.write("longitude;110.4975072\n\n")
        f.write("#BAND_CONFIGURATION\n")
        f.write("band_number;start_frequency_mhz;end_frequency_mhz;step_bw_khz\n")
        f.write("1;87.0;108.0;6.25\n\n")
        f.write("#MEASUREMENT_DATA\n")
        f.write("frequency_mhz;level_dbfs\n")
        for i in range(200):
            freq = 87.0 + (i * 0.1)
            # Add some dummy signals
            level = random.uniform(-95, -80)
            if 88.0 <= freq <= 88.2 or 105.0 <= freq <= 105.2:
                level = random.uniform(-50, -40)
            f.write(f"{freq:.1f};{level:.3f}\n")
    print(f"Generated {filename}")

def generate_wifi():
    ts = datetime.now()
    filename = f"{STATION_ID}_WIFI_{ts.strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, 'w') as f:
        f.write("date;time;bssid;frequency;signal;ssid;vendor\n")
        for i in range(5):
            freq = random.choice([2412, 2437, 2462, 5180, 5745])
            sig = random.randint(-85, -45)
            bssid = f"00:11:22:33:44:{random.randint(10, 99)}"
            f.write(f"{ts.strftime('%Y-%m-%d')};{ts.strftime('%H:%M:%S')};{bssid};{freq};{sig};Simulated_WiFi_{i};VendorX\n")
    print(f"Generated {filename}")

def generate_health():
    ts = datetime.now()
    filename = f"{STATION_ID}_HEALTH_{ts.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    file_path = UPLOAD_DIR / filename
    
    data = {
        "timestamp": ts.isoformat(),
        "cpuUtil": psutil.cpu_percent(),
        "cpuTemp": random.uniform(40, 60),
        "freeStorage": round(psutil.disk_usage('/').free / (1024**3), 2),
        "totalStorage": round(psutil.disk_usage('/').total / (1024**3), 2),
        "freeRAM": round(psutil.virtual_memory().available / (1024**2), 2),
        "totalRAM": round(psutil.virtual_memory().total / (1024**2), 2)
    }
    with open(file_path, 'w') as f:
        json.dump(data, f)
    print(f"Generated {filename}")

if __name__ == "__main__":
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Starting auto simulation for {STATION_ID}...")
    try:
        while True:
            generate_spectrum()
            generate_wifi()
            generate_health()
            print("Waiting for next cycle...", flush=True)
            time.sleep(60) # Generate every 1 minute
    except KeyboardInterrupt:
        print("Simulation stopped.")
