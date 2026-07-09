# Monitoring Rakyat

[![Buka Dashboard Publik](https://img.shields.io/badge/BUKA_DASHBOARD_PUBLIK-monitoringuangrakyat.github.io-f59e0b?style=for-the-badge)](https://monitoringuangrakyat.github.io/monitoring-rakyat/dashboard/)

## Buka Dashboard Publik

Klik link utama ini untuk membuka tampilan HTML dashboard:

[https://monitoringuangrakyat.github.io/monitoring-rakyat/dashboard/](https://monitoringuangrakyat.github.io/monitoring-rakyat/dashboard/)

> Catatan: file `dashboard/index.html` di GitHub akan tampil sebagai source code. Untuk melihat dashboard berjalan, gunakan link GitHub Pages di atas.

Repositori audit fiskal dan forensik publik untuk membantu rakyat Indonesia memantau aliran uang negara secara terbuka, terstruktur, dan bisa diverifikasi.

Tujuan utama proyek ini adalah transparansi: dashboard tetap ringan untuk dibuka publik, sementara data mentah lintas era disimpan sebagai CSV di Gudang DB agar bisa diperiksa ulang oleh jurnalis, peneliti, aktivis data, programmer, dan warga.

## Arsitektur

```text
monitoring-rakyat/
|-- README.md
|-- LICENSE
|-- dashboard/
|   |-- index.html
|   |-- app.js
|   |-- dashboard_summary.json
|   `-- INTEGRASI.md
`-- gudang-db/
    |-- _index/
    |   `-- ai_index.json
    |-- master/
    |   |-- master_koruptor.csv
    |   |-- master_aktor.csv
    |   |-- master_vendor.csv
    |   |-- master_beneficial_owner.csv
    |   `-- master_evidence.csv
    |-- 1_era_orba_1966_1998/
    |-- 2_era_reformasi_1999_2010/
    `-- 3_era_modern_2011_2026/
```

## Cara Kerja

Dashboard membaca `dashboard/dashboard_summary.json` saja. File ini berisi angka ringkas seperti tahun aktif, total kerugian, recovery, jumlah kasus, dan histori akumulasi. Ini membuat HTML tetap ringan.

Gudang DB menjadi source of truth. Semua data mentah disimpan sebagai CSV per modul dan tahun, misalnya `korupsi_2026.csv`, `bea_cukai_2024.csv`, atau `bumn_2011.csv`.

AI Pengawas membaca `gudang-db/_index/ai_index.json` untuk mengetahui modul apa yang tersedia, tahun apa yang punya file, dan CSV mana yang harus dibuka.

## Prinsip Periode Publik

Dashboard publik hanya menampilkan data tahun dan bulan berjalan. Untuk rilis awal ini, scope publik dikunci ke Juni 2026. Grafik dashboard memakai kerangka agregasi 20 tahun terakhir agar rakyat bisa melihat rasio perbandingan; tahun yang belum punya sumber DB ditampilkan sebagai kosong/0 dan otomatis terisi saat Gudang DB dilengkapi.

Data di luar tahun/bulan berjalan harus diakses melalui Gudang DB:

```text
gudang-db/index.html
gudang-db/{era}/{modul}_{tahun}.csv
```

## Status Data

Paket awal ini sudah menyiapkan struktur nasional 1966-2026 dengan ribuan file CSV kerangka kerja. Banyak file masih berupa template/header dan harus diisi bertahap dengan data terverifikasi.

Angka di `dashboard_summary.json` masih ditandai sebagai placeholder sampai proses agregasi dari CSV yang sudah terisi dilakukan.

## Master Data

File induk lintas era berada di `gudang-db/master/`:

- `master_koruptor.csv`: daftar perkara/terpidana/entitas terkait kasus korupsi berdasarkan sumber resmi.
- `master_aktor.csv`: aktor publik dan relasinya.
- `master_vendor.csv`: vendor, kontraktor, dan relasi pengadaan.
- `master_beneficial_owner.csv`: pemilik manfaat dan jaringan korporasi.
- `master_evidence.csv`: katalog bukti, dokumen, putusan, laporan, dan tautan sumber.

Setiap entri sensitif wajib punya sumber, status verifikasi, dan konteks hukum yang jelas.

## Sumber Data yang Disarankan

Gunakan sumber publik dan dapat diverifikasi, antara lain:

- APBN/APBD dan dokumen Kementerian Keuangan/Kemendagri.
- LHKPN KPK.
- Direktori Putusan Mahkamah Agung.
- Laporan Hasil Pemeriksaan BPK.
- Data pengadaan LKPP, SIRUP, LPSE.
- AHU Kemenkumham untuk data badan hukum dan beneficial owner.
- Rilis resmi KPK, Kejaksaan, pengadilan, kementerian/lembaga, dan pemerintah daerah.

Data tanpa sumber sebaiknya masuk sebagai draft, bukan data final.

## Cara Berkontribusi

1. Fork repositori ini.
2. Pilih era dan modul yang ingin diperbaiki di `gudang-db/`.
3. Isi CSV dengan format UTF-8, tanpa rumus Excel, dan pertahankan header.
4. Cantumkan sumber di kolom sumber/link/dokumen yang tersedia.
5. Jalankan validasi struktur sebelum pull request.
6. Kirim pull request dengan penjelasan sumber dan perubahan data.

Programmer dapat membantu memperbaiki dashboard, generator indeks, validasi CSV, dan visualisasi ringkasan.

Panduan lengkap:

- `CONTRIBUTING.md`
- `DATA_GOVERNANCE.md`
- `docs/AUDIT_PROJECT.md`
- `docs/ANON_PUBLICATION_GUIDE.md`
- `docs/GITHUB_UPLOAD_ANON_WORKFLOW.md`
- `docs/DB_IMMUTABILITY_POLICY.md`
- `docs/AI_MODE_POLICY.md`
- `docs/RELEASE_CHECKLIST.md`

## Prinsip Verifikasi

- Jangan memasukkan tuduhan tanpa dasar dokumen publik.
- Pisahkan status: dugaan, temuan audit, penyidikan, dakwaan, putusan, inkracht, pemulihan aset.
- Jangan mencampur opini dengan data.
- Simpan tautan sumber asli jika tersedia.
- Koreksi data harus diterima jika ada bukti yang lebih kuat.

## Lisensi

Kode dan struktur data menggunakan MIT License. Lihat `LICENSE`.

## Disclaimer

Repositori ini dibuat untuk edukasi, transparansi, dan pengawasan partisipatif. Data harus disusun dari sumber publik yang dapat diverifikasi. Pengelola dan kontributor wajib menghindari fitnah, doxing, penyebaran data pribadi yang tidak relevan, dan klaim hukum yang belum terbukti.
