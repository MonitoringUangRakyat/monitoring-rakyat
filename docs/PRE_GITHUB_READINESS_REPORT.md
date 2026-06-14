# Pre-GitHub Readiness Report

Generated: 2026-06-14T09:16:08+07:00 Asia/Jakarta
Status: **NEEDS_WORK**

## Active Period Gate

- Dashboard active period: Juni 2026
- Current Asia/Jakarta: 6 / 2026
- Current period rows: 0
- Current period rill rows with source + nominal: 0
- AI Agent search tasks: 15

## Blockers

- belum ada baris data riil bersumber untuk tahun/bulan berjalan

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
- Website seperti Nemesis dapat dipakai sebagai acuan awal untuk pengadaan/redflag, tetapi harus diberi status review dan diverifikasi ke LKPP/SiRUP/BPK/KPK/Kejaksaan/putusan.

## Catatan

- `OK / NEEDS_DATA` berarti file sektor dan tahun tersedia, tetapi isinya masih header/template.
- `active_rill_rows` hanya menghitung baris tahun/bulan berjalan yang punya sumber/evidence dan nominal.
- Jika current period kosong, HTML wajib menampilkan nol/ringkasan kosong dan mengarahkan detail ke Gudang DB.
- Tim AI Agent harus mengisi queue draft dengan sumber resmi sebelum data naik menjadi data publik.
