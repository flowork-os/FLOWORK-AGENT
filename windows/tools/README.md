# 🛠️ FLOWORK OS — DYNAMIC EXTERNAL TOOLS REGISTRY (`tools/`)

Direktori ini adalah gerbang ekspansi alat bantu (tools) kedaulatan di luar Blackbox Binary.
Setiap tool baru yang diletakkan di dalam folder ini otomatis dapat ditemukan oleh MR. FLOW menggunakan fungsi `flow_search_tools`.

## Format Standar Pembuatan Tool:
Setiap tool diletakkan di dalam foldernya masing-masing: `tools/<nama_tool>/`

Wajib menyertakan `manifest.json`:
```json
{
  "name": "nama_tool",
  "category": "utility | devops | document | finance | media | security",
  "description": "Penjelasan fungsi tool dan kapan harus digunakan",
  "command": "bash tool.sh arg1 arg2 (atau: python3 tool.py / node tool.js)",
  "entry": "tool.sh",
  "author": "Nama Pembuat",
  "version": "1.0.0",
  "tags": ["keyword1", "keyword2"],
  "parameters": {
    "param1": {
      "type": "string",
      "description": "Keterangan parameter"
    }
  }
}
```

MR. FLOW akan mencari tool di folder ini sebelum menyatakan tidak mampu menyelesaikan suatu tugas teknis.
