# Donasi AI Premium

Status saat ini: belum aktif.

Donasi AI hanya boleh dipakai untuk biaya API/provider AI premium yang membantu:

- membuat draft update Gudang DB dari sumber publik;
- melengkapi metadata evidence dan periode data;
- membantu audit cashflow, akuntansi, vendor, program, dan red flag;
- menyiapkan bundle review sebelum data dipublish.

## Prinsip Aman

- Tidak ada rekening pribadi, nomor dompet, token, atau API key di repo publik.
- QRIS final harus hardcoded dari entitas/treasury publik yang disepakati.
- Nilai hardcoded sementara di HTML adalah `MR-AI-PUBLIC-QRIS-PENDING`, bukan akun aktif.
- AI tidak boleh langsung mempublish data hukum/korupsi tanpa review manusia dan sumber resmi.
- Semua biaya API harus dicatat di ledger donasi dan bisa diekspor.

## Rekomendasi Governance

Gunakan salah satu pola sebelum QRIS aktif:

- rekening/QRIS organisasi resmi yang punya pengurus dan audit terbuka;
- treasury multi-penanggung jawab;
- halaman donasi terpisah dengan laporan transaksi berkala;
- backend proxy agar API key premium tidak pernah masuk HTML publik.

Selama governance belum siap, tombol/QRIS donasi tetap berstatus pending.
