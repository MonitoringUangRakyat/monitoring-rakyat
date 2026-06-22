# AI Pengawas Orchestrator

AI Pengawas Orchestrator adalah pola kerja 24/7 untuk membuat Monitoring Rakyat proaktif mencari kandidat DB uang rakyat dari sumber publik/resmi.

Tujuan utamanya sederhana: setiap aliran APBN/APBD, sampai Rp 1, harus bisa ditelusuri ke program, instansi, vendor, bukti, status verifikasi, dan dampaknya ke cashflow negara.

Hardcode utama: Tim AI Pengumpul DB wajib mencari dan mengisi data historis 10-15 tahun ke belakang. Data historis diprioritaskan karena sumbernya lebih matang, putusan/audit lebih banyak, dan validasi lebih stabil. Tahun/bulan berjalan boleh on-process dan masuk belakangan.

## Prinsip

- Orchestrator adalah router, policy guard, source patrol, dan draft queue builder.
- Output otomatis masuk queue, bukan langsung menjadi data final.
- HTML publik tidak boleh menyimpan token GitHub, API key, cookie, atau secret.
- Data sensitif tidak boleh menjadi klaim final tanpa sumber resmi atau dua sumber independen kredibel.
- Jika sumber/API/feed gagal, sistem melaporkan apa adanya dan tidak membuat data palsu.
- HTML publik hanya menampilkan tahun/bulan berjalan; bulan/tahun lama dibuka melalui Gudang DB agar halaman tetap ringan.

## Alur 24/7

```text
GitHub Actions schedule
-> generate_ai_index.py
-> validate_gudang_db.py
-> build_dashboard_summary.py
-> build_fiscal_ratio_summary.py
-> pre_github_readiness.py --write
-> build_source_patrol.py
-> ai_pengawas_orchestrator.py
-> commit dashboard status + draft queue
-> GitHub Pages menampilkan status patroli
```

Saat ada data baru di Gudang DB atau draft queue, workflow wajib memperbarui:

- `gudang-db/_index/ai_index.json`
- `dashboard/dashboard_summary.json`
- `dashboard/fiscal_ratio_annual.json`
- `dashboard/pre_github_readiness.json`
- `dashboard/ai_agent_tasks.json`
- `dashboard/ai_agent_source_patrol.json`
- `dashboard/ai_orchestrator_status.json`
- laporan readiness dan orchestrator di `docs/`

## Output

- `dashboard/ai_agent_tasks.json`: modul yang butuh pencarian.
- `dashboard/ai_agent_source_patrol.json`: daftar query/source patrol.
- `dashboard/ai_orchestrator_status.json`: ringkasan publik status orkestrator.
- `dashboard/fiscal_ratio_annual.json`: agregasi tahunan Belanja APBN vs Pajak vs SDA untuk grafik dashboard.
- `gudang-db/_queue/ai_pengawas_candidates.json`: kandidat DB hasil patrol.
- `gudang-db/_queue/ai_pengawas_candidates.csv`: versi CSV untuk review.
- `docs/AI_ORCHESTRATOR_24_7_REPORT.md`: laporan run terakhir.

## Status Data

- `AI_CLASSIFIED_NEEDS_VERIFICATION`: kandidat awal, perlu bukti tambahan.
- `DRAFT_REVIEW`: kandidat layak review, belum final.
- `VERIFIED_SOURCE_CANDIDATE`: berasal dari kategori resmi dan confidence tinggi, tetap perlu review sebelum masuk data rill.
- `HISTORICAL_BACKFILL_REQUIRED`: tugas wajib untuk mengisi Gudang DB 10-15 tahun ke belakang.

## Integrasi Ke Menu

Dashboard membaca `dashboard/ai_orchestrator_status.json` melalui `dashboard/app.js`.

Grafik `Perbandingan Tahun ke Tahun: Belanja APBN vs Pendapatan Pajak vs Hasil SDA` membaca `dashboard/fiscal_ratio_annual.json`. Grafik ini wajib tetap menampilkan minimum 10 tahun karena hanya agregasi tahunan, bukan detail bulanan/harian. Jika Gudang DB belum punya nilai tahun tertentu, tahun itu tetap tampil sebagai `Kosong` dan otomatis terisi saat CSV Gudang DB diperbarui lalu workflow berjalan.

Menu dan fitur lain tetap memakai Gudang DB sebagai source of truth. Kandidat dari `_queue` baru boleh dipindahkan ke CSV sektor setelah:

- duplikasi dicek;
- tahun/bulan/periode jelas;
- nominal/cashflow jelas;
- sumber resmi atau dua sumber independen tersedia;
- status verifikasi sesuai kebijakan;
- review lolos.

## Batas Aman

Orchestrator tidak boleh:

- memvonis orang atau lembaga;
- memindahkan kandidat menjadi `RILL_CURRENT_PERIOD` tanpa review;
- menghapus data valid;
- menulis token ke HTML atau repo;
- membuat angka atau sumber palsu;
- memakai satu media/agregator sebagai bukti final.

## AI Koordinator Alur Harian

Satu role hardcode mengatur urutan kerja sistem setiap hari: `AI_KOORDINATOR_ALUR_HARIAN`.

Tugas permanen:

- regenerate index Gudang DB;
- validasi Gudang DB dan immutable ledger;
- build `dashboard_summary.json`;
- build `fiscal_ratio_annual.json`;
- build readiness dan task backfill historis;
- build source patrol;
- jalankan AI Pengawas Orchestrator;
- pastikan semua output dashboard/queue sinkron sebelum commit otomatis.
