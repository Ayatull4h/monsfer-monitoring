import time
import random
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
import csv
from agent_core import load_config, setup_logging, get_paths

logger = setup_logging("agent_acquisition")

def read_subservices(base_dir):
    """Read bands from subservice.csv or use defaults"""
    bands = []
    csv_path = Path(base_dir) / 'config' / 'subservice.csv'
    if csv_path.exists():
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if len(row) >= 5 and row[4] == '1': # Active
                        bands.append({
                            'band_number': int(row[0]),
                            'name': row[1],
                            'start_hz': int(row[2]),
                            'stop_hz': int(row[3]),
                            'step_hz': 6250 # Default step 6.25kHz
                        })
            return bands
        except Exception as e:
            logger.error(f"Error reading subservice.csv: {e}")
    
    # Default bands if file missing
    return [
        {'band_number': 1, 'name': 'Radio FM', 'start_hz': 88000000, 'stop_hz': 108000000, 'step_hz': 100000}
    ]

def read_identity(base_dir, config):
    """Read identity from identity.csv or config"""
    csv_path = Path(base_dir) / 'config' / 'identity.csv'
    if csv_path.exists():
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if len(row) >= 8:
                        return {
                            'station_id': row[0],
                            'station_name': row[2],
                            'latitude': row[6],
                            'longitude': row[7]
                        }
        except Exception as e:
            logger.error(f"Error reading identity.csv: {e}")
            
    # Fallback to config
    station = config.get('station_id', '07plamongan_indah')
    st_group = ''.join([c for c in station if c.isdigit()])[:2] or '07'
    return {
        'station_id': station,
        'station_name': station[2:].replace('_', ' ').title(),
        'latitude': '-7.0291707',
        'longitude': '110.4975072'
    }

def simulate_rtl_power(start_hz, stop_hz, step_hz):
    """Simulates the output of rtl_power if hardware is missing"""
    results = []
    current = start_hz
    while current <= stop_hz:
        results.append((current, random.uniform(-95.0, -55.0)))
        current += step_hz
    return results

def run_rtl_power(start_hz, stop_hz, step_hz):
    """Runs rtl_power and returns a list of (frequency, dbm) tuples"""
    # Check if rtl_power is in PATH
    if shutil.which("rtl_power") is None:
        logger.warning("rtl_power not found in PATH. Simulating data.")
        return simulate_rtl_power(start_hz, stop_hz, step_hz)

    # Use a temporary file for rtl_power output
    tmp_file = f"/tmp/rtl_power_tmp_{start_hz}.csv"
    cmd = [
        "rtl_power",
        "-f", f"{start_hz}:{stop_hz}:{step_hz}",
        "-c", "0.2",
        "-g", "3",
        "-i", "1s", # 1 second interval for fast one-shot
        "-1", # One shot
        tmp_file
    ]
    
    try:
        logger.info(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, timeout=60)
        
        # Parse the raw rtl_power CSV
        results = []
        if os.path.exists(tmp_file):
            with open(tmp_file, 'r') as f:
                for line in f:
                    parts = line.strip().split(', ')
                    if len(parts) > 6:
                        hz_low = int(float(parts[2]))
                        hz_high = int(float(parts[3]))
                        hz_step = float(parts[4])
                        dbm_values = [float(x) for x in parts[6:]]
                        
                        f_current = hz_low
                        for dbm in dbm_values:
                            results.append((f_current, dbm))
                            f_current += hz_step
            os.remove(tmp_file)
        return results
    except Exception as e:
        logger.error(f"rtl_power failed: {e}. Simulating instead.")
        return simulate_rtl_power(start_hz, stop_hz, step_hz)

def generate_final_csv(identity, bands_data, output_path):
    """Writes the data into the final #STATION_ID format required by the UI"""
    now = datetime.utcnow()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # 1. Station ID Section
        f.write("#STATION_ID\n")
        f.write(f"station_id;{identity['station_id']}\n")
        f.write(f"date;{now.strftime('%Y-%m-%d')}\n")
        f.write(f"time;{now.strftime('%H:%M:%S')}\n")
        f.write(f"station_name;{identity['station_name']}\n")
        f.write(f"latitude;{identity['latitude']}\n")
        f.write(f"longitude;{identity['longitude']}\n")
        f.write("\n")
        
        # 2. Band Configuration Section
        f.write("#BAND_CONFIGURATION\n")
        f.write("band_number;start_frequency_mhz;end_frequency_mhz;step_bw_khz\n")
        for bd in bands_data:
            start_mhz = bd['band']['start_hz'] / 1000000.0
            stop_mhz = bd['band']['stop_hz'] / 1000000.0
            step_khz = bd['band']['step_hz'] / 1000.0
            f.write(f"{bd['band']['band_number']};{start_mhz};{stop_mhz};{step_khz}\n")
        f.write("\n")
        
        # 3. Measurement Data Section
        f.write("#MEASUREMENT_DATA\n")
        f.write("frequency_mhz;level_dbfs\n")
        for bd in bands_data:
            for freq_hz, dbm in bd['data']:
                freq_mhz = freq_hz / 1000000.0
                f.write(f"{freq_mhz:.6f};{dbm:.3f}\n")

def run():
    logger.info("Starting SDR Acquisition Agent")
    base_dir = Path(__file__).parent.absolute()
    
    while True:
        try:
            config = load_config()
            paths = get_paths(config)
            paths['data'].mkdir(parents=True, exist_ok=True)
            paths['upload'].mkdir(parents=True, exist_ok=True)
            
            identity = read_identity(base_dir, config)
            bands = read_subservices(base_dir)
            
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            out_filename = f"{identity['station_id']}_MONITORING_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
            out_path = paths['data'] / out_filename
            
            logger.info(f"Starting scan for {len(bands)} bands...")
            bands_data = []
            
            for band in bands:
                logger.info(f"Scanning band {band['band_number']} ({band['name']})")
                data = run_rtl_power(band['start_hz'], band['stop_hz'], band['step_hz'])
                bands_data.append({
                    'band': band,
                    'data': data
                })
            
            # Write aggregated final CSV
            generate_final_csv(identity, bands_data, out_path)
            
            # Move to upload queue
            final_upload_path = paths['upload'] / out_filename
            out_path.rename(final_upload_path)
            logger.info(f"Successfully generated and queued: {final_upload_path.name}")
            
        except Exception as e:
            logger.error(f"Fatal error in acquisition loop: {e}")
            
        time.sleep(config.get('intervals', {}).get('acquisition_interval', 60))

if __name__ == "__main__":
    run()
