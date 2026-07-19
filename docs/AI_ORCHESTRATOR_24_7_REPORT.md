# AI Pengawas Orchestrator 24/7 Report

Generated: 2026-07-20T06:12:24+07:00 Asia/Jakarta

## Scope

- Misi: setiap aliran APBN/APBD, sampai Rp 1, harus bisa ditelusuri ke program, instansi, vendor, bukti, dan status verifikasi.
- Output otomatis masuk draft queue, bukan data final.
- Data final tetap harus lolos policy guard, evidence, dan review.
- Hardcode: Tim AI Pengumpul DB wajib mencari 10-15 tahun data historis; tahun berjalan boleh on-process.
- Hardcode: semua tool/sumber yang tersedia wajib dimanfaatkan mandiri 24/7; tidak boleh berhenti di queue tanpa promosi draft.
- Upload DB Rakyat: link, Excel, Word, PDF, catatan/noted, CSV, dan teks diterima sebagai DRAFT_PUBLIC_SUBMISSION.
- Validitas awal >= 50 wajib masuk audit queue Gudang DB sesegera mungkin; < 40 wajib audit ketat dan fake dikick.
- Koordinator harian: AI Koordinator Alur Harian mengatur urutan build, validasi, patrol, dan sinkron dashboard.

## Status

- Total candidates: 128
- New candidates this run: 0
- High confidence candidates: 4
- Historical backfill tasks: 212
- Historical backfill candidates: 40
- Public submissions pending audit: 0
- Autonomous mode: FULL_MANDIRI_PROAKTIF_24_7
- Artificial source limit: False

## Daily Flow Controller

- ID: AI_KOORDINATOR_ALUR_HARIAN
- Mission: Mengatur urutan kerja harian agar Gudang DB, dashboard, patrol, dan draft queue selalu sinkron tanpa perlu diingatkan manual.
- Hardcoded tasks:
  - generate_ai_index.py
  - validate_gudang_db.py
  - validate_immutable_db.py
  - build_dashboard_summary.py
  - build_fiscal_ratio_summary.py
  - import_nemesis_procurement.py
  - import_public_submissions.py
  - pre_github_readiness.py --write
  - build_source_patrol.py
  - ai_pengawas_orchestrator.py
  - promote_ai_hunter_candidates.py

## Autonomous Tool Mandate

- Mode: FULL_MANDIRI_PROAKTIF_24_7
- Rule: Semua tool/sumber yang tersedia wajib dimanfaatkan untuk memperlengkap Gudang DB tanpa menunggu instruksi manual.
- Tools/sources wajib dipakai:
  - RSS/feed publik yang aktif
  - GitHub public submissions
  - Nemesis intake jika data tersedia
  - Gudang DB index/validator
  - source patrol
  - AI hunter promotion
  - dashboard/fiscal/dashboard summary sync

## Upload DB Rakyat Policy

- Entry status: DRAFT_PUBLIC_SUBMISSION
- Accepted inputs: link_sumber, excel, word, pdf, catatan_noted, csv, teks_biasa
- Minimum queue score: 50%
- Reject/audit ketat below: 40%
- Page update rule: Data yang lolos audit minimal wajib memicu sinkronisasi Gudang DB dan tampil di halaman/menu terkait secepat workflow validasi memungkinkan.
- Public queue: gudang-db/_queue/public_submissions.json (0 pending)

## Module Coverage

- akuntansi: 9
- audit: 6
- audittrail: 6
- bea_cukai: 8
- bumn: 6
- korupsi: 15
- pajak: 11
- parpol: 6
- prog_daerah: 9
- prog_eksekutif: 6
- prog_legislatif: 20
- redflag: 6
- risknas: 6
- sda: 6
- vendor: 8

## Safety Guard

- auto_publish_final_data: False
- write_public_claims_directly: False
- token_in_html: False
- required_before_rill: sumber resmi atau dua sumber independen, nominal/periode jelas, dan review manusia/AI policy guard
- hunter_autonomy: AI Hunter boleh mencari, membuat draft, dedupe, dan mapping otomatis 24/7; guard hanya mencegah klaim final palsu.
