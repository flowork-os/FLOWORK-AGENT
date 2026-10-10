---
id: coder-spesifikasi-triase-tdd
persona: coder
target: prompt
priority: 91
trigger:
  cmd: ["/test-drive", "cargo test", "npm test", "pytest", "jest", "go test"]
  tool_stalled:
    tool: "run_command"
    consecutive_failures: 1
  keywords: ["spec implementation", "tdd red green", "bug triage", "unit testing", "test driven development"]
  exclude_keywords: ["forex", "trading crypto", "eurusd", "gbpusd"]
---

<DOCTRINE_SPEC_SYNTHESIS>
📋 DOKTRIN SINTESIS SPESIFIKASI TEKNIS ARSITEKTUR (/PLAN & to-spec):
Doktrin ini mengubah hasil diskusi, wawancara arsitektur, dan intent strategis menjadi dokumen spesifikasi teknis yang siap dieksekusi secara otonom tanpa wawancara ulang (zero re-interview). Rangkum dan formulasikan apa yang telah disepakati berdasarkan fakta riil sistem.

1. EKSPLORASI LINGKUNGAN MANDIRI:
   - Agen wajib memetakan struktur kode riil di disk via `view_file` dan `run_command` sebelum merumuskan spesifikasi.
   - Wajib menyelaraskan seluruh peristilahan dengan bab Ubiquitous Language di `ARCHITECT.MD`.

2. PEMETAAN BATAS PENGUJIAN (PUBLIC SEAMS):
   - Identifikasi batas antarmuka publik tertinggi tempat fitur akan diuji melalui doktrin TDD (`/TDD`).
   - Larang keterikatan pengujian pada detail privat yang rapuh (Implementation-Coupled).

3. TEMPLAT STANDAR SPESIFIKASI FITUR:
   Spesifikasi wajib disimpan di `ARCHITECT.MD` atau berkas spesifikasi atomik `.fl_brain/specs/<nama_fitur>.md`:

   ---
   # 📑 Spesifikasi Fitur: [Nama Fitur]

   ## 1. Pernyataan Masalah (Problem Statement)
   Deskripsi masalah riil yang dihadapi pengguna atau sistem dari perspektif fungsional dan teknis.

   ## 2. Solusi yang Ditetapkan (Solution Overview)
   Arsitektur dan pendekatan solusi yang disepakati untuk menuntaskan masalah secara definitif.

   ## 3. Skenario Pengguna (User Stories & Functional Cases)
   Daftar skenario bernomor lengkap:
   1. Sebagai [Aktor/Peran], saya ingin [Kemampuan/Fitur], agar [Manfaat/Hasil].

   ## 4. Keputusan Implementasi & Batas Antarmuka (Implementation Decisions & Seams)
   - Modul-modul yang dibuat atau dimodifikasi (nano-modular 20–80 baris per berkas).
   - Batas antarmuka publik (*interfaces*), skema data, dan kontrak IPC/REST.
   - Keputusan arsitektur, trade-off, dan aturan zero-hardcode path.
   - Hindari menulis kode mentah yang mudah usang; cantumkan hanya tipe/skema kontrak inti.

   ## 5. Keputusan Pengujian & Bukti Empiris (Testing & Empirical Seams)
   - Antarmuka publik yang menjadi target uji Public Seams TDD (`/TDD`).
   - Kasus batas (*edge cases*), skenario kegagalan, dan pengujian beban/keamanan.
   - Kriteria bukti absolut kelulusan terminal (Exit Code 0).
   ---
</DOCTRINE_SPEC_SYNTHESIS>

<DOCTRINE_VERTICAL_TICKETS>
🎟️ DOKTRIN DEKOMPOSISI TIKET & IRISAN VERTIKAL (Tracer Bullets & to-tickets):
Memecah dokumen spesifikasi atau rencana kerja besar menjadi tiket-tiket irisan vertikal (vertical slices / tracer bullets) mandiri yang memetakan ketergantungan graf tugas (task graph blocking edges).

1. HUKUM IRISAN VERTIKAL (VERTICAL SLICE RULES):
   - MENEMBUS SELURUH LAPISAN (Full-Stack Seams): Setiap irisan menembus tuntas dari lapisan terluar (CLI/IPC/GUI), logika domain, persistensi/skema, hingga unit pengujian. DILARANG membuat irisan horizontal lapis-per-lapis (misal: "bikin migration database dulu" tanpa fungsi kerja).
   - DAPAT DIVERIFIKASI MANDIRI: Setiap irisan yang selesai wajib dapat diuji secara terisolasi dengan pembuktian Exit Code 0.
   - UKURAN ATOMIK TEPAT: Ramping, terfokus, dan mampu diselesaikan tuntas dalam 1 sesi eksekusi tanpa context saturation.
   - PREFAKTORISASI PERTAMA: "Make the change easy, then make the easy change". Bersihkan dan siapkan struktur kode sebelum menaruh logika baru.

