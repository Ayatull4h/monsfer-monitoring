import os
import sys
import logging
from pathlib import Path

# Setup correct import path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config_loader import config
DATA_DIR = Path(config.DATA_DIR)

effective_username = "3KOM"
site_name = "07plamongan_indah"

wifi_dir = Path(DATA_DIR) / effective_username / site_name / 'wifi'
print("Checking wifi_dir:", wifi_dir)
print("Exists:", wifi_dir.exists())

if wifi_dir.exists():
    wifi_files = sorted(wifi_dir.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True)
    print("Found files count:", len(wifi_files))
    if wifi_files:
        print("Latest file:", wifi_files[0])
        latest_file = wifi_files[0]
        with open(latest_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("Lines count:", len(lines))
            start_idx = 0
            if lines and 'bssid' in lines[0].lower():
                start_idx = 1
                print("Header found, starting at line 1")
            
            networks = []
            for i, line in enumerate(lines[start_idx:]):
                if line.strip():
                    try:
                        parts = [part.strip() for part in line.strip().split(';')]
                        if len(parts) >= 5:
                            date, time, bssid, frequency, signal = parts[:5]
                            ssid = parts[5] if len(parts) > 5 else ''
                            vendor = parts[6] if len(parts) > 6 else ''
                            
                            frequency = int(frequency)
                            # Let's print out what we parsed
                            print(f"Line {i}: parsed bssid={bssid} frequency={frequency} signal={signal} ssid={ssid} vendor={vendor}")
                            
                            if 2412 <= frequency <= 2484:  # 2.4GHz band
                                band = '2.4GHz'
                                channel = (frequency - 2407) // 5
                            elif 5170 <= frequency <= 5825:  # 5GHz band
                                band = '5.8GHz'
                                channel = (frequency - 5000) // 5
                            else:
                                print(f"Line {i} frequency {frequency} is out of band range!")
                                continue
                            
                            signal = float(signal)
                            networks.append({
                                'date': date,
                                'time': time,
                                'bssid': bssid,
                                'frequency': int(frequency),
                                'signal': float(signal),
                                'ssid': ssid,
                                'vendor': vendor,
                                'band': band,
                                'channel': int(channel)
                            })
                    except Exception as e:
                        print(f"Error parsing line {i}: {e}")
            print("Total networks parsed successfully:", len(networks))
else:
    print("Directory does not exist!")
