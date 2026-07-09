# Public Intake Anonim

Endpoint ini dibuat agar netizen bisa upload file/link/teks tanpa login GitHub dan tanpa menampilkan nama akun publik.

## Alur

1. Dashboard mengirim `FormData` ke `MR_PUBLIC_INTAKE_ENDPOINT`.
2. Worker menerima submission sebagai `DRAFT_PUBLIC_SUBMISSION`.
3. Metadata dan file disimpan di binding `PUBLIC_SUBMISSIONS` jika R2/KV disediakan.
4. Worker memanggil `repository_dispatch` ke GitHub memakai secret `GITHUB_TOKEN`.
5. Workflow `AI Agent Readiness Patrol` membaca payload, memasukkan queue, promote ke Gudang DB draft, lalu rebuild dashboard summary.

## Secret dan Binding

- `GITHUB_TOKEN`: fine-grained token yang hanya boleh trigger workflow/repository dispatch pada repo ini.
- `PUBLIC_SUBMISSIONS`: binding penyimpanan file, disarankan R2 bucket privat.
- `ALLOWED_ORIGIN`: origin dashboard, default `https://monitoringuangrakyat.github.io`.
- `GITHUB_REPO`: default `MonitoringUangRakyat/monitoring-rakyat`.

## Dashboard

Set endpoint publik sebelum script dashboard berjalan:

```html
<script>
window.MR_PUBLIC_INTAKE_ENDPOINT = "https://endpoint-worker.example.workers.dev";
</script>
```

Jika endpoint kosong/gagal, dashboard wajib menghentikan upload publik dan menampilkan pesan bahwa endpoint anonim belum aktif. Dashboard tidak boleh membuka GitHub Issue sebagai fallback karena GitHub selalu menampilkan akun pengirim.
