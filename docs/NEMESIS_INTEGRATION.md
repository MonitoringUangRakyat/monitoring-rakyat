# Nemesis Procurement Signal

Nemesis dipakai sebagai akselerator mapping pengadaan, bukan bukti final tunggal.

Sumber:

- Dashboard: https://nemesis.assai.id
- Repo: https://github.com/assai-id/nemesis
- Transparansi algoritma: https://nemesis.assai.id/algoritma

## Peran

Nemesis membantu Monitoring Rakyat mempercepat mapping:

- paket pengadaan;
- K/L/PD;
- satker;
- lokasi;
- pagu;
- sumber dana;
- potensi pemborosan;
- red flag;
- vendor dan program terkait.

Semua hasil dari Nemesis wajib masuk status `DRAFT_REVIEW` dan `NEEDS_LKPP_SIRUP_CROSSCHECK`.

## Jalur Intake

Taruh dump Nemesis lokal di:

```text
gudang-db/_intake/nemesis/
```

Format yang diterima:

- `.jsonl`
- `.json`
- `.csv`

Jalankan:

```text
python scripts/import_nemesis_procurement.py
```

Output:

- `gudang-db/_queue/nemesis_procurement_candidates.json`
- `gudang-db/_queue/nemesis_procurement_candidates.csv`
- `dashboard/nemesis_integration_status.json`

## Guard

AI Agent tidak boleh memindahkan kandidat Nemesis menjadi data final sebelum:

- paket cocok dengan LKPP/SiRUP asli;
- nominal/pagu jelas;
- K/L/PD dan satker jelas;
- periode/tahun jelas;
- red flag punya alasan yang bisa diaudit;
- jika menjadi klaim korupsi/kerugian negara, harus ada BPK/KPK/Kejaksaan/putusan atau dua sumber kredibel tambahan.
