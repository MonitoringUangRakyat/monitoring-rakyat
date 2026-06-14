# Security Policy

Monitoring Rakyat menangani data publik yang sensitif secara sosial dan politik. Keamanan repo ini berarti menjaga integritas data, keselamatan kontributor, dan mencegah penyalahgunaan informasi.

## Jangan Commit

- Token API, Telegram token, cookie, password, private key.
- Data pribadi yang tidak relevan dengan pengawasan uang publik.
- File ekspor lokal berisi identitas kontributor.
- Metadata dokumen yang memuat nama pribadi, lokasi, atau perangkat kerja.

## Pelaporan Kerentanan

Jika menemukan celah keamanan, jangan membuka issue publik yang berisi exploit detail. Laporkan melalui kanal privat pengelola repo setelah kanal tersebut ditentukan.

Jika kanal privat belum tersedia, buat issue singkat tanpa detail eksploit:

```text
Security issue found. Maintainer contact needed.
```

## Prinsip Data Sensitif

- Klaim hukum harus punya sumber.
- AI hanya memberi indikator awal, bukan vonis.
- Beneficial owner, vendor, pejabat, dan kasus korupsi harus diberi status verifikasi.
- Koreksi berbasis bukti harus diterima.

## Publikasi Anonim

Repo ini tidak membutuhkan identitas pribadi di kode. Sebelum publikasi:

- Pakai akun publikasi yang terpisah dari akun pribadi.
- Jangan commit path lokal, nama komputer, token, atau dokumen mentah yang punya metadata pribadi.
- Jalankan validator dan checklist release.
- Pastikan link Gudang DB memakai URL organisasi/repo publik, bukan URL personal yang belum siap.
