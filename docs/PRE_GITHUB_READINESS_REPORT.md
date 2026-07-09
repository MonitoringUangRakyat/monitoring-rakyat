# Pre-GitHub Readiness Report

Generated: 2026-07-10T01:15:13+07:00 Asia/Jakarta
Status: **NEEDS_WORK**

## Active Period Gate

- Dashboard active period: Juni 2026
- Current Asia/Jakarta: 7 / 2026
- Current period rows: 249
- Current period rill rows with source + nominal: 4
- AI Agent search tasks: 225
- Historical backfill hardcode: last 15 years, minimum 10 years

## Blockers

- dashboard/active-period.json tidak sama dengan tanggal Asia/Jakarta saat ini
- hardcode backfill 10 tahun historis belum lengkap untuk modul inti

## Historical Backfill Mandate

- Tim AI Pengumpul DB wajib mengisi data 10-15 tahun ke belakang karena data historis lebih matang, lebih banyak putusan/audit, dan lebih mudah diverifikasi.
- Tahun berjalan tetap boleh on-process dan masuk belakangan sebagai current-period draft.
- HTML publik tetap hanya menampilkan tahun/bulan berjalan; klik tahun/bulan lama harus diarahkan ke Gudang DB.
- Target backfill: [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
- Minimum wajib: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
- Modul yang belum memenuhi minimum: audit, audittrail, bea_cukai, bumn, korupsi, pajak, parpol, prog_daerah, prog_eksekutif, prog_legislatif, redflag, risknas, sda, vendor

## Core Sector Coverage

| Modul | Tahun | Rows | Source | Nominal | Active Rows | Active Rill | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| akuntansi | 61/61 | 11 | 11 | 11 | 0 | 0 | OK / HAS_EVIDENCE |
| audit | 61/61 | 6 | 0 | 0 | 4 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| audittrail | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| bea_cukai | 61/61 | 8 | 8 | 1 | 4 | 1 | OK / HAS_EVIDENCE |
| bumn | 61/61 | 6 | 0 | 0 | 4 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| korupsi | 61/61 | 15 | 15 | 9 | 5 | 3 | OK / HAS_EVIDENCE |
| pajak | 61/61 | 22 | 0 | 12 | 9 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| parpol | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| prog_daerah | 61/61 | 9 | 0 | 0 | 7 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| prog_eksekutif | 61/61 | 6 | 0 | 0 | 4 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| prog_legislatif | 61/61 | 20 | 0 | 0 | 18 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| redflag | 61/61 | 6 | 0 | 0 | 4 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| risknas | 61/61 | 6 | 0 | 0 | 4 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| sda | 61/61 | 17 | 0 | 12 | 4 | 0 | OK / HAS_ROWS_NO_EVIDENCE |
| vendor | 61/61 | 8 | 0 | 0 | 6 | 0 | OK / HAS_ROWS_NO_EVIDENCE |

## Fallback & AI Agent

- Jika periode berjalan kosong, dashboard boleh menampilkan fallback historis/master dengan label jelas.
- Fallback tidak boleh dianggap data riil tahun/bulan berjalan.
- Daftar tugas pencarian otomatis ditulis ke `dashboard/ai_agent_tasks.json`.
- `HISTORICAL_BACKFILL_REQUIRED` adalah tugas wajib, bukan opsional.
- Website seperti Nemesis dapat dipakai sebagai acuan awal untuk pengadaan/redflag, tetapi harus diberi status review dan diverifikasi ke LKPP/SiRUP/BPK/KPK/Kejaksaan/putusan.

## Catatan

- `OK / NEEDS_DATA` berarti file sektor dan tahun tersedia, tetapi isinya masih header/template.
- `active_rill_rows` hanya menghitung baris tahun/bulan berjalan yang punya sumber/evidence dan nominal.
- Jika current period kosong, HTML wajib menampilkan nol/ringkasan kosong dan mengarahkan detail ke Gudang DB.
- Tim AI Agent harus mengisi queue draft dengan sumber resmi sebelum data naik menjadi data publik.
