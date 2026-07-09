# Contributing to Monitoring Rakyat

Terima kasih sudah ingin membantu. Repositori ini dibuat untuk transparansi uang rakyat, jadi kontribusi harus rapi, dapat diverifikasi, dan tidak mencampur opini dengan data.

## Jenis Kontribusi

- Upload data rakyat dalam format mudah: link, Excel, Word, PDF, catatan/noted, CSV, atau teks biasa.
- Mengisi CSV Gudang DB dari sumber publik resmi.
- Memperbaiki dashboard, validasi, dan script agregasi.
- Menambah dokumentasi sumber data.
- Melaporkan data yang salah atau belum lengkap.

## Upload Data Base Rakyat

Masyarakat tidak wajib paham struktur CSV untuk membantu. Kirim dulu data lewat issue `Masukan DB dari Rakyat` dalam bentuk:

- link sumber;
- file Excel/CSV;
- file Word;
- PDF;
- catatan/noted;
- teks biasa.

Tim Audit AI wajib membaca kontribusi sebagai `DRAFT_PUBLIC_SUBMISSION`, memberi skor validitas awal, lalu memetakan data ke modul Gudang DB.

- Validitas `>= 50%`: masuk audit queue Gudang DB sesegera mungkin.
- Validitas `40-49%`: menjadi task pencarian pembanding.
- Validitas `< 40%`: audit ketat link/dokumen/sumber; fake, spam, fitnah, atau data tidak bisa dicek diberi status `REJECTED_FAKE_OR_UNVERIFIABLE`.

Data yang lolos audit minimal harus dikejar sampai tampil di halaman/menu terkait setelah workflow validasi dan sinkronisasi berjalan.

## Aturan Data

Setiap data faktual wajib menyertakan sumber. Untuk data sensitif seperti korupsi, vendor, beneficial owner, pejabat publik, putusan, dan kerugian negara, gunakan status verifikasi yang jelas:

- `DRAFT_PUBLIC_SUBMISSION`
- `DRAFT_UNVERIFIED`
- `DRAFT_REVIEW`
- `AI_CLASSIFIED_NEEDS_VERIFICATION`
- `NEEDS_MORE_EVIDENCE`
- `REJECTED_NO_SOURCE`
- `REJECTED_FAKE_OR_UNVERIFIABLE`
- `VERIFIED_SOURCE`
- `RILL_CURRENT_PERIOD`
- `TEMUAN_AUDIT`
- `DUGAAN`
- `DAKWAAN`
- `PUTUSAN`
- `INKRACHT`
- `DIKOREKSI`

Jangan memasukkan klaim final tanpa dokumen publik.

Masukan publik tidak langsung masuk sebagai kebenaran final. Untuk klaim sensitif, gunakan aturan:

- satu sumber resmi, atau
- dua sumber independen yang kredibel, lalu tetap direview.

Jika belum cukup sumber, kontribusi akan masuk queue audit dan diberi label `NEEDS_MORE_EVIDENCE`.

## Aturan Anti-Hapus Data Valid

Data berstatus `VERIFIED`, `VERIFIED_SOURCE`, atau `INKRACHT` tidak boleh dihapus permanen.

Jika data valid perlu dikoreksi, kirim pull request yang:

- mengubah status menjadi `DISPUTED`, `DIKOREKSI`, atau `RETRACTED`,
- menjelaskan alasan koreksi,
- mencantumkan evidence baru,
- tidak menghilangkan riwayat tanpa alasan.

Jika record valid hilang, validator immutable akan gagal dan AI Agent dapat membuat PR restore otomatis.

## Format CSV

- Encoding: UTF-8.
- Pemisah: koma.
- Tanpa rumus Excel.
- Satu file untuk satu modul dan satu tahun: `{modul}_{tahun}.csv`.
- Data historis masuk ke folder era yang sesuai.

Contoh:

```text
gudang-db/3_era_modern_2011_2026/korupsi_2026.csv
```

## Sebelum Pull Request

Jalankan:

```bash
python scripts/validate_gudang_db.py
python scripts/validate_immutable_db.py
python scripts/generate_ai_index.py
```

Pastikan validator tidak mengeluarkan error.

## Prinsip Keselamatan Publik

- Jangan doxing.
- Jangan memuat data pribadi yang tidak relevan dengan pengawasan uang publik.
- Jangan menulis tuduhan tanpa sumber.
- Pisahkan data, analisis, dan opini.
- Berikan ruang koreksi jika ada bukti yang lebih kuat.
