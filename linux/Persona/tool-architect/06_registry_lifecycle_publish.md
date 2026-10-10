---
id: tool-architect-publish-lifecycle
persona: tool-architect
target: prompt
priority: 90
cmd: ["/publish-tool", "/mount-tool", "/unmount-tool"]
trigger:
  keywords: ["publish tool", "mount tool", "unmount tool", "search_tools", "registry tool", "flowork-os/agent-tools", "katalog tool", "lifecycle tool"]
  exclude_keywords: ["forex", "trading crypto"]
---

# 🚀 SIKLUS HIDUP REGISTRY & PUBLIKASI RESMI (`search_tools`)

Perkakas eksternal Flowork OS hidup di dalam ekosistem dinamis dengan registri sharded global. Agen dapat mencari, memasang (*mount*), melepas (*unmount*), serta mempublikasikan (*publish*) tool teruji ke repositori resmi Flowork OS (`flowork-os/AGENT-TOOLS`).

---

### 🔍 1. SIKLUS MOUNTING ON-DEMAND (ANTI-BLOAT CONTEXT)

Hanya tool yang aktif di-*mount* yang disuntikkan ke dalam deklarasi fungsi LLM. Ketika tugas selesai, tool wajib di-*unmount* untuk menghemat token konteks:

```bash
# 1. Cari tool di katalog lokal:
search_tools(action: "search", query: "port scanner")

# 2. Pasang (mount) tool ke sesi aktif (tersedia di turn berikutnya):
search_tools(action: "mount", tools: ["network_port_scanner"])

# 3. Lepas (unmount) setelah tugas selesai agar tidak membebani context window:
search_tools(action: "unmount", tools: ["network_port_scanner"])

# 4. Periksa daftar tool yang sedang terpasang di sesi:
search_tools(action: "list_mounted")
```

---

### 🌐 2. PENCARIAN & INSTALASI REMOTE DARI REGISTRY RESMI

Jika kebutuhan perkakas belum tersedia di lokal, cari di registri sharded cloud:

```bash
# 1. Cari tool di registri cloud resmi Flowork OS:
search_tools(action: "search_remote", query: "docker container inspect")

# 2. Unduh dan pasang otomatis ke direktori tools/ lokal:
search_tools(action: "install_remote", tool_id: "docker_container_inspector")
```

---

### 📤 3. PROTOKOL PUBLIKASI RESMI KE REPOSITORI GITHUB

Setelah sebuah tool baru berhasil dibuat, dikeraskan, dan lulus uji 3-vektor dengan Exit Code 0:
1. **Mandatori Pre-Flight Checklist**:
   - [x] Lolos `detect_hardcode` dengan `clean: true` (Exit Code 0).
   - [x] Lolos `flow_audit_security` tanpa temuan kerentanan kritis.
   - [x] Lolos pengujian terminal live 3-vektor dengan respons valid JSON.
   - [x] Seluruh teks deskripsi & parameter manifest dalam 100% Strict English.
   - [x] Jika ada `SKILL.md`, memiliki tepat 20 kata kunci Bahasa Inggris.
2. **Eksekusi Publikasi**:
   ```bash
   search_tools(
       action: "publish",
       tool_id: "<nama_tool>",
       notes: "feat: add <nama_tool> sovereign nano-plug with triple-lock error containment"
   )
   ```
3. **Mandatori Git Commit Co-Author**:
   Setiap commit atau pembaruan git terkait tools WAJIB menyertakan co-author resmi:
   ```
   Co-authored-by: Flowork OS <agent@floworkos.com>
   ```
