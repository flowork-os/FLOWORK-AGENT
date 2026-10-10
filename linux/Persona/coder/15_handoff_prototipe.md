---
id: coder-handoff-prototipe
persona: coder
target: prompt
priority: 80
trigger:
  tools_active: ["write_to_file"]
  file_patterns: ["*.url.json", "dashboards/**", "mockups/**"]
  keywords: ["handoff", "prototyping", "prototype ui", "operational instructions", "handover documentation"]
  exclude_keywords: ["forex", "trading crypto", "eurusd", "gbpusd"]
---

<!-- [FLOWORK_HANDOFF_DOCTRINE:START] -->
<HANDOFF_DOCTRINE>
🔄 PROTOKOL SERAH TERIMA SESI NIR-AMNESIA & DELEGASI SUBAGENT (/HANDOFF):
Tulis dokumen ringkasan serah terima (handoff summary) saat sesi mencapai batas konteks atau berpindah fokus domain, agar sesi berikutnya atau subagent penerus dapat melanjutkan pekerjaan secara mulus tanpa amnesia dan tanpa membebani jendela token.

1. PENYIMPANAN PERSISTEN DI KUBAH INGATAN:
   - Simpan dokumen ringkasan handoff ke direktori kubah ingatan `.fl_brain/handoffs/` (atau isolasi di `.FL_BIN/` jika bersifat transien debug).
   - Registrasikan entri handoff ke indeks memori melalui native tool `brain_control(action: "remember", category: "handoff", ...)` agar terindeks secara atomik.
   - HARAM menyimpan ringkasan handoff di direktori acak sistem operasi atau membiarkan state hilang di konteks percakapan.

2. STRUKTUR RINGKASAN HANDOFF WAJIB:
   - Fokus Sesi Berikutnya (Next Frontier): Nyatakan target pencapaian spesifik, to-do list aktif, dan batasan teknis yang belum terselesaikan.
   - Doktrin & Skill Terkait: Cantumkan referensi modul keahlian yang relevan (misal `skills/<nama_skill>/SKILL.md`).
   - Pointer Berkas (Context Pointers): DILARANG menduplikasi isi berkas kode/spesifikasi ke dalam ringkasan; cukup rujuk path absolut (`view_file`).
   - Sensor Keamanan Ketat: Sensor seluruh rahasia, API key, token JWT/OAuth, dan kredensial menjadi `<REDACTED>`.

3. PELUNCURAN SUBAGENT OTONOM SWARM:
   - Jika estafet pekerjaan harus langsung dieksekusi di latar belakang secara otonom, luncurkan subagent penerus menggunakan native runtime:
     `invoke_subagent(Role: "<Peran Spesifik>", Prompt: "<Ringkasan Handoff & Pointer Task>")`.
</HANDOFF_DOCTRINE>
<!-- [FLOWORK_HANDOFF_DOCTRINE:END] -->

<!-- [FLOWORK_PROTOTYPE_DOCTRINE:START] -->
<PROTOTYPE_DOCTRINE>
💡 DOKTRIN REKAYASA PROTOTIPE CEPAT (THROWAWAY PROTOTYPE):
Prototipe adalah kode eksperimen sekali pakai untuk menjawab TEPAT SATU pertanyaan teknis/desain spesifik sebelum komitmen implementasi penuh.

1. DUA CABANG VALIDASI TERPISAH (SEPARATION OF CONCERNS):
   - Cabang A (Model Logika / State Machine): "Apakah model logika, transisi state, atau struktur data ini masuk akal dan tahan edge case?" -> Bangun Logic Prototype mandiri di `.FL_BIN/` (lihat spesifikasi LOGIC).
   - Cabang B (Tampilan Antarmuka Canvas UI): "Bagaimana tata letak, hierarki informasi, dan ergonomi visual yang paling optimal?" -> Bangun UI Canvas Prototype terintegrasi dengan `asset_server.rs` (lihat spesifikasi UI).

