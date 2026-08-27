# Kandidat Update Berita DB - 2026-08-27

Diverifikasi pada: 2026-08-27 08:47 WIB.

## Kebenaran Utama

DB tidak boleh langsung dipromosikan dari berita menjadi data final. Hasil cek ini hanya masuk antrean `gudang-db/_queue/ai_pengawas_candidates.csv` dengan status `DRAFT_REVIEW`.

## Status Bukti

- [Terverifikasi][Diamati Langsung] File antrean kandidat diperbarui dengan 7 baris baru pada `gudang-db/_queue/ai_pengawas_candidates.csv`.
- [Terverifikasi][Dilaporkan Sumber] ANTARA melaporkan KPK menyebut dugaan kerugian negara Rp322,18 miliar dalam kasus digitalisasi SPBU PT Pertamina 2018-2023.
- [Terverifikasi][Dilaporkan Sumber] ANTARA melaporkan KPK menyatakan Bupati Kuansing nonaktif diduga memotong TPP ASN hingga 50 persen.
- [Terverifikasi][Dilaporkan Sumber] ANTARA melaporkan KPK menahan mantan Kepala Kanwil Ditjen Pajak Jakarta Khusus terkait dugaan gratifikasi.
- [Terverifikasi][Dilaporkan Sumber] Tirto melaporkan KPK menahan 4 tersangka kasus Bank BJB dengan dugaan kerugian negara Rp223,6 miliar.
- [Terverifikasi][Dilaporkan Sumber] Media Indonesia melaporkan pemeriksaan saksi PUPR Kota Bengkulu terkait temuan Rp4 miliar.
- [Terverifikasi][Dilaporkan Sumber] Monitor Indonesia melaporkan pemeriksaan saksi Pelni/Jasindo; laporan tersebut perlu cek silang karena bukan sumber primer.
- [Terverifikasi][Dilaporkan Sumber] ANTARA melaporkan KPK menghentikan penyidikan enam kasus, termasuk kasus Sekjen DPR; ini dicatat sebagai audit trail, bukan daftar pelaku.

## Kandidat Baru

| ID Queue | Modul | Status | Sumber | Ringkasan |
|---|---|---|---|---|
| MR-AI-20260827-ANTARA-SPBU | korupsi | DRAFT_REVIEW | ANTARA | Dugaan korupsi digitalisasi SPBU PT Pertamina 2018-2023; KPK menyebut dugaan kerugian Rp322,18 miliar. |
| MR-AI-20260827-ANTARA-KUANSING | korupsi | DRAFT_REVIEW | ANTARA | Dugaan pemotongan TPP ASN Kuansing hingga 50 persen. |
| MR-AI-20260827-TIRTO-BJB | korupsi | DRAFT_REVIEW | Tirto | Penahanan 4 tersangka Bank BJB; dugaan kerugian Rp223,6 miliar. |
| MR-AI-20260827-ANTARA-DJP | pajak | DRAFT_REVIEW | ANTARA | Penahanan mantan Kepala Kanwil DJP Jakarta Khusus terkait dugaan gratifikasi. |
| MR-AI-20260827-MEDIAINDONESIA-BENGKULU | korupsi | DRAFT_REVIEW | Media Indonesia | Pemeriksaan saksi PUPR Kota Bengkulu terkait temuan Rp4 miliar. |
| MR-AI-20260827-MONITOR-JASINDO | bumn | DRAFT_REVIEW | Monitor Indonesia | Pemeriksaan saksi Pelni/Jasindo; laporan menyebut kontrak Rp263 miliar dan kerugian Rp15,6 miliar. |
| MR-AI-20260827-ANTARA-SP3 | audittrail | DRAFT_REVIEW | ANTARA | KPK menghentikan penyidikan enam kasus; dicatat sebagai audit trail/SP3. |

## Sumber yang Diperiksa

- https://www.antaranews.com/berita/5679871/kpk-sebut-negara-rugi-rp32218-miliar-akibat-kasus-digitalisasi-spbu
- https://www.antaranews.com/berita/5680115/kpk-bupati-kuansing-nonaktif-potong-tpp-asn-hingga-50-persen
- https://tirto.id/kpk-tahan-4-tersangka-kasus-bank-bjb-rugikan-negara-rp2236-m-hA2y
- https://www.antaranews.com/berita/5702188/kpk-tahan-mantan-kepala-kanwil-ditjen-pajak-jakarta-khusus
- https://mediaindonesia.com/politik-dan-hukum/925645/kasus-suap-bengkulu-kpk-periksa-bendahara-pupr-terkait-temuan-rp4-miliar
- https://monitorindonesia.com/hukum/read/2026/08/632776/4-tersangka-ditahan-kpk-kini-periksa-petinggi-pelni-terkait-korupsi-asuransi-jasindo
- https://m.antaranews.com/amp/berita/5678453/kpk-hentikan-penyidikan-enam-kasus-termasuk-kasus-sekjen-dpr

## Batasan

- Belum semua kandidat diperiksa ke sumber primer KPK, BPK, BPKP, putusan pengadilan, atau dokumen perkara.
- Angka kerugian masih mengikuti laporan sumber, belum direkonsiliasi dengan dokumen primer.
- Kandidat dengan status saksi/pemeriksaan/penyidikan tidak boleh masuk `master_koruptor.csv`.
- Kandidat SP3 hanya boleh menjadi audit trail/status perkara, bukan klaim kesalahan.

## Cara Memverifikasi Sebelum Promosi DB

1. Cek rilis resmi KPK atau halaman penanganan perkara.
2. Cek dokumen BPK/BPKP bila angka kerugian disebut.
3. Cek putusan PN/PT/MA bila status hukum sudah vonis.
4. Cek duplikasi terhadap `korupsi_2026.csv`, `koruptor_db_2026.csv`, dan `master_koruptor.csv`.
5. Promosikan hanya setelah status, subjek, nominal, periode, dan sumber primer jelas.
