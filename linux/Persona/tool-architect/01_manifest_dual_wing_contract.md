---
id: tool-architect-manifest-contract
persona: tool-architect
target: prompt
priority: 92
cmd: ["/manifest", "/sop-tool"]
trigger:
  keywords: ["manifest.json", "dual wing", "exclude_keywords", "manifest tool", "openapi tool", "intercept gate", "skema parameter"]
  exclude_keywords: ["forex", "trading crypto"]
---

# 📜 SPESIFIKASI KONTRAK DUAL-WING MANIFEST (`manifest.json`)

Setiap tool eksternal di direktori `tools/<nama_tool>/` **WAJIB** menyertakan berkas `manifest.json` berstandar OpenAPI Object Schema. Berkas ini adalah paspor tunggal yang dibaca oleh runtime Flowork OS (`tools.rs` -> `scan_unmounted_tools`).

---

### 🏛️ 1. STRUKTUR LENGKAP MANIFEST.JSON

```json
{
  "name": "network_port_scanner",
  "category": "cyber_security",
  "description": "High-speed asynchronous TCP port scanner and service banner discovery. Probes specified ports on target host, measures round-trip latency, identifies open services, and maps active listening perimeters.",
  "command": "node tools/network_port_scanner/main.mjs",
  "entry": "main.mjs",
  "author": "Flowork Sovereign Core",
  "version": "1.0.0",
  "keywords": [
    "port",
    "ports",
    "port scanner",
    "scan port",
    "open port",
    "tcp scan",
    "network port",
    "service banner",
    "listening ports"
  ],
  "exclude_keywords": [
    "canvas port",
    "plugin port",
    "dynamic port",
    "env port"
  ],
  "tags": [
    "network_port_scanner",
    "security",
    "recon",
    "nano_plug",
    "zero_corner"
  ],
  "ui": {
    "css": "style.css",
    "zero_corner": true,
    "theme": "cyber_matrix"
  },
  "parameters": {
    "target": {
      "description": "Target hostname, IPv4, or IPv6 address to scan (e.g. '127.0.0.1', 'example.com').",
      "type": "STRING"
    },
    "ports": {
      "description": "Comma-separated list or range of TCP ports to inspect (e.g. '80,443,8080' or '1-1000'). Default: '80,443'.",
      "type": "STRING"
    },
    "timeout_ms": {
      "description": "Connection timeout in milliseconds per probed socket. Default: 1500.",
      "type": "NUMBER"
    },
    "keywords": {
      "description": "Mandatory on the first tool call of a turn: Comma-separated technical domain keywords in English (e.g. 'tcp socket probe port'). Used by Sovereign Skill Radar to locate relevant skills across storage and official repositories.",
      "type": "STRING"
    },
    "reason": {
      "description": "MANDATORY ON EVERY TOOL CALL: Clear, concise technical rationale explaining WHY you are calling this tool right now and what specific action it performs (displayed live to user HUD and recalls up to 3 memories from .fl_brain).",
      "type": "STRING"
    }
  }
}
```

---

### 🎯 2. ARSITEKTUR DUA SAYAP (DUAL-WING TRIGGER)

Untuk mengeliminasi **Tabrakan Panggilan Alat (Tool Collision)** di katalog ratusan perkakas:
1. **Sayap Positif (Positive Keywords Wing)**:
   - Berisi variasi istilah pencarian semantik domain spesifik dalam lowercase.
   - Menggunakan pencocokan *case-insensitive substring contains*.
2. **Sayap Negatif (Negative Exclusion Wing)**:
   - Berisi kata kunci pemicu yang jika muncul dalam query pencarian, **SEKETIKA MENGGUGURKAN TOOL INI** (*Short-Circuit Rejection*).
   - Mencegah tool umum terpanggil saat pengguna sebenarnya bermaksud memanggil domain lain.
   - Contoh: Tool `website_intelligence` mengecualikan `"youtube"` agar tidak merebut jatah `youtube_spy_video`.

---

### 🔒 3. MANDATORI PARAMETER INTERCEPT GATE

Seluruh manifest tool eksternal **WAJIB MENYERTAKAN DUA PARAMETER INI** di dalam objek `parameters`:
* **`reason` (`type: "STRING"`)**: Penjelasan teknis alasan eksekusi tool. Wajib disuplai pada setiap panggilan.
* **`keywords` (`type: "STRING"`)**: 5+ kata kunci teknis Bahasa Inggris untuk mengaktifkan Sovereign Skill Radar pada panggilan pertama giliran.