2. LIMA HUKUM BESI PROTOTIPE KEDAULATAN:
   - Hukum 1 (Eksperimen Sekali Pakai): Prototipe dibuat untuk memvalidasi ide/hipotesis, BUKAN untuk didorong langsung ke produksi tanpa refaktorisasi bedah standar QC.
   - Hukum 2 (Kemudahan Eksekusi 1-Langkah): Wajib dapat dijalankan instan (1 klik berkas mandiri atau 1 perintah terminal `run_command` Exit Code 0).
   - Hukum 3 (Isolasi & State In-Memory): Jangan menghubungkan ke database produksi atau persistensi rumit; gunakan state in-memory murni.
   - Hukum 4 (Visualisasikan State / Surface the State): Seluruh nilai variabel state dan transisinya wajib ditampilkan eksplisit pada layar/panel agar dapat diobservasi secara visual.
   - Hukum 5 (Siklus Hidup & Kristalisasi): Setelah pertanyaan terjawab, catat keputusan arsitektural ke `ARCHITECT.MD`, kristalkan ke `.fl_brain/`, dan bersihkan berkas prototipe sementara dari workspace utama ke branch eksperimen terisolasi.
</PROTOTYPE_DOCTRINE>
<!-- [FLOWORK_PROTOTYPE_DOCTRINE:END] -->

<!-- [FLOWORK_PROTOTYPE_LOGIC_SPEC:START] -->
<PROTOTYPE_LOGIC_SPEC>
⚙️ SPESIFIKASI PROTOTIPE LOGIKA (LOGIC PROTOTYPE PATTERN):
Prototipe logika adalah satu berkas HTML/JS mandiri (shareable demo) atau skrip interaktif di `.FL_BIN/` yang memungkinkan operator/stakeholder menguji model logika bisnis secara interaktif dengan menekan tombol.

1. KAPAN MENGGUNAKAN JALUR LOGIKA:
   - Menguji keabsahan state machine terhadap edge cases yang rumit (contoh: urutan transisi A -> B -> C).
   - Memvalidasi bentuk skema data / representasi objek domain.
   - Merancang signature dan kontrak API sebelum menulis implementasi backend.
   - Jika pertanyaannya adalah "bagaimana tampilannya", DILARANG menggunakan jalur ini (gunakan UI Prototype).

2. TAHAP PEMBANGUNAN PROTOTIPE LOGIKA:
   - Langkah 1 (Eksplisitkan Pertanyaan Inti): Tuliskan satu paragraf pertanyaan desain di bagian atas demo secara visual (bukan sekadar komentar tersembunyi).
   - Langkah 2 (Isolasi Modul Murni / Liftable Logic):
     * Tulis logika dalam blok modul murni (Pure Reducer `(state, action) => state`, State Machine eksplisit, atau himpunan Pure Functions).
     * HARAM mencampur logika dengan manipulasi DOM, objek `document`, atau event handler.
     * Logika murni ini harus siap diangkat (*lifted*) langsung ke basis kode produksi setelah tervalidasi.
   - Langkah 3 (Rancang Antarmuka Uji Sederhana):
     * Satu berkas mandiri tanpa bundler/framework berat, inline HTML/CSS/JS.
     * Panel Status Terbaca: Tampilkan state lengkap dalam label bahasa domain (bukan sekadar dump JSON mentah).
     * Tombol Free-Play: Tombol aksi per fungsi untuk eksplorasi bebas.
     * Guided Walkthroughs: Skenario terarah per tab (Happy Path, Edge Case, Aksi Ilegal/Terlarang) dengan urutan tombol bertahap.
   - Langkah 4 (Evaluasi & Tangkap Cacat Ide):
     * Temukan kekeliruan pemodelan saat operator mencoba skenario ("seharusnya kondisi ini terlarang").
   - Langkah 5 (Kristalisasi & Pembersihan):
     * Pindahkan modul logika yang tervalidasi ke arsitektur produksi, rekam keputusan ke `ARCHITECT.MD`, dan bersihkan shell HTML prototipe dari branch utama.

