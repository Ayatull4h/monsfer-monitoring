import os
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths
base_dir = Path(__file__).parent / "userdata" / "semarang" / "plamongan indah"
spectrum_dir = base_dir / "spectrum"
wifi_dir = base_dir / "wifi"
health_dir = base_dir / "health"

# Create directories
for d in [spectrum_dir, wifi_dir, health_dir]:
    d.mkdir(parents=True, exist_ok=True)

# Time logic
now = datetime.now()
dates_to_generate = [
    now.date() - timedelta(days=1), # Yesterday (H-1)
    now.date()                      # Today (H-0)
]

STATION_ID = "07001"

def generate_spectrum_file(dt):
    filename = f"{dt.strftime('%Y-%m-%d')}_{dt.strftime('%H-%M-%S')}.csv"
    filepath = spectrum_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("#STATION_ID\n")
        f.write(f"station_id;{STATION_ID}\n")
        f.write(f"date;{dt.strftime('%Y-%m-%d')}\n")
        f.write(f"time;{dt.strftime('%H:%M:%S')}\n")
        f.write(f"station_name;Plamongan Indah\n")
        f.write("latitude;-7.0291707\n")
        f.write("longitude;110.4975072\n\n")
        f.write("#BAND_CONFIGURATION\n")
        f.write("band_number;start_frequency_mhz;end_frequency_mhz;step_bw_khz\n")
        f.write("1;87.0;108.0;6.25\n\n")
        f.write("#MEASUREMENT_DATA\n")
        f.write("frequency_mhz;level_dbfs\n")
        
        # Generasi 200 data frekuensi
        for i in range(200):
            freq = 87.0 + (i * 0.1)
            level = random.uniform(-95, -70)
            # Dummy active FM stations
            if abs(freq - 88.0) < 0.2 or abs(freq - 105.0) < 0.2:
                level = random.uniform(-40, -20)
            f.write(f"{freq:.1f};{level:.3f}\n")

def generate_wifi_file(dt):
    filename = f"{dt.strftime('%Y-%m-%d')}_{dt.strftime('%H-%M-%S')}.csv"
    filepath = wifi_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("date;time;bssid;frequency;signal;ssid;vendor\n")
        for i in range(10):
            freq = random.choice([2412, 2437, 2462, 5180, 5745])
            sig = random.randint(-85, -30)
            bssid = f"00:11:22:33:44:{random.randint(10, 99)}"
            vendor = random.choice(["TP-Link", "Huawei", "ZTE", "Ubiquiti"])
            ssid = f"Wifi_Dummy_{i}"
            f.write(f"{dt.strftime('%Y-%m-%d')};{dt.strftime('%H:%M:%S')};{bssid};{freq};{sig};{ssid};{vendor}\n")

def generate_health_file(dt):
    filename = f"{dt.strftime('%Y-%m-%d')}_{dt.strftime('%H-%M-%S')}.json"
    filepath = health_dir / filename
    
    data = {
        "timestamp": dt.isoformat(),
        "cpuUtil": round(random.uniform(10, 80), 1),
        "cpuTemp": round(random.uniform(40, 65), 1),
        "freeStorage": round(random.uniform(10, 50), 2),
        "totalStorage": 128.0,
        "freeRAM": round(random.uniform(1000, 3000), 2),
        "totalRAM": 4096.0
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def main():
    print("Mulai membuat data dummy untuk H-1 dan H-0...")
    for target_date in dates_to_generate:
        # Buat 24 data (1 per jam) untuk spectrum, wifi, dan health per harinya
        for hour in range(24):
            # Cuma bikin sampe jam sekarang jika harinya hari ini
            if target_date == now.date() and hour > now.hour:
                break
                
            dt = datetime(target_date.year, target_date.month, target_date.day, hour, 0, 0)
            generate_spectrum_file(dt)
            generate_wifi_file(dt)
            generate_health_file(dt)
            
    print(f"Selesai! Data berhasil diisikan ke {base_dir}")

if __name__ == "__main__":
    main()
