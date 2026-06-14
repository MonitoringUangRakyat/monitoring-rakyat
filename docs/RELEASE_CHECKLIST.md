# Release Checklist

Gunakan checklist ini sebelum repo dipublikasikan ke GitHub.

## 1. Identitas dan Metadata

- Tidak ada token/API key di repo.
- Tidak ada file `.env`.
- Tidak ada log lokal.
- Tidak ada path lokal personal di dokumen publik.
- Akun publikasi sudah dipilih dan tidak wajib memakai identitas pribadi.

## 2. Struktur Data

- `gudang-db/_index/ai_index.json` sudah digenerate ulang.
- `scripts/validate_gudang_db.py` lolos tanpa error.
- `scripts/pre_github_readiness.py --write` sudah dijalankan.
- `docs/PRE_GITHUB_READINESS_REPORT.md` dibaca sebelum upload.
- CSV sensitif punya kolom sumber/status verifikasi.
- Data draft diberi status `DRAFT_UNVERIFIED`.

## 3. Dashboard

- `dashboard/active-period.json` sesuai periode publik.
- Dashboard hanya menampilkan tahun/bulan berjalan.
- Grafik dashboard memakai kerangka 20 tahun terakhir; tahun tanpa DB tampil kosong/0.
- Track historis membuka `gudang-db/index.html` atau URL repo final.

## 4. Dokumen Publik

- `README.md` jelas.
- `CONTRIBUTING.md` ada.
- `DATA_GOVERNANCE.md` ada.
- `SECURITY.md` ada.
- `LICENSE` ada.

## 5. Perintah Validasi

```bash
python scripts/generate_ai_index.py
python scripts/validate_gudang_db.py
python scripts/validate_immutable_db.py
python scripts/build_dashboard_summary.py
python scripts/pre_github_readiness.py --write
python scripts/release_check.py
```

Semua harus selesai tanpa error fatal sebelum publikasi.
Jika `Pre-GitHub readiness` masih `NEEDS_WORK`, repo boleh dipreview secara lokal tetapi jangan diklaim sebagai data riil lengkap.

## 6. Setelah Upload

- Buka GitHub Pages atau preview dashboard.
- Cek tombol Track Gudang DB.
- Cek katalog Gudang DB.
- Cek minimal satu CSV era modern, reformasi, dan orba.
- Buat issue pertama berisi roadmap data prioritas.

## 7. Anon Publishing Gate

- Upload dari akun GitHub/email publik terpisah, bukan akun pribadi.
- Jangan push dari folder kerja yang berisi ZIP, DB arsip, screenshot, cache, folder privat Codex/agent, atau log terminal.
- Buat folder release bersih, lalu `git init` dari nol di folder itu.
- Jalankan scan identitas/secret sebelum commit:

  ```bash
  python scripts/anonymity_scan.py
  python scripts/release_check.py
  ```

- Jangan klaim data final jika status masih `DRAFT_REVIEW`, `DRAFT_UNVERIFIED`, atau belum punya evidence primer.
