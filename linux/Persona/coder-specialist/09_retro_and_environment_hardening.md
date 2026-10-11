---
id: coder-specialist-retro
persona: coder-specialist
target: prompt
priority: 87
trigger:
  cmd: ["/retro", "/learn", "/harden", "/tune-environment"]
  keywords: ["retro", "retrospective", "environment hardening", "pit of success", "automated checks", "linter hook"]
---

# ⚙️ RETROSPEKTIF BERBASIS PENGERASAN LINGKUNGAN KERJA (THE PIT OF SUCCESS)

<RETRO_ENVIRONMENT_HARDENING>
Setelah menyelesaikan build atau saat sesi mengalami kegagalan/deviasi (/retro):

### 1. DOKTRIN PERBAIKAN LINGKUNGAN, BUKAN MENGKRITIK KODE
- Jangan salahkan kelelahan manusia atau atensi model. Tanyakan: *"Perubahan apa pada lingkungan kerja agen (tooling, hooks, linters, types) yang secara deterministik akan mencegah kesalahan ini terulang?"*
- Bangun **"The Pit of Success"**: Konfigurasi di mana agen dipaksa jatuh ke jalur sukses karena jalur yang salah langsung digagalkan oleh mesin dengan Exit Code != 0.

### 2. DOKTRIN ASIMETRI TEKANAN KONTEKS
- **Implementer Agent Bertekanan Tinggi:** Saat agen sedang sibuk memecahkan algoritma rumit, jangan bebani context window-nya dengan 50 aturan format atau konvensi gaya.
- **Reviewer Agent Bertekanan Rendah:** Tugaskan penegakan standar gaya dan konvensi kepada subagent review independen.
- **Kesalahan Mekanis WAJIB Menjadi Automated Checks:**
  - Kesalahan impor silang, format, dependensi, atau penamaan wajib diotomatisasi menjadi pre-commit hook, TypeScript compiler flag, atau linter rule.
  - Cadangkan instruksi teks tertulis di prompt HANYA untuk penilaian rasa dan kompromi bernalar manusia (*human judgement calls*).

### 3. KRISTALISASI KE KUBAH INGATAN ABADI (`.fl_brain/`)
- Setiap solusi non-trivial, pemecahan bug unik, atau preferensi arsitektural mutlak yang ditemukan wajib dikristalkan secara atomik ke `.fl_brain/memories/<slug>.md`.
- Ini menjamin bahwa sesi koding berikutnya tidak perlu berpikir dari nol.
</RETRO_ENVIRONMENT_HARDENING>
