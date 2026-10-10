---
id: plugin-architect-gui-craftsmanship
persona: plugin-architect
target: prompt
priority: 85
cmd: ["/design-gui", "/gui"]
file_patterns: ["plugins/**/gui/**", "plugins/**/*.html", "plugins/**/*.css", "plugins/**/gui/app.js"]
trigger:
  keywords: ["design-gui", "canvas ui", "webview", "gui craftsmanship", "scoped css", "dark mode", "frontend plugin", "ui co-creation", "html gui"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 🎨 CANVAS GUI CRAFTSMANSHIP & INTERACTIVE WEBVIEW

Ketika merancang atau menyempurnakan antarmuka visual plugin (`gui/index.html`, `gui/style.css`, `gui/app.js`), patuhi standar ketat berikut:

---

### 1. ATURAN 100% STRICT ENGLISH UI
- Seluruh teks antarmuka: judul (`<h1>`), nama tombol (`<button>`), label formulir (`<label>`), placeholder (`placeholder="..."`), tooltip, badge status, dan dialog konfirmasi **WAJIB 100% BAHASA INGGRIS**.
- Bahasa Indonesia DILARANG KERAS di antarmuka publik agar plugin berstandar industri global.

---

### 2. ISOLASI SCOPED CSS (`#<plugin_id>-root`)
Untuk mencegah tabrakan style dengan Canvas Host, bungkus seluruh elemen root di HTML dan selektor di CSS:
```html
<div id="chess-root" class="plugin-canvas-wrapper">
  <!-- Plugin UI Components -->
</div>
```

```css
#chess-root {
  --bg-primary: #0a0f1d;
  --bg-secondary: #111827;
  --bg-card: #1e293b;
  --border-color: rgba(0, 255, 170, 0.2);
  --accent-cyan: #00ffaa;
  --accent-blue: #38bdf8;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  color: var(--text-primary);
  background: var(--bg-primary);
  height: 100vh;
  box-sizing: border-box;
}

#chess-root button.btn-primary {
  background: var(--accent-cyan);
  color: #000;
  border: none;
  font-weight: 600;
  cursor: pointer;
  border-radius: 4px;
}
```

---

### 3. PROTOKOL SINKRONISASI REAL-TIME (CO-CREATION ENGINE)
Plugin di Flowork Canvas bukan sekadar halaman statis, melainkan meja kerja kolaborasi:
1. **Status Polling & Server-Sent Events (SSE):**
   - Di `gui/app.js`, sambungkan `EventSource('/api/events')` atau WebSocket untuk menerima pembaruan instan saat AI Agent memanipulasi data di backend.
2. **Action Dispatcher:**
   - Setiap interaksi pengguna (klik, drag-and-drop, input form) mengirim mutasi state via `POST /api/action` atau endpoint REST terkait.
3. **Optimistic UI Updates:**
   - Perbarui antarmuka secara instan saat pengguna bertindak, lalu rekonsiliasi dengan konfirmasi backend.
