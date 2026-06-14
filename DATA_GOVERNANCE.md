# Data Governance

Dokumen ini adalah aturan dasar agar Monitoring Rakyat bisa dipercaya publik.

## Scope Dashboard

Dashboard HTML publik hanya menampilkan data tahun dan bulan berjalan. Untuk rilis saat ini:

- Tahun aktif: 2026
- Bulan aktif: Juni
- Trend dashboard: kerangka 20 tahun agregasi; tahun tanpa DB tampil kosong/0

Data di luar periode aktif tidak dimuat sebagai tabel mentah di HTML. Rakyat diarahkan ke Gudang DB untuk tracking historis.

## Source of Truth

Source of truth adalah CSV di:

```text
gudang-db/
```

Dashboard hanya membaca ringkasan:

```text
dashboard/dashboard_summary.json
```

AI hanya memakai index:

```text
gudang-db/_index/ai_index.json
```

## Sumber Resmi yang Diprioritaskan

- APBN/APBD, Kementerian Keuangan, Kemendagri.
- LHKPN KPK.
- Direktori Putusan Mahkamah Agung.
- LHP BPK.
- LKPP, SIRUP, LPSE.
- AHU Kemenkumham.
- Rilis resmi KPK, Kejaksaan, pengadilan, kementerian/lembaga, dan pemerintah daerah.

## Multi-Source Intelligence

Project ini tidak boleh bergantung pada satu sumber saja. Tim AI Agent memakai banyak sumber dengan bobot berbeda:

- Sumber resmi/audit/putusan: confidence awal 90-95.
- LKPP/SiRUP/LPSE dan data pengadaan resmi: confidence awal 90.
- Media mainstream seperti Kompas, Detik, Tempo, Metro TV, CNN Indonesia, CNBC Indonesia, Tirto: confidence awal 70-75 sebagai sinyal publik.
- Agregator/AI seperti Nemesis: confidence awal 60 sebagai acuan awal, bukan bukti final.
- Masukan rakyat: confidence awal 30 sampai lolos audit.

Daftar sumber awal disimpan di:

```text
gudang-db/master/master_source_registry.csv
```

Media mainstream boleh menjadi pintu awal pencarian dan cross-check, tetapi klaim sensitif tetap harus naik status melalui audit/evidence.

## Status Verifikasi

Gunakan status yang eksplisit:

- `DRAFT_PUBLIC_SUBMISSION`: masukan rakyat baru masuk dan belum diaudit.
- `DRAFT_UNVERIFIED`: data baru masuk, belum diverifikasi.
- `DRAFT_REVIEW`: data punya sumber awal tetapi masih perlu cek ulang.
- `AI_CLASSIFIED_NEEDS_VERIFICATION`: data hasil klasifikasi AI/agregator, belum final.
- `NEEDS_MORE_EVIDENCE`: sumber belum cukup.
- `REJECTED_NO_SOURCE`: ditolak karena tidak ada sumber yang bisa dicek.
- `VERIFIED_SOURCE`: sumber resmi/independen sudah dicek.
- `RILL_CURRENT_PERIOD`: data periode berjalan, punya sumber/evidence, dan punya nominal.
- `TEMUAN_AUDIT`: berasal dari laporan audit.
- `DUGAAN`: masih indikasi awal.
- `DAKWAAN`: sudah masuk proses dakwaan.
- `PUTUSAN`: sudah ada putusan pengadilan.
- `INKRACHT`: putusan berkekuatan hukum tetap.
- `DIKOREKSI`: data direvisi berdasarkan bukti baru.

## Immutable DB dan Anti-Penghapusan

Record dengan status `VERIFIED_SOURCE`, `VERIFIED`, atau `INKRACHT` tidak boleh dihapus permanen.

Jika ada koreksi:

- ubah status menjadi `DISPUTED` atau `DIKOREKSI`,
- cantumkan sumber koreksi,
- jika data terbukti salah, ubah menjadi `RETRACTED`,
- jangan menghapus jejak tanpa ledger.

Index data valid disimpan di:

```text
gudang-db/_ledger/immutable_index.json
```

Validator wajib dijalankan:

```bash
python scripts/validate_immutable_db.py
```

Jika data valid hilang, AI Agent wajib mengusulkan pull request restore dengan label `AUTO_RESTORE_VALID_DB`.

## AI Policy

AI Pengawas hanya memberi indikator awal. AI tidak boleh menjadi sumber tunggal untuk:

- Vonis hukum.
- Tuduhan korupsi.
- Identifikasi beneficial owner final.
- Penetapan kerugian negara final.

Setiap output AI harus bisa ditelusuri ke data dan sumber.

## Masukan Publik

Masukan dari rakyat wajib dicek dan ricek sebelum masuk Gudang DB.

- Semua masukan publik dimulai dari `DRAFT_PUBLIC_SUBMISSION`.
- Klaim sensitif wajib punya satu sumber resmi atau dua sumber independen kredibel.
- Jika belum cukup sumber, masukan disimpan sebagai task pencarian, bukan data rill.
- AI Agent wajib cek duplikasi, periode, nominal, sumber, dan status hukum.
- Aturan lengkap ada di `docs/PUBLIC_SUBMISSION_AUDIT.md`.
