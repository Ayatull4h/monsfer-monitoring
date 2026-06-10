# Tutorial Deploy & Clone SDR Agent ke Banyak Lokasi

## Arsitektur

```
[SDR Dongle] --USB--> [Raspberry Pi] --HTTP--> [Server 10.100.80.140:5000] --reverse--> [Monitoring UI :5005]
                            ^
                            |
                    Banyak lokasi (clone)
```

Tiap lokasi punya **1 Raspberry Pi + 1 SDR dongle**. Pi mengolah data spektrum, WiFi, dan health, lalu dikirim ke server pusat `10.100.80.140:5000`. Server menyajikan data ke UI Monitoring.

---

## Yang Perlu Disiapkan

- Raspberry Pi (sudah terinstall OS)
- RTL-SDR dongle (colok USB)
- Monitor + keyboard untuk setup awal (atau SSH)
- USB flashdisk untuk mindahin file (atau clone langsung dari GitHub)

---

## Setup Awal (cukup sekali)

### Langkah 1 — Copy file ke Pi

Copy folder **`monsfer/`** dan **`linux/`** ke `/home/pi/` di Raspberry Pi.

**Via flashdisk:** colok USB, buka File Manager, copy-paste.

**Via SCP dari laptop:**
```bash
scp -r monsfer linux pi@IP_PI:/home/pi/
```

### Langkah 2 — Install sekali jalan

Buka terminal di Raspberry Pi:

```bash
cd /home/pi/linux
chmod +x install_sdr.sh
./install_sdr.sh --station 07001 --site "Plamongan Indah"
```

Script ini otomatis melakukan:
1. Install driver RTL-SDR (`rtl-sdr`, `librtlsdr-dev`)
2. Buat Python virtual environment
3. Install dependencies (`requests`, `psutil`)
4. Generate file konfigurasi (`agent_config.json`, `identity.csv`)
5. Verifikasi dongle SDR terdeteksi
6. Start semua agent

### Langkah 3 — Cek status

```bash
cd /home/pi/monsfer
./start_agent.sh status
```

Output yang diharapkan:
```
SDR Agent Status:
-----------------
  [RUNNING] acquisition (PID: 1234)
  [RUNNING] health (PID: 1235)
  [RUNNING] wifi (PID: 1236)
  [RUNNING] sync (PID: 1237)
```

### Langkah 4 — Cek data terkirim ke server

```bash
tail -f /home/pi/monsfer/logs/sync.log
```

Kalau berhasil akan terlihat:
```
Uploaded and archived: 07001_MONITORING_2026-06-10_10-30-00.csv
Uploaded and archived: 07001_WIFI_2026-06-10_10-30-00.csv
Uploaded and archived: 07001_HEALTH_2026-06-10_10-30-00.json
```

---

## Clone ke Lokasi Lain

Ini bagian terpenting. Untuk memasang di lokasi lain dengan Pi baru:

### Cara 1 — Clone folder via flashdisk (recommended)

1. Copy folder **`monsfer/`** + **`linux/`** dari Pi pertama ke flashdisk
2. Colok flashdisk ke Pi baru
3. Copy ke `/home/pi/`

```bash
cp -r /media/pi/USB/monsfer /home/pi/
cp -r /media/pi/USB/linux /home/pi/
```

4. Jalankan install dengan station ID yang berbeda:

```bash
cd /home/pi/linux
./install_sdr.sh --station 07002 --site "Simongan"
```

Selesai. **Pi kedua sudah berjalan dengan identitas berbeda**, data akan masuk ke server dengan station ID `07002`.

### Cara 2 — Clone via GitHub

```bash
git clone https://github.com/Ayatull4h/monsfer-monitoring.git
cd monsfer-monitoring/linux
./install_sdr.sh --station 07002 --site "Simongan"
```

---

## Tabel Station ID

Setiap lokasi harus punya station ID unik. Contoh:

| Lokasi | Station ID | Perintah |
|---|---|---|
| Plamongan Indah | `07001` | `--station 07001 --site "Plamongan Indah"` |
| Simongan | `07002` | `--station 07002 --site "Simongan"` |
| Tembalang | `07003` | `--station 07003 --site "Tembalang"` |
| Kota Baru | `07004` | `--station 07004 --site "Kota Baru"` |
| Pandanaran | `07005` | `--station 07005 --site "Pandanaran"` |

Format bebas, misal:
- `JKT01`, `JKT02`, `BDG01` ...
- Yang penting **unik** dan konsisten

---

## Mengubah Konfigurasi Setelah Install

Kalau sudah terlanjur install dan ingin mengubah sesuatu:

### Ubah station ID / site name

```bash
cd /home/pi/monsfer
./start_agent.sh stop
nano config/agent_config.json
nano config/identity.csv
./start_agent.sh start
```

### Ubah alamat server

```bash
cd /home/pi/monsfer
./start_agent.sh stop
nano config/agent_config.json
# Ganti "server_url" ke alamat baru
./start_agent.sh start
```

### Ubah interval scan

Edit `config/agent_config.json` bagian `intervals`:
```json
"intervals": {
    "health_check": 30,
    "sync": 15,
    "acquisition_interval": 30,
    "wifi_interval": 60
}
```

Lalu restart: `./start_agent.sh restart`

---

## Perintah Kontrol Agent

| Perintah | Fungsi |
|---|---|
| `./start_agent.sh start` | Jalankan semua agent |
| `./start_agent.sh stop` | Matikan semua agent |
| `./start_agent.sh restart` | Restart semua agent |
| `./start_agent.sh status` | Cek status masing-masing agent |

---

## Melihat Log

```bash
# Log scan spektrum
tail -f /home/pi/monsfer/logs/acquisition.log

# Log WiFi
tail -f /home/pi/monsfer/logs/wifi.log

# Log health sistem
tail -f /home/pi/monsfer/logs/health.log

# Log upload ke server
tail -f /home/pi/monsfer/logs/sync.log
```

---

## Struktur File Penting di `monsfer/`

```
monsfer/
├── agent_acquisition.py    # Scan spektrum via RTL-SDR
├── agent_health.py         # Monitor CPU/RAM/disk Pi
├── agent_wifi.py           # Scan WiFi via nmcli
├── agent_sync.py           # Upload data ke server
├── agent_core.py           # Utility (config, logging)
├── start_agent.sh          # Start/stop/status agent
├── bootstrap_monsfer.sh    # Generate config + systemd service
├── requirements.txt        # Python dependencies
├── config/
│   ├── agent_config.json   # Konfigurasi utama (station_id, server_url, interval)
│   ├── identity.csv        # Identitas stasiun
│   └── subservice.csv      # Daftar band frekuensi yang discan
└── systemd/
    ├── sdr-agent-acquisition.service
    ├── sdr-agent-health.service
    ├── sdr-agent-wifi.service
    └── sdr-agent-sync.service
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `rtl_power not found` | RTL-SDR tidak terdeteksi | Colok dongle USB, jalankan `./start_agent.sh restart` |
| `Connection refused` | Server tidak merespon | Pastikan server di `10.100.80.140:5000` sudah jalan |
| `sync.log` error upload | Koneksi jaringan | Cek kabel/Ping ke `10.100.80.140` |
| Log penuh (besar) | Tidak ada log rotation | Sudah otomatis, max 5MB per file (2 backup) |
| Ingin ganti port server | Port berbeda | Edit `agent_config.json` → `server_url`, lalu restart |
