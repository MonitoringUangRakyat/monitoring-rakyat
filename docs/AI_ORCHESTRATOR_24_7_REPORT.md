# AI Pengawas Orchestrator 24/7 Report

Generated: 2026-06-22T09:29:33+07:00 Asia/Jakarta

## Scope

- Misi: setiap aliran APBN/APBD, sampai Rp 1, harus bisa ditelusuri ke program, instansi, vendor, bukti, dan status verifikasi.
- Output otomatis masuk draft queue, bukan data final.
- Data final tetap harus lolos policy guard, evidence, dan review.
- Hardcode: Tim AI Pengumpul DB wajib mencari 10-15 tahun data historis; tahun berjalan boleh on-process.
- Koordinator harian: AI Koordinator Alur Harian mengatur urutan build, validasi, patrol, dan sinkron dashboard.

## Status

- Total candidates: 3
- New candidates this run: 0
- High confidence candidates: 0
- Historical backfill tasks: 225
- Historical backfill candidates: 0

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
  - pre_github_readiness.py --write
  - build_source_patrol.py
  - ai_pengawas_orchestrator.py

## Module Coverage

- korupsi: 2
- prog_legislatif: 1

## Safety Guard

- auto_publish_final_data: False
- write_public_claims_directly: False
- token_in_html: False
- required_before_rill: sumber resmi atau dua sumber independen, nominal/periode jelas, dan review manusia/AI policy guard
