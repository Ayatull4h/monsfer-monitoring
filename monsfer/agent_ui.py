from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import psutil
import random
from datetime import datetime
from pathlib import Path
from agent_core import load_config, get_paths

app = Flask(__name__)
BASE_DIR = Path(__file__).parent.absolute()

def is_agent_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower() and proc.info['cmdline']:
                cmd = ' '.join(proc.info['cmdline'])
                if 'agent_acquisition.py' in cmd or 'agent_wifi.py' in cmd or 'agent_sync.py' in cmd:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

@app.route('/')
def index():
    config = load_config()
    status = "Running" if is_agent_running() else "Stopped"
    return render_template('index.html', config=config, status=status)

@app.route('/api/status')
def status():
    return jsonify({
        "agent_running": is_agent_running(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    try:
        new_config = request.json
        config_path = BASE_DIR / "config" / "agent_config.json"
        
        # Load existing
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Update fields
        config['station_id'] = new_config.get('station_id', config['station_id'])
        config['server_url'] = new_config.get('server_url', config['server_url'])
        
        # Save
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        return jsonify({"status": "success", "message": "Config updated"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def simulate_data():
    try:
        data = request.json
        station_id = data.get('station_id')
        if not station_id:
            return jsonify({"status": "error", "message": "Station ID required"}), 400
            
        # Trigger agent_acquisition simulation logic or create file directly
        # For simplicity in simulation mode, we'll create a file in data_upload directly
        config = load_config()
        paths = get_paths(config)
        
        # Ensure upload dir exists
        upload_path = BASE_DIR / paths['upload']
        upload_path.mkdir(parents=True, exist_ok=True)
        
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{station_id}_MONITORING_{ts}.csv"
        file_path = upload_path / filename
        
        with open(file_path, 'w') as f:
            f.write("#STATION_ID\n")
            f.write(f"station_id;{station_id}\n")
            f.write(f"date;{datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"time;{datetime.now().strftime('%H:%M:%S')}\n")
            f.write(f"station_name;Simulation Site\n")
            f.write("latitude;-7.0291707\n")
            f.write("longitude;110.4975072\n\n")
            f.write("#BAND_CONFIGURATION\n")
            f.write("band_number;start_frequency_mhz;end_frequency_mhz;step_bw_khz\n")
            f.write("1;88.0;108.0;100.0\n\n")
            f.write("#MEASUREMENT_DATA\n")
            f.write("frequency_mhz;level_dbfs\n")
            for i in range(200):
                f.write(f"{88.0 + (i*0.1):.1f};{random.uniform(-95, -45):.3f}\n")
                
        return jsonify({"status": "success", "message": f"Simulated data generated for {station_id}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Ensure config and template dirs exist
    os.makedirs(BASE_DIR / 'templates', exist_ok=True)
    os.makedirs(BASE_DIR / 'config', exist_ok=True)
    app.run(host='0.0.0.0', port=5100, debug=False)
