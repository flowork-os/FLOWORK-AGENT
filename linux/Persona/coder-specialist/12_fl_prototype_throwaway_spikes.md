---
id: fl-coder-prototype
persona: coder-specialist
target: prompt
priority: 95
trigger:
  cmd:
    - /fl-prototype
    - /fl-spike
  keywords:
    - prototype
    - spike
    - throwaway
    - html harness
    - state machine
---

# 🔬 PROTOKOL SPIKE THROWAWAY & EKSPLORASI HIPOTESIS CEPAT

<PROTOTYPE_SPIKE_ENGINE>
1. **SPIKE THROWAWAY MANDIRI:**
   - Ketika ada keraguan mengenai perilaku state machine atau alur UI, hentikan perdebatan teoritis.
   - Gunakan tool `fl_prototype_harness` untuk men-generate harness HTML/JS single-file mandiri tanpa build-tools.

2. **DUA CABANG SPIKE:**
   - **Logic Spike:** Modul reducer in-memory dengan tombol pemicu interaktif dan panel inspeksi transisi state riil.
   - **UI Spike:** Maksimal 3 varian struktural pada rute yang sama via parameter `?variant=X` dengan floating pill switcher bar.

3. **MANAJEMEN SIKLUS HIDUP THROWAWAY:**
   - Simpan kode spike di cabang eksperimen `prototype/<topik>` sebagai sumber primer empiris.
   - Jangan pernah me-merge kode spike langsung ke `main`. Angkat hanya logika teruji yang bersih ke kode produksi.
</PROTOTYPE_SPIKE_ENGINE>
