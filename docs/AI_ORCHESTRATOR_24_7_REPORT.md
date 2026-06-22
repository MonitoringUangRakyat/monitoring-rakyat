# AI Pengawas Orchestrator 24/7 Report

Generated: 2026-06-22T08:56:30+07:00 Asia/Jakarta

## Scope

- Misi: setiap aliran APBN/APBD, sampai Rp 1, harus bisa ditelusuri ke program, instansi, vendor, bukti, dan status verifikasi.
- Output otomatis masuk draft queue, bukan data final.
- Data final tetap harus lolos policy guard, evidence, dan review.
- Hardcode: Tim AI Pengumpul DB wajib mencari 10-15 tahun data historis; tahun berjalan boleh on-process.

## Status

- Total candidates: 3
- New candidates this run: 0
- High confidence candidates: 0
- Historical backfill tasks: 225
- Historical backfill candidates: 0

## Module Coverage

- korupsi: 2
- prog_legislatif: 1

## Safety Guard

- auto_publish_final_data: False
- write_public_claims_directly: False
- token_in_html: False
- required_before_rill: sumber resmi atau dua sumber independen, nominal/periode jelas, dan review manusia/AI policy guard
