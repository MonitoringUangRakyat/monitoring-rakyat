# Audit Project Monitoring Rakyat

Tanggal audit: 2026-06-13

## Status Singkat

Project sudah punya tiga fondasi penting:

- Dashboard HTML untuk UI publik.
- Gudang DB berbasis CSV per era, modul, dan tahun.
- AI index untuk membantu AI mencari file sumber.

Struktur ini sudah benar untuk prinsip "dashboard ringan, data mentah lengkap di belakang".

## Koreksi yang Sudah Dilakukan

- Tombol floating kuning "Buka AI" dihapus karena fitur AI sudah tersedia di command center atas.
- `dashboard/app.js` diarahkan ke katalog lokal `../gudang-db/index.html`.
- Dibuat `gudang-db/index.html` sebagai katalog Gudang DB yang membaca `_index/ai_index.json`.
- DB-Link dashboard dikoreksi dari pola lama `module/year.json` ke pola final `modul_tahun.csv`.
- Menu Parpol diperluas menjadi daftar DB "Dana Organisasi Publik" yang menggabungkan Parpol, Ormas/Yayasan/Hibah, dan bantuan organisasi dari APBN/APBD.
- Parpol/Organisasi Publik disinkronkan ke jurnal otomatis sektor `Hibah Parpol/Ormas`, sehingga ikut terbaca oleh Akuntansi, Buku Besar, CashFlow, dan Evidence.
- Dashboard publik dikunci ke periode berjalan Juni 2026. Data yang memiliki `tahun`/`bulan` di luar periode berjalan tidak ditampilkan di tabel publik dan diarahkan ke Gudang DB.
- Grafik dashboard memakai kerangka agregasi 20 tahun terakhir untuk rasio perbandingan; tahun tanpa DB tampil kosong/0.

## Temuan Utama

### 1. Data Masih Banyak Berupa Template

Gudang DB sudah rapi, tetapi banyak CSV masih berisi header tanpa data. Ini wajar untuk fase awal, tetapi publik harus diberi label jelas bahwa sebagian data masih kerangka.

Rekomendasi:

- Prioritaskan bulan berjalan 2026 untuk tampilan HTML publik.
- Gunakan agregasi 20 tahun hanya untuk grafik perbandingan, bukan untuk menampilkan data mentah penuh di HTML.
- Masukkan data historis bertahap per modul.
- Jangan tampilkan angka final tanpa sumber.

### 2. HTML Sudah Terlalu Padat

`dashboard/index.html` menyimpan UI, CSS, data seed, patch runtime, AI, DB-Link, dan renderer dalam satu file besar.

Rekomendasi fase berikut:

- Pecah ke `src/modules/*`.
- Gunakan Vite atau framework ringan.
- Pindahkan data seed ke JSON/CSV.
- Jadikan dashboard hanya renderer, bukan gudang logika.

### 3. AI Harus Selalu Transparan

AI tidak boleh memberi kesan memvonis. AI harus menyatakan apakah data adalah:

- Draft.
- Temuan audit.
- Dugaan.
- Dakwaan.
- Putusan.
- Inkracht.

Rekomendasi:

- Tambah halaman `transparansi-algoritma`.
- Simpan prompt, model, input, output, confidence, dan disclaimer seperti konsep Nemesis.
- Buat log `ai_enrichment_log.csv` untuk setiap enrichment otomatis.

### 4. Evidence Wajib Jadi Syarat Data Sensitif

Data korupsi, BO, vendor, pejabat, dan aliran uang harus punya sumber.

Rekomendasi:

- Setiap CSV sensitif wajib punya kolom `sumber`, `status_verifikasi`, `tanggal_sumber`, `catatan_hukum`.
- Data tanpa sumber tetap boleh masuk, tetapi statusnya `DRAFT_UNVERIFIED`.

### 5. SQLite Masih Arsip Pendamping

SQLite `Gudang_DB4.db` berisi banyak tabel tetapi mayoritas kosong. CSV DB3 saat ini lebih kuat sebagai sumber struktur.

Rekomendasi:

- Pertahankan CSV sebagai source of truth publik.
- Gunakan SQLite hanya untuk indexing/search lokal.
- Nanti buat pipeline CSV -> SQLite -> dashboard_summary.json.

## Roadmap Prioritas

### Phase 1: Data Hygiene

- Isi `master_koruptor.csv`, `master_aktor.csv`, `master_vendor.csv`, `master_beneficial_owner.csv`, dan `master_evidence.csv`.
- Tambah kolom status verifikasi di CSV sensitif.
- Tetapkan format sumber resmi.

### Phase 2: Agregasi

- Buat script `build_dashboard_summary.py`.
- Hitung total kerugian, recovery, jumlah kasus, jumlah aktor, dan evidence coverage dari CSV.
- Output ke `dashboard/dashboard_summary.json`.

### Phase 3: Search dan Track

- Gunakan `gudang-db/index.html` sebagai katalog awal.
- Tambah pencarian lintas CSV untuk nama aktor, vendor, kasus, tahun, instansi.
- Buat mode "track tahun" dari dashboard langsung ke CSV terkait.

### Phase 4: Modularisasi

- Migrasi HTML jumbo ke Vite.
- Pisahkan modul: dashboard, parpol, korupsi, vendor, BO, audit, akuntansi, AI, DB-Link.
- Simpan konfigurasi di file terpisah.

### Phase 5: Transparansi AI

- Buat halaman transparansi algoritma.
- Simpan prompt, model, dan disclaimer.
- Pastikan AI hanya memberi indikator awal, bukan vonis.

## Prinsip Publikasi

Project ini akan kuat jika disiplin di tiga hal:

- Data punya sumber.
- AI punya disclaimer dan log.
- Dashboard tidak mengarang angka.

Dengan itu, Monitoring Rakyat bisa menjadi repositori pengawasan publik yang serius, bukan sekadar tampilan data.
