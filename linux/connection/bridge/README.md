# ⚡ FLOWORK OS — UNIVERSAL BRIDGE MODULE

This directory contains the Nano-Plug implementation of the **Bilateral Protocol Translator and Upstream Bridge** for Flowork OS.

### Module Map:
- `bridge_config.js`: Loads settings from `.env` (`FLOWORK_ROUTER_MODE`, `FLOWORK_CUSTOM_PROVIDER`, etc.).
- `bridge_dispatcher.js`: Intercepts IDE AI inference and mock calls when mode is `custom`.
- `mock_engine.js`: Implements pre-flight mocking (`:loadCodeAssist`, `:retrieveUserQuota`, `:fetchAvailableModels`).
- `translators/gemini_to_openai.js`: Translates Google CCPA/Gemini AST requests to OpenAI Chat Completions.
- `translators/openai_to_gemini.js`: Streaming SSE transformer (OpenAI chunks to Gemini chunks).
- `translators/schema_sanitizer.js`: Sanitizes Gemini uppercase schema types to standard lowercase JSON schema.
- `providers/openai_driver.js`: Streaming HTTP/HTTPS driver for upstream endpoints.

For full developer instructions and examples on building your own custom router, see [README_ROUTER.md](../../README_ROUTER.md).
