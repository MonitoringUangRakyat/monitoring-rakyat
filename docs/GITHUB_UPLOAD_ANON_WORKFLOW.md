# GitHub Upload Anon Workflow

Panduan ini untuk menyiapkan publikasi repo tanpa membawa jejak lokal/pribadi.

## Identitas Publik

- Buat akun GitHub baru khusus project.
- Gunakan email baru yang tidak terkait akun pribadi, nomor pribadi, foto pribadi, username lama, atau recovery email yang mudah ditebak.
- Aktifkan 2FA/passkey.
- Jangan isi profil dengan lokasi, nama asli, nomor kontak pribadi, atau tautan akun utama.

Catatan email:

- `monitoring_rakyat@gmail.com` belum tentu bisa dipakai karena Gmail umumnya tidak memakai underscore pada username.
- Alternatif yang lebih rapi: `monitoring.rakyat.id@gmail.com`, `monitoring.uang.rakyat@gmail.com`, atau email privacy-first seperti Proton.

## Folder Yang Di-upload

Upload dari folder release bersih:

```text
PUBLIC_RELEASE_MONITORING_RAKYAT/
```

Jangan upload dari folder kerja yang berisi arsip lokal, ZIP, DB pribadi, screenshot, terminal log, folder kerja privat Codex/agent, atau cache.

## Validasi Sebelum Commit

Jalankan dari folder release:

```bash
python scripts/release_check.py
python scripts/anonymity_scan.py
```

Keduanya harus lolos sebelum `git init`.

Jika ingin menambah marker nama/username pribadi untuk scan lokal, set environment variable `ANON_MARKERS` sebelum menjalankan scanner. Jangan commit marker pribadi itu ke repo.

## Commit Awal

```bash
git init
git add .
git commit -m "Initial public release"
git branch -M main
git remote add origin https://github.com/ACCOUNT/monitoring-rakyat.git
git push -u origin main
```

Ganti `ACCOUNT` dengan akun publik baru.

## GitHub Pages

Jika repo sudah publik:

1. Buka `Settings -> Pages`.
2. Source: `Deploy from a branch`.
3. Branch: `main`.
4. Folder: `/root`.
5. Dashboard dibuka dari:

```text
https://ACCOUNT.github.io/monitoring-rakyat/dashboard/
```

## Aturan Kontribusi Data

- Semua input rakyat masuk `DRAFT_REVIEW` terlebih dulu.
- Data sensitif wajib minimal punya sumber primer/resmi atau minimal dua sumber media kredibel.
- Jangan menaikkan status menjadi final tanpa evidence.
- Jangan memuat data pribadi yang tidak relevan dengan penggunaan uang publik.
