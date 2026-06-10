# Panduan Pengecekan Manual Monsfer Project

Untuk melihat seluruh hasil perbaikan yang telah kita lakukan secara manual, ikuti langkah-langkah di bawah ini. Anda sebaiknya membuka **dua terminal (Command Prompt/PowerShell)** agar bisa menjalankan Server dan SDR secara bersamaan.

---

## Langkah 1: Jalankan Server (Terminal 1)
Ini adalah langkah untuk menghidupkan backend/UI server yang telah kita modifikasi.

1. Buka Terminal 1.
2. Masuk ke folder server:
   ```bash
   cd C:\Users\3KOM\monsfer_project_final\monsfer-server
   ```
3. Jalankan server secara normal:
   ```bash
   python server.py
   ```
4. Buka browser dan akses UI Anda, biasanya di `http://127.0.0.1:5000` (atau port yang biasa Anda gunakan).

---

## Langkah 2: Jalankan Auto-Simulate SDR (Terminal 2)
Langkah ini berguna untuk menjalankan "mesin pembuat data dummy" seolah-olah SDR perangkat keras nyata sedang menangkap sinyal di Plamongan Indah, lalu mengunggahnya.

1. Buka Terminal 2.
2. Masuk ke folder SDR:
   ```bash
   cd C:\Users\3KOM\monsfer_project_final\monsfer
   ```
3. Jalankan auto simulate script yang baru kita buat:
   ```bash
   python auto_simulate.py
   ```
4. *(Opsional)* Jika Anda ingin data simulasi tadi **otomatis terunggah** ke server, buka **Terminal 3** dan jalankan pengunggah data SDR:
   ```bash
   cd C:\Users\3KOM\monsfer_project_final\monsfer
   python agent_sync.py
   ```

---

## Langkah 3: Hal yang Harus Anda Cek di UI (Browser)
Setelah Server berjalan dan Data disimulasikan, buka Browser Anda dan cek hal-hal berikut:

✅ **Mode Terang (Light Mode)**
1. Klik tombol pengubah tema (Theme) dari Dark ke Light.
2. Perhatikan perbedaan skema warna; sekarang UI mode terang tidak berwarna putih terang mencolok, melainkan *off-white/abu-abu halus* yang jauh lebih nyaman untuk mata.

✅ **Cek Nama Subservice & Band**
1. Buka menu **Monitoring**.
2. Lihat bagian pilihan dropdown/filter frekuensi. Nama yang muncul tidak lagi "Band 1" atau "Band 2", tapi nama aslinya seperti **FM Broadcasting**, **Aeronautical**, dll.

✅ **Cek Fitur Download Gabungan 24 Jam**
1. Pada menu Monitoring atau Dashboard, cari tombol untuk **Download Data CSV**.
2. Pilih jumlah hari ke belakang (misal H-1 / 1 hari yang lalu).
3. Anda seharusnya sekarang bisa mengunduh file, dan jika file tersebut dibuka, seluruh data frekuensi selama 1 hari (yang dipisahkan dalam banyak file kecil) sudah dikompilasi (digabungkan) ke dalam satu CSV memanjang dengan urutan waktu.

✅ **Cek Halaman Settings**
1. Buka menu **Settings** di navigasi Anda.
2. Halaman seharusnya akan langsung terbuka tanpa ada *alert / pop-up* yang mengatakan "Gagal memuat settings" lagi, karena endpoint `/api/settings` telah dibuat.

---

## Langkah 4: Pengecekan Tata Letak Folder (File Manager)
Untuk memastikan data dari SDR diletakkan ke folder yang benar, silakan buka File Explorer biasa di Windows Anda:

1. Pergi ke: `C:\Users\3KOM\monsfer_project_final\userdata\`
2. Masuk ke folder akun Anda, lalu ke folder site `07plamongan_indah` (atau site lain yang sedang disimulasikan).
3. **Cek Subfolder:** Seharusnya di dalam sana, file otomatis sudah disortir dan dimasukkan dengan rapi ke dalam tiga folder terpisah:
   - `spectrum/` (untuk data frekuensi .csv)
   - `wifi/` (untuk data scan wifi .csv)
   - `health/` (untuk data status sistem seperti RAM/CPU .json)
