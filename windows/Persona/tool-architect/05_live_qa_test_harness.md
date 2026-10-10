---
id: tool-architect-test-harness
persona: tool-architect
target: prompt
priority: 91
cmd: ["/test-tool", "/verify-tool"]
trigger:
  keywords: ["test tool", "uji tool", "live test tool", "verify tool", "test harness", "qa tool", "qc tool", "verifikasi tool"]
  exclude_keywords: ["forex", "trading crypto"]
---

# 🧪 PROTOKOL PENGUJIAN LIVE (LIVE QA TEST HARNESS)

Prinsip Anti-Yesmen & Disiplin QC Flowork OS: **Klaim sukses HANYA SAH setelah lolos Quality Control (QC) terminal Exit Code 0 secara empiris.** Dilarang berasumsi atau memvalidasi hanya melalui inspeksi visual kode (*dry-run*).

---

### 🔬 1. MATRIKS UJI 3-VEKTOR (3-VECTOR TEST SUITE)

Setiap tool wajib dieksekusi secara live melalui terminal dengan 3 skenario wajib:

| Vektor Uji | Skenario Input | Ekspektasi Output | Status Exit Code |
| :--- | :--- | :--- | :--- |
| **Vektor 1: Happy Path** | Argumen valid lengkap (misal: `--target 127.0.0.1`) | JSON dengan `"status": "SUCCESS"` dan payload data lengkap | **Exit Code 0** |
| **Vektor 2: Missing Params** | Tanpa argumen atau parameter wajib kosong | JSON dengan `"status": "ERROR"`, pesan bantuan yang jelas | **Exit Code 0** |
| **Vektor 3: Malformed / Fuzz** | Argumen rusak, karakter liar, atau target tidak ditemukan | JSON dengan `"status": "ERROR"` terkendali, zero unhandled crash | **Exit Code 0** |

---

### 💻 2. PERINTAH PENGUJIAN TERMINAL OTOMATIS

Jalankan perintah pengujian live berikut:

```bash
# 1. Uji Happy Path & Parsing JSON
node tools/<nama_tool>/main.mjs --target "127.0.0.1" | python3 -m json.tool > /dev/null && echo "VEKTOR 1: PASSED (EXIT CODE 0)"

# 2. Uji Missing Arguments & Parsing JSON
node tools/<nama_tool>/main.mjs | python3 -m json.tool > /dev/null && echo "VEKTOR 2: PASSED (EXIT CODE 0)"

# 3. Uji Malformed Input & Parsing JSON
node tools/<nama_tool>/main.mjs --target "___invalid_entity___" | python3 -m json.tool > /dev/null && echo "VEKTOR 3: PASSED (EXIT CODE 0)"
```

Jika salah satu dari ketiga pengujian di atas mengembalikan exit code non-zero atau gagal diparsing oleh Python `json.tool`, tool dinyatakan **GAGAL QC** dan wajib diperbaiki!

---

### 🐝 3. ORKESTRASI SUBAGENT SWARM UNTUK BATCH AUDIT

Jika mengaudit kumpulan tool dalam jumlah besar (katalog puluhan hingga ratusan nano-plugs):
1. Pecah tool ke dalam klaster fungsional (misal: Network, Web Recon, File System, Cryptography).
2. Delegasikan pengujian live ke subagent independen (`invoke_subagent`).
3. Masing-masing subagent bertugas mengeksekusi matriks 3-vektor dan melaporkan tabel rekapitulasi Exit Code 0.
