# AI Mode Policy

AI Pengawas Uang Rakyat harus bisa berjalan dalam mode gratis/offline dan bisa meningkat ke mode premium jika ada dukungan publik.

## Mode AI

### Free Local

Mode ini tidak mengirim data ke luar browser.

- DB lokal / rule engine.
- Ollama/local model jika tersedia.
- Cocok untuk audit cepat, cek evidence, cashflow, dan draft queue.

Contoh provider:

- Gemma4 E4B Q4 - Fast Brain.
- Hermes Agent - TIM CODING.
- 9Router masih diparkir.

### Free Cloud

Mode ini memakai provider cloud yang punya kuota gratis atau key sendiri.

- Groq FREE / Groq key sendiri.
- Gemini FREE.
- Harus fallback ke Free Local jika key/proxy belum tersedia.

### Premium

Mode premium dipakai jika ada Donasi AI atau biaya operasional yang transparan.

- OpenAI.
- Claude.
- Gemini paid.
- NVIDIA NIM/Nemotron.

Untuk repo publik, mode premium sebaiknya lewat backend proxy agar API key tidak bocor di browser.

## Donasi AI

Donasi AI bertujuan membiayai provider premium agar AI bisa membantu:

- Membaca sumber data publik.
- Membuat draft CSV Gudang DB.
- Melengkapi metadata evidence.
- Membuat draft koreksi dan enrichment.
- Menyiapkan bundle update untuk review/PR.

Donasi AI bukan untuk membuat AI memvonis orang. Semua output AI tetap draft sampai diverifikasi.

## Autonomous DB Builder

AI boleh membuat draft update Gudang DB secara mandiri, tetapi HTML publik tidak boleh menyimpan token GitHub atau menulis langsung ke repo.

Alur aman:

```text
AI scan DB -> draft queue lokal -> export bundle -> review -> Pull Request
```

Jika nanti ada backend aman:

```text
AI scan DB -> draft queue -> backend proxy -> branch/PR otomatis
```

Backend wajib menyimpan token secara server-side, bukan di HTML.

## Batas Aman

- Tidak auto-publish tanpa review.
- Tidak membuat klaim hukum tanpa sumber.
- Tidak mengirim data ke cloud jika mode Free Local aktif.
- Tidak menyimpan API key di repo.
- Semua enrichment harus punya status `DRAFT_REVIEW` sebelum masuk Gudang DB.
