# Anonymous Publication Guide

Panduan ini membantu publikasi repo tanpa menanam identitas pribadi di kode.

## Prinsip

- Kode tidak perlu tahu siapa pemilik akun GitHub.
- Link Gudang DB default memakai path lokal `../gudang-db`.
- URL GitHub final bisa disetel setelah repo publik lewat panel `AI Settings -> Gudang DB Repository`.
- Jangan commit token, cookie, private key, atau file `.env`.

## Sebelum Upload

1. Jalankan release check:

   ```bash
   python scripts/release_check.py
   ```

2. Pastikan tidak ada:

   - Placeholder akun/repo GitHub yang belum diganti.
   - Token Telegram/API.
   - Path lokal pribadi.
   - Log runtime.
   - Dokumen mentah dengan metadata pribadi.

3. Pastikan `dashboard/active-period.json` sudah benar.

## Setelah Repo Ada

Jika repo sudah publik, pengelola dapat mengatur link raw Gudang DB dari dashboard:

```text
AI Settings -> Gudang DB Repository
```

Contoh format:

```text
https://raw.githubusercontent.com/ORG_OR_ACCOUNT/REPO/main/gudang-db
```

Untuk GitHub Pages, katalog Gudang DB tetap bisa dibuka lewat:

```text
gudang-db/index.html
```

## Catatan

Gunakan identitas publikasi yang sah dan aman. Hindari memasukkan data pribadi yang tidak perlu. Fokus repo ini adalah transparansi data publik, bukan membocorkan rahasia pribadi.
