import time
import random
import requests
import json
import subprocess
import shutil
from datetime import datetime
from agent_core import load_config, setup_logging, get_paths

logger = setup_logging("agent_wifi")

def run_nmcli():
    """Run nmcli to get real wifi data on Linux"""
    try:
        if shutil.which("nmcli") is None:
            return None
        
        # nmcli -t -f SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY dev wifi
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY", "dev", "wifi"], 
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0:
            return None
            
        networks = []
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            parts = line.split(':')
            if len(parts) >= 6:
                ssid = parts[0]
                bssid = ":".join(parts[1:7]).replace('\\:', ':') if len(parts) > 6 else parts[1]
                # Sometimes SSID has colons, so we take from the end
                security = parts[-1]
                signal = parts[-2]
                freq = parts[-3].replace(' MHz', '')
                chan = parts[-4]
                
                networks.append({
                    'ssid': ssid if ssid else "Hidden",
                    'bssid': bssid,
                    'channel': int(chan) if chan.isdigit() else 0,
                    'frequency_mhz': int(freq) if freq.isdigit() else 2412,
                    'signal_dbm': int(signal) if signal.lstrip('-').isdigit() else -100,
                    'security': security,
                    'last_seen': datetime.utcnow().strftime('%Y-%m-%d ; %H-%M'),
                    'hidden': True if not ssid else False
                })
        return networks
    except Exception as e:
        logger.error(f"nmcli error: {e}")
        return None

def scan_mock():
    """Mock scan if nmcli is not available"""
    out = []
    ssids = ['Home_WiFi', 'Office_Guest', 'Cafe_Free', 'Neighbor_Net', 'Hidden_IoT']
    for _ in range(random.randint(3, 8)):
        ssid = random.choice(ssids) + f"_{random.randint(1, 99)}"
        out.append({
            'ssid': ssid,
            'bssid': f"00:11:22:33:44:{random.randint(10, 99)}",
            'channel': random.randint(1, 11),
            'frequency_mhz': 2412 + (random.randint(0, 10) * 5),
            'signal_dbm': random.randint(-90, -40),
            'security': random.choice(['WPA2 CCMP', 'Open', 'WPA3 SAE']),
            'last_seen': datetime.utcnow().strftime('%Y-%m-%d ; %H-%M'),
            'hidden': False
        })
    return out

def write_csv(networks, filepath):
    now = datetime.utcnow()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("date;time;bssid;frequency;signal;ssid;vendor\n")
        for net in networks:
            ssid = net.get('ssid', 'Hidden')
            bssid = net.get('bssid', '00:00:00:00:00:00')
            freq = net.get('frequency_mhz', 2412)
            sig = net.get('signal_dbm', -100)
            vendor = "RaspberryPi_WLAN"
            f.write(f"{date_str};{time_str};{bssid};{freq};{sig};{ssid};{vendor}\n")

def run():
    logger.info("Starting WiFi Scanner Agent (CSV mode)")
    while True:
        try:
            config = load_config()
            paths = get_paths(config)
            
            # Try nmcli first, fallback to mock
            networks = run_nmcli()
            if not networks:
                networks = scan_mock()
                
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            station = config.get('station_id', '07plamongan_indah')
            st_group = ''.join([c for c in station if c.isdigit()])[:2] or '07'
            # Format requires {STATION_ID}_WIFI_{TIMESTAMP}.csv
            # For compatibility with simulation folder structure, we use the device group/id format
            # If station is like 07plamongan_indah, let's use 07001 to ensure server routes it properly
            station_id_str = "07001" if "07" in station else station
            
            fn = paths['upload'] / f"{station_id_str}_WIFI_{ts}.csv"
            paths['upload'].mkdir(parents=True, exist_ok=True)
            
            write_csv(networks, fn)
            logger.info(f"Generated WiFi CSV: {fn.name}")
                
            time.sleep(config.get('intervals', {}).get('wifi_interval', 60))
            
        except Exception as e:
            logger.error(f"WiFi Loop error {e}")
            time.sleep(10)

if __name__ == "__main__":
    run()
