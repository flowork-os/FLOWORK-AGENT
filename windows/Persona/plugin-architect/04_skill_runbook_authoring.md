---
id: plugin-architect-skill-authoring
persona: plugin-architect
target: prompt
priority: 85
cmd: ["/write-skill", "/plugin-skill"]
file_patterns: ["plugins/**/SKILL.md", "plugins/**/skill.md"]
trigger:
  keywords: ["write-skill", "plugin skill", "runbook", "20 keywords", "sop plugin", "authoring skill", "twenty keywords", "skill frontmatter"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 📜 AUTHORING PLUGIN RUNBOOK SOP (`SKILL.md`)

Setiap plugin di Flowork Canvas WAJIB memiliki berkas runbook SOP `plugins/<plugin_id>/SKILL.md`. Berkas ini adalah manual pemandu bagi AI Agent agar memahami cara berinteraksi dengan plugin tersebut secara otonom.

---

### 🛡️ ATURAN MUTLAK TEPAT 20 KATA KUNCI BAHASA INGGRIS
Runtime Flowork OS memvalidasi frontmatter YAML secara ketat (`keywords.len() == 20`).
- **Kurang dari 20 kata kunci:** Plugin ditolak runtime dan gagal validasi attestation!
- **Lebih dari 20 kata kunci:** Plugin ditolak runtime!
- **Bukan Bahasa Inggris:** Gagal inspeksi sanitasi!

```yaml
---
name: <plugin_id>_interactive_co_creation
description: SOP and API runbook for AI Agent interaction with the <Plugin Name> Canvas plugin, covering REST endpoints, event streams, and real-time state synchronization.
author: "@awenkaudico"
version: "1.0.0"
keywords:
  - <keyword_1>
  - <keyword_2>
  - <keyword_3>
  - <keyword_4>
  - <keyword_5>
  - <keyword_6>
  - <keyword_7>
  - <keyword_8>
  - <keyword_9>
  - <keyword_10>
  - <keyword_11>
  - <keyword_12>
  - <keyword_13>
  - <keyword_14>
  - <keyword_15>
  - <keyword_16>
  - <keyword_17>
  - <keyword_18>
  - <keyword_19>
  - <keyword_20>
exclude_keywords:
  - <negative_keyword_1>
  - <negative_keyword_2>
  - <negative_keyword_3>
---
```

---

### 📖 ANATOMI WAJIB ISI `SKILL.MD` PLUGIN
1. **Executive Overview**: Penjelasan tujuan meja kerja kolaborasi interaktif.
2. **Interactive Co-Creation Flow**: Panduan langkah-demi-langkah bagi AI Agent saat mendeteksi pengguna sedang berinteraksi di Canvas UI.
3. **REST API Contract**:
   - Dokumentasi lengkap endpoint: URL, metode HTTP (`GET`/`POST`), payload JSON input, dan schema response JSON.
4. **SSE Event Stream Contract**:
   - Tipe-tipe event yang disiarkan server (`status_change`, `action_completed`, `error_event`).
5. **Lifecycle Management**:
   - Cara meluncurkan dan menghentikan plugin via biner Flowork:
     ```json
     plugin_control(action: "launch", id: "<plugin_id>")
     plugin_control(action: "status", id: "<plugin_id>")
     plugin_control(action: "stop", id: "<plugin_id>")
     ```
