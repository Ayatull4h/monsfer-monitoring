# Tutorial: Memperbanyak Site SDR Agent

Dokumen ini menjelaskan cara menyalin dan memperbanyak agen SDR untuk digunakan di banyak site berbeda secara paralel atau pada PC/Raspberry Pi yang berbeda.

## 1. Persiapan Perangkat Baru (Linux / Raspberry Pi)
Jika menggunakan perangkat baru, cukup copy folder `monsfer_project_final/monsfer` ke dalam PC/perangkat tujuan.

Lalu jalankan skrip instalasi dari terminal:
```bash
cd monsfer_project_final/linux
./install_sdr.sh
```

## 2. Mengatur Identitas Site (Station ID)
Setiap agen SDR harus memiliki Station ID unik yang terdaftar pada Server Utama (contoh: `07plamongan_indah`, `01tugu_muda`, dll).

### Simulasi Manual
1. Jalankan agen dengan `./start_agent.sh` di folder `monsfer`.
2. Buka UI Lokal SDR di browser perangkat: `http://localhost:5100`.
3. Pada bagian **Site Simulation** atau menu utama, masukkan Station ID unik yang diinginkan, misal: `07plamongan_indah`.
4. Klik **Generate & Send Data**.

### Simulasi Otomatis
1. Kami telah menyediakan skrip `auto_simulate.py`.
2. Buka `auto_simulate.py` dan ubah variabel `STATION_ID = "07plamongan_indah"` sesuai dengan nama site baru.
3. Jalankan di background menggunakan screen atau systemd:
   ```bash
   nohup python auto_simulate.py > simulate.log 2>&1 &
   ```

## 3. Verifikasi di Server Monitoring
1. Buka halaman Dashboard Server Monitoring Utama (Port `5102/monitoring`).
2. Login sebagai UPT admin terkait.
3. Site baru yang mengirimkan data (simulasi/asli) otomatis akan masuk dan datanya dapat ditampilkan di UI.

## Tips: Menjalankan Banyak Site di 1 PC
Anda dapat menyimulasikan banyak site di satu PC dengan menjalankan file `auto_simulate.py` berkali-kali dengan Station ID yang berbeda, atau membuat skrip python master yang memanggil fungsi generate untuk array nama site (seperti `['site_A', 'site_B', 'site_C']`).
