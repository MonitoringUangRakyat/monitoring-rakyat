# Pre-GitHub Readiness Report

Generated: 2026-06-27T05:47:32+07:00 Asia/Jakarta
Status: **NEEDS_WORK**

## Active Period Gate

- Dashboard active period: Juni 2026
- Current Asia/Jakarta: 6 / 2026
- Current period rows: 0
- Current period rill rows with source + nominal: 0
- AI Agent search tasks: 240
- Historical backfill hardcode: last 15 years, minimum 10 years

## Blockers

- belum ada baris data riil bersumber untuk tahun/bulan berjalan
- hardcode backfill 10 tahun historis belum lengkap untuk modul inti

## Historical Backfill Mandate

- Tim AI Pengumpul DB wajib mengisi data 10-15 tahun ke belakang karena data historis lebih matang, lebih banyak putusan/audit, dan lebih mudah diverifikasi.
- Tahun berjalan tetap boleh on-process dan masuk belakangan sebagai current-period draft.
- HTML publik tetap hanya menampilkan tahun/bulan berjalan; klik tahun/bulan lama harus diarahkan ke Gudang DB.
- Target backfill: [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
- Minimum wajib: [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
- Modul yang belum memenuhi minimum: akuntansi, audit, audittrail, bea_cukai, bumn, korupsi, pajak, parpol, prog_daerah, prog_eksekutif, prog_legislatif, redflag, risknas, sda, vendor

## Core Sector Coverage

| Modul | Tahun | Rows | Source | Nominal | Active Rows | Active Rill | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| akuntansi | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| audit | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| audittrail | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| bea_cukai | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| bumn | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| korupsi | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| pajak | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| parpol | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| prog_daerah | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| prog_eksekutif | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| prog_legislatif | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| redflag | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| risknas | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| sda | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |
| vendor | 61/61 | 0 | 0 | 0 | 0 | 0 | OK / NEEDS_DATA |

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
