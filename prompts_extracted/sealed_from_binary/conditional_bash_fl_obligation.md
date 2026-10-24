<!-- [FL_INDEX: bash_fl_obligation, run_command, mandatory_fl_index, terminal_guardrail, zero_tolerance | purpose="Directive enforcing mandatory FL_INDEX on any bash or terminal code mutation"] -->
<!-- CANONICAL_TRIGGER: bash_fl_obligation | TOOLS: run_command -->
<CONDITIONAL_BASH_FL_INDEX_OBLIGATION_DIRECTIVE>
1. KEWAJIBAN MUTLAK FL_INDEX SAAT MUTASI KODE & FILE LEWAT BASH (MANDATORY FL_INDEX IN BASH):
   - Setiap perintah bash atau terminal (`run_command`) yang membuat atau memodifikasi file kode (via heredoc `cat <<`, echo `> / >>`, `tee`, script inline, compiler, atau patch), WAJIB menyertakan tag semantic index `FL_INDEX` pada baris awal file:
     `[FL_INDEX: keywords="..." | purpose="..."]`
   - File tanpa FL_INDEX dianggap sebagai file liar yang melanggar standar sovereign indexing Flowork OS.

2. KEBIJAKAN PENEGAKAN KEGAGALAN EKSEKUSI (ZERO TOLERANCE ON MISSING FL_INDEX):
   - Jika suatu operasi pembuatan atau modifikasi file dilakukan melalui bash/terminal tanpa menyematkan atau mempertahankan `FL_INDEX`, status eksekusi secara arsitektural DIANGGAP GAGAL dan TIDAK BOLEH diklaim selesai.
   - Segera lakukan inspeksi file hasil eksekusi; jika `FL_INDEX` belum terpasang, perbaiki file saat itu juga sebelum melanjutkan ke langkah berikutnya.

3. DISIPLIN KATA KUNCI FL_INDEX:
   - Nilai `keywords` dalam tag `FL_INDEX` wajib berisi kata kunci teknis standar industri (bahasa Inggris) minimal 3-5 kata kunci yang akurat dan spesifik, menggambarkan fungsi, arsitektur, dan domain logika file tersebut.
   - Hindari kata kunci generik seperti "file", "test", atau "code". Gunakan terminologi definitif agar Sovereign Skill Radar dan Semantic Xref dapat memetakan file secara deterministik.
</CONDITIONAL_BASH_FL_INDEX_OBLIGATION_DIRECTIVE>
