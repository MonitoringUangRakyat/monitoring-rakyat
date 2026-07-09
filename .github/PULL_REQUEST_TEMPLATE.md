## Ringkasan

Jelaskan perubahan yang dibuat.

## Jenis Perubahan

- [ ] Data CSV
- [ ] Dashboard/UI
- [ ] Script/validasi
- [ ] Dokumentasi
- [ ] Koreksi data

## Sumber Data

Sertakan link sumber resmi/publik untuk data faktual.

## Status Verifikasi

- [ ] DRAFT_PUBLIC_SUBMISSION
- [ ] DRAFT_UNVERIFIED
- [ ] DRAFT_REVIEW
- [ ] AI_CLASSIFIED_NEEDS_VERIFICATION
- [ ] NEEDS_MORE_EVIDENCE
- [ ] REJECTED_NO_SOURCE
- [ ] VERIFIED_SOURCE
- [ ] RILL_CURRENT_PERIOD
- [ ] TEMUAN_AUDIT
- [ ] DUGAAN
- [ ] DAKWAAN
- [ ] PUTUSAN
- [ ] INKRACHT
- [ ] DIKOREKSI
- [ ] Tidak relevan

## Checklist

- [ ] Tidak ada token/API key/file rahasia.
- [ ] Tidak ada data pribadi yang tidak relevan.
- [ ] CSV tetap UTF-8 dan memakai header yang benar.
- [ ] `python scripts/validate_gudang_db.py` lolos.
- [ ] `python scripts/generate_ai_index.py` sudah dijalankan jika menambah/menghapus CSV.
- [ ] `python scripts/build_dashboard_summary.py` sudah dijalankan jika data angka berubah.
- [ ] `python scripts/pre_github_readiness.py --write` sudah dijalankan jika data periode berjalan berubah.
- [ ] Masukan publik sudah dicek duplikasi, periode, nominal, dan sumber/evidence.
- [ ] Klaim sensitif punya satu sumber resmi atau dua sumber independen kredibel.

## Catatan Risiko

Tuliskan risiko, asumsi, atau bagian yang masih perlu review.
