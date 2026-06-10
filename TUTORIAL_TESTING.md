# 🛡️ Panduan Pengujian & Simulasi Monsfer SDR

Dokumen ini berisi langkah-langkah untuk melakukan testing manual sistem Monsfer SDR dalam mode simulasi (tanpa perangkat keras SDR).

---

## 1. Persiapan Awal
Pastikan Anda berada di folder utama proyek:
`C:\Users\3KOM\monsfer_project_final`

Sistem terdiri dari 3 komponen utama yang berjalan di port berikut:
- **Port 5102**: Backend Gateway (Pintu masuk data)
- **Port 5105**: Monitoring Dashboard (Tampilan Web utama)
- **Port 5100**: Agent UI (Simulator & Kontrol Agen)

---

## 2. Cara Menjalankan Sistem
Jika sistem belum berjalan, Anda bisa membukanya secara manual dengan menjalankan 3 perintah ini di terminal (PowerShell) yang berbeda:

1. **Jalankan Backend:**
   ```powershell
   cd "C:\Users\3KOM\monsfer_project_final\monsfer-server"
   python server.py
   ```
2. **Jalankan Dashboard:**
   ```powershell
   cd "C:\Users\3KOM\monsfer_project_final\monsfer-server\MONITORING_UI"
   python app.py
   ```
3. **Jalankan Simulator Agen:**
   ```powershell
   cd "C:\Users\3KOM\monsfer_project_final\monsfer"
   python agent_ui.py
   ```

---

## 3. Cara Melakukan Simulasi Data (Testing Manual)
Untuk mensimulasikan pengiriman data dari berbagai site, ikuti langkah ini:

1. Buka Browser dan akses **Agent UI**: `http://127.0.0.1:5100`
2. Cari bagian **"Site Simulation"**.
3. Di kolom **"Target Station ID"**, masukkan ID site yang ingin Anda tes.
   * *Contoh ID:* `07plamongan_indah` atau ID lain yang ada di folder `userdata`.
4. Klik tombol **"Generate & Send Data"**.
5. Tunggu muncul notifikasi *"Simulated data generated for..."*.

---

## 4. Cara Memeriksa Hasil
Setelah data dikirim dari simulator, Anda bisa memverifikasi hasilnya dengan dua cara:

1. **Cek Melalui Dashboard UI:**
   - Buka `http://127.0.0.1:5105`
   - Pilih site yang Anda simulasikan tadi.
   - Pastikan grafik spektrum muncul dengan data terbaru.
   
2. **Cek Melalui Folder File:**
   - Buka folder: `C:\Users\3KOM\monsfer_project_final\userdata`
   - Masuk ke sub-folder site yang Anda tes (misal: `07plamongan_indah`).
   - Cek di dalam folder `spectrum`, pastikan ada file CSV baru dengan timestamp saat ini.

---

## 5. Pelaporan Bug / Error
Jika saat pengujian Anda menemukan hal berikut, harap laporkan kepada saya:
- Halaman web tidak terbuka (Error 404/500).
- Tombol simulasi diklik tapi file tidak muncul di folder `userdata`.
- Grafik di dashboard tidak terupdate meski file sudah terkirim.

**Selamat Mencoba!** 🚀
