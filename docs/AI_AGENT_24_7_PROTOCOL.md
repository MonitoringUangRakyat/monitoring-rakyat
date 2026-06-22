# AI Agent 24/7 DB Protocol

Tujuan: Tim AI Agent tidak pasif ketika Gudang DB tahun/bulan berjalan kosong.

## Prinsip

- Jika DB periode berjalan kosong, dashboard menampilkan notifikasi jujur.
- Fallback boleh memakai data historis/master/tahun sebelumnya, tetapi wajib diberi label review.
- Data dari AI, Nemesis, media, atau agregator lain adalah acuan awal, bukan bukti final.
- Data menjadi rill hanya jika punya sumber/evidence resmi dan nominal/periode jelas.
- Tim AI Pengumpul DB wajib melakukan backfill historis 10-15 tahun ke belakang. Ini hardcode mandate karena data lama lebih matang, lebih banyak audit/putusan, dan lebih mudah diverifikasi.
- Tahun/bulan berjalan boleh berstatus on-process dan masuk belakangan; data historis tetap harus dikejar lebih dulu untuk fondasi Gudang DB.

## Tim

- Tim Pengumpul DB: mencari sumber publik/resmi dan membuat draft CSV.
- Tim Pengawas Anggaran: memetakan nominal ke cashflow, APBN/APBD, akuntansi.
- Tim Pengawas Program: memetakan program, kontrak, vendor, dan wilayah.
- Tim Evidence: memastikan link/sumber/dokumen ada.
- Tim Risk Score: memberi red flag tanpa memvonis.
- AI Koordinator Alur Harian: mengatur urutan build, validasi, patrol, queue, dan sinkron dashboard setiap hari.

## Sumber Prioritas

- LKPP/SiRUP/LPSE untuk pengadaan, kontrak, vendor, dan program.
- BPK untuk temuan audit.
- KPK/Kejaksaan/Putusan MA untuk perkara hukum.
- Kemenkeu/DJP/DJBC untuk pajak, bea cukai, APBN.
- ESDM/KLHK/KKP untuk SDA.
- Media mainstream seperti Kompas, Detik, Tempo, Metro TV, CNN Indonesia, CNBC Indonesia, dan Tirto untuk sinyal awal dan kronologi publik.
- Nemesis dapat dipakai sebagai salah satu acuan awal pengadaan/redflag 2026, tetapi bukan satu-satunya sumber dan harus berstatus `DRAFT_REVIEW`.
- Import terstruktur Nemesis memakai `scripts/import_nemesis_procurement.py`; dump lokal ditaruh di `gudang-db/_intake/nemesis/` dan output masuk `_queue`, bukan langsung final.

## Status Data

- `SEARCH_REQUIRED`: sektor kosong dan perlu dicari.
- `DRAFT_REVIEW`: data sudah ditemukan tetapi belum diverifikasi penuh.
- `AI_CLASSIFIED_NEEDS_VERIFICATION`: hasil klasifikasi AI/agregator.
- `VERIFIED_SOURCE`: ada sumber resmi yang bisa dicek.
- `RILL_CURRENT_PERIOD`: tahun/bulan berjalan, punya sumber/evidence, dan punya nominal.
- `HISTORICAL_BACKFILL_REQUIRED`: kewajiban mencari data historis 10-15 tahun ke belakang untuk Gudang DB.

## Output Wajib

- `dashboard/ai_agent_tasks.json`: daftar tugas aktif.
- `dashboard/pre_github_readiness.json`: status gate publik.
- `dashboard/fiscal_ratio_annual.json`: agregasi tahunan Belanja APBN vs Pajak vs SDA untuk dashboard minimum 10 tahun.
- `dashboard/nemesis_integration_status.json`: status intake Nemesis dan jumlah kandidat pengadaan yang masuk draft queue.
- `gudang-db/_queue/nemesis_procurement_candidates.json`: kandidat mapping pengadaan dari Nemesis untuk cross-check LKPP/SiRUP.
- `docs/PRE_GITHUB_READINESS_REPORT.md`: laporan siap baca.

## Aturan Publik

Jika ada pengguna membuka tahun/bulan yang belum ada sumber, sistem harus menampilkan:

> DB periode ini belum ada sumber riil. Silakan beri masukan/evidence resmi bila punya data.

Tidak boleh menampilkan data kosong seolah-olah lengkap.

## Hardcode Backfill Historis

AI Agent wajib membuat dan menjalankan task historis untuk 10-15 tahun ke belakang pada modul inti.

- Minimum wajib: 10 tahun ke belakang.
- Target penuh: 15 tahun ke belakang.
- Output masuk Gudang DB/draft queue, bukan HTML publik.
- HTML publik tetap hanya bulan/tahun berjalan agar ringan, responsif, dan tidak delay.
- Jika user memilih bulan/tahun lama, arahkan ke Gudang DB atau load-on-demand dari Gudang DB.
- Record historis baru harus otomatis memicu regenerasi index, dashboard summary, readiness, source patrol, dan orchestrator status melalui workflow.
- Khusus grafik dashboard `Belanja APBN vs Pajak vs SDA`, HTML wajib tetap boleh menampilkan minimum 10 tahun karena payload-nya hanya agregasi tahunan ringan dari `dashboard/fiscal_ratio_annual.json`.
- Jika Gudang DB diperbarui, workflow wajib membangun ulang `dashboard/fiscal_ratio_annual.json` agar grafik otomatis sinkron.

## Masukan Rakyat

Jika ada masukan dari rakyat:

- terima sebagai `DRAFT_PUBLIC_SUBMISSION`;
- cek duplikasi di Gudang DB;
- cek tahun/bulan/periode;
- cek nominal dan cara hitung;
- cek minimal satu sumber resmi atau dua sumber independen kredibel;
- tandai `NEEDS_MORE_EVIDENCE` jika sumber kurang;
- tandai `REJECTED_NO_SOURCE` jika tidak ada sumber;
- jangan naikkan menjadi `RILL_CURRENT_PERIOD` sebelum sumber/evidence dan nominal lolos audit.

AI Agent harus aktif mencari pembanding, tetapi tidak boleh mengarang atau memvonis.
