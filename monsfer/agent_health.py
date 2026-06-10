import time
import psutil
import requests
import json
from datetime import datetime
from agent_core import load_config, setup_logging, get_paths

logger = setup_logging("agent_health")

def metrics():
    cpu_util = psutil.cpu_percent(interval=1)
    cpu_temp = 0.0
    try:
        t = psutil.sensors_temperatures()
        if 'coretemp' in t:
            cpu_temp = t['coretemp'][0].current
        elif 'thermal_zone0' in t:
            cpu_temp = t['thermal_zone0'][0].current
    except:
        pass
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_seconds = time.time() - psutil.boot_time()
    return {
        'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
        'cpuUtil': cpu_util,
        'cpuTemp': cpu_temp,
        'freeRAM': ram.available / (1024 * 1024),
        'totalRAM': ram.total / (1024 * 1024),
        'freeStorage': disk.free / (1024 * 1024 * 1024),
        'totalStorage': disk.total / (1024 * 1024 * 1024),
        'uptime_seconds': uptime_seconds
    }

def run():
    logger.info("start agent_health (File Drop Mode)")
    while True:
        try:
            config = load_config()
            paths = get_paths(config)
            payload = metrics()
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            station = config.get('station_id', '07plamongan_indah')
            # Consistent with file_manager.py logic for simulation group
            station_id_str = "07001" if "07" in station else station
            
            fn = paths['upload'] / f"{station_id_str}_HEALTH_{ts}.json"
            paths['upload'].mkdir(parents=True, exist_ok=True)
            
            with open(fn, 'w') as f:
                json.dump(payload, f, indent=2)
                
            logger.info(f"Generated Health JSON: {fn.name}")
                
            time.sleep(config.get('intervals', {}).get('health_check', 30))
        except Exception as e:
            logger.error(f"loop error {e}")
            time.sleep(10)

if __name__ == "__main__":
    run()