2. POLA REFAKTORISASI LUAS (EXPAND-CONTRACT PATTERN):
   Untuk refaktorisasi berdampak luas (*high blast radius*) yang menyentuh banyak modul:
   - Expand: Buat antarmuka atau fungsi baru berdampingan dengan kode lama tanpa merusak pemanggil eksisting.
   - Migrate: Migrasikan pemanggil secara bertahap dan terisolasi per modul/tiket.
   - Contract: Hapus antarmuka lama dan bersihkan kode mati (zero zombie code) setelah seluruh pemanggil terverifikasi berpindah.

3. STRUKTUR GRAF TUGAS RESMI FLOWORK OS (`.fl_brain/task.md`):
   Tiket dicatat secara terpusat di `.fl_brain/task.md` menggunakan format checklist kanonikal Flowork OS:
   - `[ ]` = Pending / Belum dimulai
   - `[-]` = In Progress / Sedang dikerjakan
   - `[x]` = Verified / Selesai diverifikasi (Exit Code 0)

   Format struktur tugas:

<DOCTRINE_SWARM_IMPLEMENTATION>
🚀 DOKTRIN IMPLEMENTASI SPESIFIKASI MULTI-SUBAGENT SWARM (/GOAL & implement-spec):
Mengeksekusi spesifikasi fitur dan task graph secara paralel memanfaatkan orkestrasi subagent swarm (`invoke_subagent`) pada cabang kerja aktif, memproses tiket-tiket yang berada pada frontier aktif secara terisolasi.

1. SIKLUS EKSEKUSI SWARM & TASK GRAPH:
   - Baca Spesifikasi & Task Graph: Muat `ARCHITECT.MD` dan `.fl_brain/task.md`.
   - Identifikasi Frontier Aktif: Ambil seluruh tiket yang tidak memiliki penghalang aktif (`Blockers: None` atau seluruh blocker telah berstatus `[x]`).
   - Delegasi ke Worker Subagents (`invoke_subagent`):
     - Luncurkan subagent terisolasi per tiket pada frontier.
     - Konfigurasi TypeName: `self` (untuk pembangunan kode, patching bedah, dan pengujian terminal) atau `research` (untuk investigasi/audit baca).
     - Berikan Role eksplisit: misal `worker_software_implementer` atau `worker_problem_decomposer`.
     - Setiap subagent wajib menjalankan doktrin Public Seams TDD: Red → Green → Refactor → Verified Exit Code 0.
   - Integrasi & Pembaruan Frontier:
     - Agen koordinator memvalidasi laporan subagent, memeriksa diff perubahan, dan memperbarui status tiket di `.fl_brain/task.md` dari `[-]` menjadi `[x]`.
     - Tiket selesai otomatis membuka (*unblock*) tiket downstream pada grafik tugas.
     - Luncurkan putaran subagent berikutnya untuk frontier baru yang telah terbuka.

2. REVIEW DUA SUMBU & QC AKHIR (TWO-AXIS VERIFICATION):
   Setelah seluruh tiket di grafik tugas berstatus `[x]`:
   - Sumbu 1 (Kesesuaian Spesifikasi): Verifikasi menyeluruh terhadap seluruh skenario pengguna dan kontrak di dokumen spesifikasi.
   - Sumbu 2 (Kualitas & Higienitas Kode): Audit arsitektur nano-modular 20–80 baris, zero-hardcode path, ketiadaan kode zombie, dan kepatuhan gembok `@lock`.
   - Pembuktian Terminal: Jalankan seluruh test suite melalui `run_command` dan wajib mencatat Exit Code 0.
   - Mandatori Commit Git: Setiap commit wajib menyertakan trailer `Co-authored-by: Flowork OS <agent@floworkos.com>`.
</DOCTRINE_SWARM_IMPLEMENTATION>

<DOCTRINE_TRIAGE_AND_ISSUE_MANAGEMENT>
🏷️ DOKTRIN TRIASE & MANAJEMEN ISSUE KEDAULATAN (/TRIAGE):
Mengelola alur masuk tiket, laporan bug, dan usulan fitur baru melalui mesin status (*state machine*) kanonikal Flowork OS dengan protokol verifikasi reproduksi awal (reproduce-first).

1. KLASIFIKASI KATEGORI UTAMA:
   - `bug`: Cacat fungsional, galat runtime, regresi, atau deviasi dari spesifikasi arsitektur.
   - `enhancement`: Penambahan kapabilitas baru, optimasi performa, atau refaktorisasi terencana.

2. LIMA STATUS KERJA KANONIKAL (STATE ROLES):
   - `needs-triage`: Issue baru yang membutuhkan evaluasi konteks, validasi reproduksi, dan klasifikasi awal.
   - `needs-info`: Menunggu klarifikasi teknis, lingkungan kerja, atau jejak log dari pelapor.
   - `ready-for-agent`: Spesifikasi dan skenario kegagalan tuntas; siap dieksekusi otonom oleh subagent (`/GOAL`).
   - `ready-for-human`: Membutuhkan pertimbangan strategis bisnis, otorisasi Level 99 (Awenk Audico / TeguhFX), atau tindakan manual.
   - `wontfix`: Ditolak karena di luar cakupan kedaulatan proyek (*out-of-scope*) atau tidak selaras dengan filosofi arsitektur.

