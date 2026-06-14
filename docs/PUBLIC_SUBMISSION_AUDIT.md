# Audit Masukan Publik

Masukan rakyat sangat penting, tetapi tidak boleh langsung menjadi kebenaran final.

## Prinsip Utama

- Semua masukan publik masuk sebagai `DRAFT_PUBLIC_SUBMISSION`.
- Tim AI Agent wajib cek dan ricek sebelum data masuk Gudang DB.
- Data tanpa sumber tidak boleh tampil sebagai data rill.
- Tuduhan korupsi, kerugian negara, beneficial owner, dan nama orang harus diperlakukan sebagai data sensitif.
- Jika sumber lemah, data tetap boleh disimpan sebagai task pencarian, bukan sebagai klaim publik.

## Syarat Minimal Masukan

Masukan publik harus berisi:

- Modul: contoh `korupsi`, `bea_cukai`, `vendor`, `kontrak`, `sda`, `parpol`.
- Tahun dan bulan/periode.
- Nama instansi/program/vendor/pelaku jika relevan.
- Nominal jika ada.
- Link sumber atau dokumen pendukung.
- Status hukum/verifikasi jika relevan.

## Two-Source Rule

Untuk klaim sensitif, minimal salah satu harus terpenuhi:

- satu sumber resmi: BPK, KPK, Kejaksaan, MA/pengadilan, LKPP/SiRUP, Kemenkeu, kementerian/lembaga resmi; atau
- dua sumber publik independen yang kredibel, termasuk media mainstream seperti Kompas, Detik, Tempo, Metro TV, CNN Indonesia, CNBC Indonesia, atau Tirto, lalu tetap diberi status `DRAFT_REVIEW`.

Jika hanya ada satu sumber media/agregator, statusnya:

```text
AI_CLASSIFIED_NEEDS_VERIFICATION
```

## Red Flag Masukan Ngawur

AI Agent wajib menandai/menolak masukan jika:

- tidak ada link sumber;
- nominal tidak masuk akal dan tidak ada dokumen;
- tanggal/tahun/bulan tidak jelas;
- hanya opini, rumor, atau screenshot tanpa konteks;
- mengandung doxing/data pribadi tidak relevan;
- menuduh orang tanpa proses hukum/sumber resmi;
- duplikat dari data yang sudah ada.

## Alur Audit

1. Terima masukan publik sebagai issue/PR/form.
2. Simpan ke queue dengan status `DRAFT_PUBLIC_SUBMISSION`.
3. Cek format: modul, tahun, bulan, nominal, sumber.
4. Cek duplikasi di Gudang DB.
5. Cek sumber resmi atau dua sumber independen.
6. Tandai status:
   - `REJECTED_NO_SOURCE`
   - `NEEDS_MORE_EVIDENCE`
   - `DRAFT_REVIEW`
   - `VERIFIED_SOURCE`
   - `RILL_CURRENT_PERIOD`
7. Baru setelah lolos, data boleh masuk CSV Gudang DB.

## Sikap AI Agent

AI Agent harus proaktif mencari pembanding, tetapi tetap konservatif:

- tidak memvonis;
- tidak mengarang sumber;
- tidak menaikkan klaim sensitif tanpa evidence;
- selalu menyimpan catatan audit.

## Bobot Sumber Awal

- Sumber resmi/audit/putusan: 90-95.
- Data pengadaan resmi LKPP/SiRUP/LPSE: 90.
- Media mainstream: 70-75.
- Agregator/AI seperti Nemesis: 60.
- Masukan rakyat tanpa sumber pembanding: 30.

Bobot ini bukan vonis. Bobot hanya membantu prioritas audit dan pencarian pembanding.
