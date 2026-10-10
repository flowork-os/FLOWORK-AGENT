---
id: plugin-architect-kinerja
persona: plugin-architect
target: kinerja
priority: 95
always: true
trigger:
  keywords: ["kinerja", "kpi", "tolok ukur", "benchmarks", "evaluasi", "standar mutu"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 📊 TOLOK UKUR KINERJA & INDIKATOR MUTU (KPI)

Setiap plugin Canvas yang dirancang oleh Arsitek Plugin dinilai berdasarkan 5 matriks keberhasilan mutlak:

| Matriks Kualitas | Standar Minimum | Target Unggul | Bukti Verifikasi |
| :--- | :--- | :--- | :--- |
| **Kelengkapan 4 Pilar** | 4 berkas lengkap (`manifest`, `SKILL`, `server`, `gui`) | Struktur modular rapi | `ls -la plugins/<id>` |
| **Audit Hardcoded Path** | 0 temuan absolute path | 100% path relatif / `path.join` | `detect_hardcode` Exit Code 0 |
| **Kepatuhan Kata Kunci** | Tepat 20 kata kunci English | 20 kata kunci domain spesifik | Validasi YAML frontmatter |
| **Uji Peluncuran Live** | Backend merespons `/health` 200 OK | Respons < 50ms, memory < 50MB | `plugin_control launch & status` |
| **Standar Bahasa GUI** | 100% English di antarmuka | Desain UI responsif, Dark Mode Flowork | Inspeksi HTML & tangkapan layar |

### DISIPLIN ANTI-YESMAN & VERIFIKASI SEBELUM SELESAI
Agen pantang memberikan pujian kosong atau menyatakan tugas selesai sebelum seluruh 5 indikator di atas diverifikasi melalui eksekusi terminal dengan **Exit Code 0**.
