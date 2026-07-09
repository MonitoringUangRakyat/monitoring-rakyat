# Integrasi Dashboard dan Gudang DB

## Kontrak Utama

Dashboard tidak membaca ribuan CSV mentah. Dashboard hanya membaca:

```text
dashboard/dashboard_summary.json
```

Gudang DB tetap menjadi sumber data mentah:

```text
gudang-db/{era}/{modul}_{tahun}.csv
```

Katalog lokal Gudang DB tersedia di:

```text
gudang-db/index.html
```

Halaman ini membaca `gudang-db/_index/ai_index.json` dan menampilkan link CSV per modul/tahun.

AI Pengawas membaca peta data:

```text
gudang-db/_index/ai_index.json
```

## File Dashboard

- `index.html`: dashboard HTML utama.
- `app.js`: bridge ringan yang menampilkan panel Gudang DB dan membaca summary.
- `dashboard_summary.json`: ringkasan angka dashboard tahun berjalan.

`index.html` sudah memuat:

```html
<script src="app.js"></script>
```

## Update Summary

Saat data CSV sudah diisi, update `dashboard_summary.json` dengan hasil agregasi:

```json
{
  "tahun": 2026,
  "kerugian_total": 120000000000000,
  "recovery_total": 23000000000000,
  "jumlah_kasus": 458,
  "jumlah_koruptor": 892,
  "history_akumulasi": {
    "2016": 35000000000000,
    "2018": 56000000000000,
    "2021": 68000000000000,
    "2024": 89000000000000,
    "2026": 120000000000000
  },
  "catatan": "Angka contoh/placeholder - ganti dengan hasil agregasi dari gudang-db setelah data diisi."
}
```

## Update Link GitHub

Default lokal memakai:

```text
../gudang-db
```

Setelah repo publik tersedia, URL raw Gudang DB dapat disetel dari panel:

```text
AI Settings -> Gudang DB Repository
```

## Konvensi CSV

Gunakan format:

```text
{modul}_{tahun}.csv
```

Contoh:

```text
korupsi_2026.csv
bea_cukai_2024.csv
bumn_2011.csv
```

CSV harus UTF-8, dipisahkan koma, tanpa rumus Excel, dan menyertakan sumber data jika memuat klaim faktual.
