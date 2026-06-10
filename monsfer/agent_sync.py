import time
import shutil
import os
import requests
from datetime import datetime, timedelta
from agent_core import load_config, setup_logging, get_paths

logger = setup_logging("agent_sync")

def check_disk_health(paths, policy):
    """
    Monitors disk usage and aggressively cleans up if limits are breached.
    Returns True if disk is healthy, False if critical.
    """
    try:
        total, used, free = shutil.disk_usage(paths['data'])
        free_gb = free / (1024**3)
        percent_used = (used / total) * 100
        
        logger.info(f"Disk Status: {percent_used:.1f}% used, {free_gb:.2f} GB free")

        # Thresholds
        max_percent = policy.get('max_usage_percent', 85)
        min_free = policy.get('min_free_gb', 1.0)

        if percent_used > max_percent or free_gb < min_free:
            logger.warning("DISK WARNING: Threshold breached. Initiating emergency cleanup.")
            cleanup_archive(paths['archive'], target_mb=0) # Delete all archives
            
            # Re-check
            total, used, free = shutil.disk_usage(paths['data'])
            if (used / total) * 100 > max_percent:
                logger.error("DISK CRITICAL: Still full after archive cleanup. Purging upload queue.")
                cleanup_directory(paths['upload']) # Data loss scenario to save OS
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking disk: {e}")
        return True

def cleanup_archive(archive_path, target_mb=None, days=None):
    """
    Cleans up archive directory based on size or age.
    """
    if not archive_path.exists():
        return

    files = sorted(archive_path.glob('*'), key=os.path.getmtime)
    
    # Age-based cleanup
    if days is not None:
        cutoff = time.time() - (days * 86400)
        for f in files:
            if f.stat().st_mtime < cutoff:
                try:
                    if f.is_file(): f.unlink()
                    logger.info(f"Deleted old archive: {f.name}")
                except Exception as e:
                    logger.error(f"Failed delete {f.name}: {e}")

    # Size-based cleanup (keep deleting oldest until under target_mb)
    if target_mb is not None:
        current_size = sum(f.stat().st_size for f in archive_path.glob('*') if f.is_file()) / (1024*1024)
        while current_size > target_mb and files:
            f = files.pop(0) # Oldest
            try:
                if f.is_file():
                    s = f.stat().st_size / (1024*1024)
                    f.unlink()
                    current_size -= s
                    logger.info(f"Deleted for space: {f.name}")
            except Exception as e:
                logger.error(f"Failed delete {f.name}: {e}")

def cleanup_directory(path):
    for f in path.glob('*'):
        try:
            if f.is_file(): f.unlink()
        except: pass

def run():
    logger.info("Starting Sync & Disk Guardian Agent...")
    
    while True:
        config = load_config()
        paths = get_paths(config)
        policy = config.get('disk_policy', {})
        
        # Ensure directories exist
        for p in paths.values():
            p.mkdir(parents=True, exist_ok=True)

        # 1. Disk Health Check & Emergency Cleanup
        check_disk_health(paths, policy)

        # 2. Upload Process
        upload_files = list(paths['upload'].glob('*.json')) + list(paths['upload'].glob('*.csv'))
        if upload_files:
            logger.info(f"Found {len(upload_files)} files to upload.")
            server_url = config.get('server_url', 'http://localhost:5102').rstrip('/')
            token = config.get('token', '')
            station_id = config.get('station_id', '')
            
            for fp in upload_files:
                try:
                    url = f"{server_url}/upload"
                    headers = {'X-Station-Token': token}
                    data = {'station_id': station_id}
                    
                    logger.info(f"Uploading {fp.name} to {url}...")
                    
                    with open(fp, 'rb') as f:
                        files = {'file': f}
                        resp = requests.post(url, headers=headers, data=data, files=files, timeout=30)
                    
                    if resp.status_code == 200:
                        success = True
                        shutil.move(str(fp), str(paths['archive'] / fp.name))
                        logger.info(f"Uploaded and archived: {fp.name}")
                    else:
                        logger.error(f"Upload failed for {fp.name}: {resp.status_code} - {resp.text}")
                        success = False
                        
                except Exception as e:
                    logger.error(f"Upload exception for {fp.name}: {e}")


        # 3. Routine Cleanup (Maintenance)
        cleanup_archive(
            paths['archive'], 
            target_mb=policy.get('max_archive_size_mb', 500),
            days=policy.get('retention_days', 1)
        )

        time.sleep(config.get('intervals', {}).get('sync', 10))

if __name__ == "__main__":
    run()