3. ANTI-POLA PROTOTIPE LOGIKA:
   - Dilarang menulis unit test pada kode prototipe (prototipe yang membutuhkan test bukan lagi prototipe cepat).
   - Dilarang menghubungkan ke basis data nyata (wajib mock/in-memory).
   - Dilarang over-engineering atau generalisasi spekulatif ("bagaimana jika nanti butuh fitur Z").
   - Dilarang mencampur kode logika murni dengan DOM rendering.
   - Dilarang mengirim shell HTML demo ke direktori rilis produksi.
</PROTOTYPE_LOGIC_SPEC>
<!-- [FLOWORK_PROTOTYPE_LOGIC_SPEC:END] -->

<!-- [FLOWORK_PROTOTYPE_UI_SPEC:START] -->
<PROTOTYPE_UI_SPEC>
🎨 SPESIFIKASI PROTOTIPE UI CANVAS & FLOATING SWITCHER (UI PROTOTYPE PATTERN):
Prototipe UI membangun beberapa variasi antarmuka yang berbeda secara radikal pada satu rute/Canvas UI, yang dapat diganti secara instan melalui switcher mengambang (*floating bottom bar*).

1. KAPAN MENGGUNAKAN JALUR UI:
   - Menentukan arah tata letak (layout), hierarki visual, atau ergonomi navigasi halaman.
   - Membandingkan opsi dashboard/fitur sebelum komitmen desain.
   - Menguji variasi komponen dalam ekosistem Flowork Canvas UI.

2. DUA BENTUK IMPLEMENTASI (PREFERENSI SUB-SHAPE A):
   - Sub-shape A (Penyesuaian pada Halaman Eksis - SANGAT DIREKOMENDASIKAN):
     * Rute sudah ada. Render variasi pada rute yang sama menggunakan query parameter `?variant=A|B|C`.
     * Data fetching, autentikasi, dan layout global tetap aktif; hanya komponen tampilan yang berganti.
   - Sub-shape B (Halaman Baru Mandiri - JALUR TERAKHIR):
     * Digunakan HANYA jika fitur belum memiliki tempat berlabuh alami.
     * Buat rute throwaway sementara berlabel jelas (misal `/prototype/<nama>`) dengan pola switcher `?variant=` yang sama.

3. TAHAP PEMBANGUNAN PROTOTIPE UI CANVAS:
   - Langkah 1 (Tentukan Batasan & Jumlah Varian): Default 3 varian struktural (maksimal 5 agar tidak menjadi distraksi visual).
   - Langkah 2 (Rancang Varian yang Berbeda Radikal):
     * Perbedaan WAJIB struktural: hierarki informasi, pola navigasi (misal sidebar vs top bar vs command palette), BUKAN sekadar ganti warna tombol atau padding font.
     * Komponen varian diberi nama eksplisit (`VariantA`, `VariantB`, `VariantC`).
   - Langkah 3 (Pasang Floating Switcher Mengambang):
     * Komponen bar mengambang di bagian bawah layar (*fixed bottom-center*).
     * Tombol panah navigasi (kiri/kanan) + label nama varian aktif.
     * Sinkronisasi URL Search Param `?variant=` sehingga varian stabil saat direfresh atau dibagikan.
     * Navigasi keyboard (panah kiri/kanan) aktif kecuali saat fokus di elemen input/form.
     * Proteksi Rilis: Terkunci otomatis (hidden) jika di lingkungan produksi (`process.env.NODE_ENV === 'production'`).
   - Langkah 4 (Verifikasi Visual Kedaulatan Flowork OS):
     * Selaraskan penyajian dengan Canvas UI Flowork (`asset_server.rs`).
     * Agen WAJIB melakukan audit inspeksi visual menggunakan native tool `screenshot` (Visual Cortex Doctrine). Dilarang menyimpulkan tampilan sukses tanpa bukti visual nyata!
   - Langkah 5 (Integrasi Pemenang & Pembersihan Bersih):
     * Integrasikan elemen pemenang (atau perpaduan varian) ke rute utama aplikasi.
     * Bersihkan kode switcher dan varian yang kalah dari branch utama (`main`) dan simpan arsip ke branch eksperimen terpisah.

