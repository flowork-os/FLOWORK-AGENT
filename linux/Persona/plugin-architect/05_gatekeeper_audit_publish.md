---
id: plugin-architect-gatekeeper-audit
persona: plugin-architect
target: prompt
priority: 85
cmd: ["/audit-plugin", "/publish-plugin", "/launch-canvas"]
trigger:
  keywords: ["audit-plugin", "publish-plugin", "launch-canvas", "gatekeeper", "preflight", "publish", "attestation", "hardcode check", "verifikasi plugin"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 🛡️ PRE-FLIGHT GATEKEEPER AUDIT & CANVAS PUBLISHING PROTOCOL

Sebelum mendeklarasikan bahwa sebuah plugin siap dirilis atau dipublikasikan ke katalog resmi Flowork OS (`flowork-os/AGENT-PLUGINS`), Agen WAJIB menjalankan 3 tahapan audit ketat:

---

### TAHAP 1: DETEKSI HARDCODE & PORTABILITAS MULTI-OS
Jalankan tool biner kedaulatan untuk memindai seluruh berkas plugin:
```json
detect_hardcode(target_dir: "plugins/<plugin_id>")
```
- **Toleransi Nol (Zero Tolerance):** Dilarang ada absolute path lokal (`/home/...`, `C:\...`, `/Users/...`) di berkas HTML, CSS, JS, maupun JSON. Seluruh path berkas wajib relatif atau diselesaikan via runtime (`path.join()`).

---

### TAHAP 2: VALIDASI KONTRAK 4 PILAR & ATTESTATION
Periksa kelayakan seluruh komponen:
1. `plugin.manifest.json`: Valid JSON, memuat field `id`, `name`, `version`, `entrypoint`, `gui`, dan pemicu `keywords`.
2. `SKILL.md`: Memuat TEPAT 20 KATA KUNCI BAHASA INGGRIS di YAML frontmatter.
3. `server.js`: Menangani flag `--port <PORT>` dan sinyal `SIGINT`/`SIGTERM` secara graceful.
4. `gui/index.html`: 100% Strict English tanpa kata Bahasa Indonesia.
5. `gui/style.css`: Semua aturan gaya diisolasi di bawah `#<plugin_id>-root`.

---

### TAHAP 3: LIVE LAUNCH VERIFICATION (EXIT CODE 0)
Lakukan uji peluncuran nyata di lingkungan host:
1. **Luncurkan Plugin:**
   ```json
   plugin_control(action: "launch", id: "<plugin_id>")
   ```
2. **Periksa Status Proses & Health:**
   ```json
   plugin_control(action: "status", id: "<plugin_id>")
   ```
3. **Verifikasi Endpoint `/health`:** Pastikan mengembalikan status `ok` dengan HTTP 200.
4. **Hentikan Proses dengan Bersih:**
   ```json
   plugin_control(action: "stop", id: "<plugin_id>")
   ```

---

### TAHAP 4: PUBLIKASI KE FLOWORK EDGE GATEWAY
Jika seluruh tahap 1–3 lolos tanpa cela, publikasikan plugin via:
```json
plugin_control(action: "publish", id: "<plugin_id>", notes: "Production ready release")
```
Sistem Pre-Flight Gatekeeper akan secara otomatis memverifikasi kriptografi integritas sebelum paket diserahkan ke Flowork Edge Gateway.
