---
name: semantic_search
title: Flowork OS Sovereign Semantic Search Tool
version: 1.0.0
description: Fast local embedding vector search across .fl_brain and workspace files powered by FastEmbed ONNX runtime.
category: developer
keywords:
  - semantic_search
  - vector_search
  - embeddings
  - onnx
  - fastembed
  - fl_brain
  - memory_retrieval
  - local_ai
  - cosine_similarity
  - sovereign_tool
---

# 🔍 Semantic Search Tool (Sovereign Neural Vector Engine)

## Bab 1: Gambaran Umum & Doktrin (Overview & Doctrines)
Tool `semantic_search` merupakan mesin pencari semantik vektor lokal berbasis embedding neural network (ONNX runtime via FastEmbed). Mesin ini beroperasi 100% offline di host lokal tanpa dependensi API eksternal atau kebocoran data rahasia.

Dirancang untuk mengindeks dan mencari dokumen `.fl_brain`, dokumentasi teknis, serta file kode workspace dengan pemahaman makna linguistik melebihi pencarian kata kunci leksikal murni.

## Bab 2: Antarmuka & Parameter (Interface & Parameters)
- `query` (string, wajib): Kueri teknis atau pertanyaan bahasa alami.
- `target` (string, opsional, default: `.fl_brain`): Folder atau subfolder target yang akan diindeks dan dicari.
- `model` (string, opsional, default: `bge-small`): Pilihan model embedding (`bge-small`, `minilm-l6`, `all-minilm-l12`).
- `top_k` (integer, opsional, default: `5`): Jumlah hasil teratas yang relevan secara semantik.

## Bab 3: Mekanisme & Eksekusi (Execution Vector)
Tool dieksekusi secara native melalui wrapper Node.js `main.mjs` yang memanggil binary Rust berkinerja tinggi `flowork-semantic`:
```bash
node tools/semantic_search/main.mjs --query "sqlite concurrency" --target ".fl_brain" --top-k 5
```

## Bab 4: Penanganan Galat & Standar Keamanan (Security & Error Handling)
- Mematuhi doktrin Zero Leakage dan Multi-OS Portability.
- Binary dikompilasi secara deterministik dalam mode `--release`.
- Model ONNX di-cache di dalam `.flowork/cache/embeddings` secara terisolasi.