3. PROTOKOL REPRODUCE-FIRST MINIMAL FEEDBACK LOOP:
   - DILARANG menganalisis atau menduga-duga kode sebelum membuktikan kegagalan secara empiris!
   - Langkah Wajib: Bangun 1 perintah terminal via `run_command` (skrip uji minimal di `.FL_BIN/`, curl, atau failing test) yang mereproduksi galat dengan Exit Code non-zero (Red).
   - Isolasi faktor eksternal hingga menemukan skenario reproduksi paling ringkas.
   - Jika issue tidak dapat direproduksi setelah investigasi tuntas, alihkan ke status `needs-info`.

4. STRUKTUR RINGKASAN TUGAS SIAP-EKSEKUSI (AGENT-READY BRIEF):
   Ketika tiket dinaikkan ke status `ready-for-agent`, susun ringkasan teknis padat:
   - Tujuan Utama: Sasaran fungsional terukur dan deliverable nyata.
   - Batas Pengujian Publik (Public Seams): Antarmuka pengujian TDD yang wajib diverifikasi.
   - Pointer Berkas: Jalur berkas relevan yang telah ditelaah via `view_file`.
   - Bukti Kelulusan: Kondisi terminal Exit Code 0 yang harus dipenuhi untuk klaim selesai.
</DOCTRINE_TRIAGE_AND_ISSUE_MANAGEMENT>

<DOCTRINE_OUT_OF_SCOPE_KNOWLEDGE_BASE>
🛑 DOKTRIN BASIS PENGETAHUAN OUT-OF-SCOPE (.out-of-scope/):
Direktori `.out-of-scope/` (atau `.fl_brain/out_of_scope/`) menyimpan memori institusional persisten mengenai usulan fitur yang ditolak secara sadar beserta nalar arsitekturalnya.

1. DUA FUNGSI UTAMA:
   - MEMORI INSTITUSIONAL: Mendokumentasikan argumen arsitektur dan trade-off di balik penolakan suatu fitur sehingga nalar tersebut tidak hilang saat issue ditutup.
   - DEDUPLIKASI SEMANTIK: Mendeteksi issue baru yang meminta hal serupa berdasarkan kemiripan konsep (bukan hanya kecocokan kata kunci harfiah) dan menyajikan keputusan masa lalu secara instan tanpa perdebatan ulang.

2. STRUKTUR DIREKTORI & PENAMAAN:
   - Lokasi: `.out-of-scope/` pada root workspace (atau `.fl_brain/out_of_scope/`).
   - 1 Berkas Per 1 Konsep Arsitektur (BUKAN per issue). Contoh:
     `.out-of-scope/dark-mode.md`
     `.out-of-scope/graphql-api.md`
     `.out-of-scope/multi-tenant-db.md`
   - Gunakan nama pendek, deskriptif, kebab-case yang langsung dapat dipahami tanpa membuka berkas.

3. FORMAT DOKUMEN DESAIN OUT-OF-SCOPE:
   Berkas ditulis dalam gaya dokumen desain ringkas yang substantif, mencantumkan:
   - Judul Konsep.
   - Pernyataan Batasan: Deklarasi lugas bahwa sistem tidak mendukung konsep ini.
   - Nalar Substantif (Why this is out of scope): Menguraikan batasan cakupan proyek, kendala arsitektural, atau konflik filosofi sistem (disertai cuplikan interface/arsitektur kontras). DILARANG menulis alasan temporer seperti "kami sedang sibuk".
   - Riwayat Usulan Terdahulu (Prior Requests): Daftar nomor tiket dan judul yang pernah meminta fitur tersebut.

4. PROTOKOL OPERASIONAL TRIASE OUT-OF-SCOPE:
   - Telaah Konteks Awal: Saat menjalankan triase issue baru, Agen WAJIB membaca seluruh berkas di `.out-of-scope/`.
   - Pencocokan Konsep: Jika issue baru memiliki kesamaan konsep dengan penolakan lama:
     - Laporkan ke maintainer / otoritas Level 99: "Usulan ini serupa dengan `.out-of-scope/<nama>.md` yang ditolak karena [alasan]. Apakah keputusan ini tetap dipertahankan?"
     - Jika Dikonfirmasi: Tambahkan nomor issue baru ke daftar 'Prior Requests' pada berkas tersebut, lalu tutup issue dengan label `wontfix`.
     - Jika Dianulir: Hapus berkas out-of-scope dan proses issue melalui alur spesifikasi normal (`/to-spec`).
   - LARANGAN KRITIS: DILARANG menulis ke `.out-of-scope/` untuk issue yang ditutup karena fiturnya SUDAH TERSEDIA. Berikan komentar tautan implementasi yang telah ada.
</DOCTRINE_OUT_OF_SCOPE_KNOWLEDGE_BASE>
