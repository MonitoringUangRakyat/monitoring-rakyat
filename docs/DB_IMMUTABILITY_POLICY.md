# DB Immutability Policy

Kebijakan ini menjaga agar data valid di Gudang DB tidak hilang karena penghapusan sepihak.

## Prinsip

- Data publik yang sudah punya evidence valid tidak boleh dihapus permanen.
- Koreksi data dilakukan dengan perubahan status dan catatan, bukan menghilangkan jejak.
- AI Agent boleh mengusulkan restore otomatis, tetapi perubahan tetap lewat pull request dan review.
- Data sensitif tidak boleh dinaikkan ke status final tanpa sumber primer atau sumber publik kredibel yang cukup.

## Status Data

- `DRAFT_REVIEW`: data ditemukan, belum selesai cek silang.
- `NEED_SOURCE`: data perlu sumber tambahan.
- `VERIFIED`: data punya evidence publik yang memadai.
- `INKRACHT`: data sudah berkekuatan hukum tetap atau didukung putusan final.
- `DISPUTED`: data sedang diperdebatkan atau ada bantahan/koreksi serius.
- `RETRACTED`: data tidak valid dan ditarik dengan alasan/evidence yang dicatat.

## Aturan Hapus

Record dengan status `VERIFIED` atau `INKRACHT` tidak boleh dihapus langsung.

Jika record valid bermasalah:

1. Ubah status menjadi `DISPUTED`.
2. Tambahkan alasan, sumber koreksi, dan tanggal review.
3. Jika terbukti salah, ubah menjadi `RETRACTED`.
4. Simpan riwayat di ledger, jangan hapus baris tanpa jejak.

## Immutable Index

File `gudang-db/_ledger/immutable_index.json` menyimpan daftar record yang dilindungi.

Validator:

```bash
python scripts/validate_immutable_db.py
```

Jika record valid hilang, validasi gagal dan AI Agent wajib membuat PR restore.

## AI Agent Restore Protocol

Jika validator mendeteksi record valid hilang:

1. AI Agent membaca `immutable_index.json`.
2. AI Agent mencari record terakhir dari riwayat Git atau backup release.
3. AI Agent membuat branch restore.
4. AI Agent membuat PR dengan label `AUTO_RESTORE_VALID_DB`.
5. PR wajib berisi alasan restore, ID record, file sumber, status, dan evidence.
6. Maintainer/reviewer memutuskan merge.

AI Agent tidak boleh menghapus, menurunkan status, atau mengubah data sensitif menjadi final tanpa evidence.

## Backup

Setiap release publik harus punya:

- Git tag/release ZIP.
- Hash/checksum release.
- Backup offline.
- Mirror repo jika memungkinkan.

Open source berarti siapa pun boleh fork, tetapi repo resmi menjaga keaslian data lewat ledger, review, dan rilis bertanda.