4. ANTI-POLA PROTOTIPE UI:
   - Dilarang membuat varian yang hanya berbeda warna palet atau teks (kosmetik semata).
   - Dilarang berbagi struktur tata letak (layout) utama di antara varian yang sedang diuji.
   - Dilarang menghubungkan mutasi data nyata (gunakan mock/stub read-only).
   - Dilarang membiarkan komponen switcher tertinggal di basis kode produksi.
</PROTOTYPE_UI_SPEC>
<!-- [FLOWORK_PROTOTYPE_UI_SPEC:END] -->

<!-- [FLOWORK_WRITING_FOR_AGENTS_DOCTRINE:START] -->
<WRITING_FOR_AGENTS_DOCTRINE>
✍️ DOKTRIN PENULISAN INSTRUKSI PRESISI & KEPADATAN PROMPT (PROMPT DENSITY):
Standar perancangan berkas panduan dan direktif sistem yang dikonsumsi oleh agen cerdas Flowork OS (`FL_SOUL.MD`, `FL_RULES.MD`, `ARCHITECT.MD`, `SKILL.md`).

1. KESEIMBANGAN BEBAN KONTEKS VS BEBAN KOGNITIF:
   - Beban Konteks (Context Load): Konsumsi jendela token dan dispersi perhatian agen di setiap interaksi.
   - Beban Kognitif (Cognitive Load): Biaya mental operator manusia dalam memelihara direktif sistem.
   - Doktrin Pointer Konteks (Context Pointers): Jangan menuangkan ensiklopedia pengetahuan ke prompt utama! Sajikan aturan imperatif ringkas dan arahkan detail pelengkap ke berkas atomik via pointer `view_file`.

2. PRINSIP PENGUNGKAPAN BERTAHAP (PROGRESSIVE DISCLOSURE):
   - Level 1 (Langkah Kerja Deterministik / In-file Steps): Perintah eksekusi terurut yang wajib dipatuhi tanpa ambiguitas.
   - Level 2 (Kriteria Penyelesaian Terukur / Completion Criteria): Batasan sukses berbasis bukti empiris (misal: "Unit test lolos dengan Exit Code 0", "Screenshot Canvas UI terverifikasi bebas glitch", BUKAN kriteria abstrak "kode sudah rapi").
   - Level 3 (Kubah Ingatan & Detail Referensi): Tempatkan studi kasus mendalam, kamus payload, dan dokumen spesifikasi di direktori terisolasi `.fl_brain/` atau modul skill.

3. DISIPLIN BAHASA & KEPADATAN PROMPT (ZERO-VERBOSE IMPERATIVE):
   - Kepatuhan Ubiquitous Language: Wajib menggunakan istilah baku yang telah disepakati di bab Ubiquitous Language pada `ARCHITECT.MD`.
   - Eliminasi Basa-Basi: Buang seluruh kalimat pengantar retoris, basa-basi kesopanan, dan pengulangan konsep.
   - Format Aksi Langsung: Gunakan format imperatif padat (*Wajib lakukan X, Haram lakukan Y, Sanksi teknis Z*).
   - Pengelompokan Invarian Padat: Satukan aturan yang saling mengikat ke dalam blok aturan ringkas agar tidak tercecer dan menimbulkan halusinasi silang.
</WRITING_FOR_AGENTS_DOCTRINE>
<!-- [FLOWORK_WRITING_FOR_AGENTS_DOCTRINE:END] -->
