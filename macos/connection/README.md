# 🌐 Sovereign AI Gateway & Multi-Provider Connection Guide
## Flowork OS Autonomous Switchboard (Antigravity Pro, Ollama & 9Router)

This document provides a comprehensive operational guide for connecting and configuring AI model providers in **Flowork OS** via the built-in Sovereign AI Switchboard (`http://127.0.0.1:9099`).

---

## 1. Google Antigravity Pro Multi-Account (Cluster Pooling)

Flowork OS features a built-in enterprise-grade account rotator that seamlessly pools up to 100 Google Antigravity Pro accounts. It manages token encryption, automatic rate-limit failover, and request balancing without interrupting active agent swarms.

### Step-by-Step Connection Instructions:
1. **Launch Flowork OS**:
   - On **Linux / macOS**: Run `./run.sh` from your terminal.
   - On **Windows**: Run `run.bat` or launch `Flowork-Agent-Installer.exe`.
2. **Access Account Pool**:
   - In the Canvas Cockpit, click the **Account Pool** icon (🔀) in the top-right toolbar, or directly navigate to:
     ```
     http://127.0.0.1:9099/auth/router/login-url
     ```
3. **Authorize via Official Google OAuth 2.0**:
   - Your default web browser will open Google's official authorization page.
   - Sign in with your Google / Antigravity account and grant the requested permissions.
4. **Instant Verification**:
   - Upon successful authorization, the switchboard redirects to a confirmation panel displaying:
     - **Identity**: Your verified Google email address (e.g., `user@gmail.com`).
     - **Active Pool Status**: Total active accounts currently available in the cluster (e.g., `25 / 100 Accounts Active`).
5. **Secure Local Vault**:
   - Access and refresh tokens are securely encrypted and stored locally in `portable-home/.flowork/account_pool.json`. No plaintext credentials are leaked or sent to third-party tracking services.
6. **Multi-Account Stacking**:
   - Repeat the login step for additional Google accounts to increase concurrency and achieve uninterrupted high-throughput agent operations.

---

## 2. Ollama Local Engine (Offline & Private AI)

Flowork OS integrates directly with locally hosted Large Language Models via Ollama, enabling air-gapped, zero-latency, and 100% private inference on your hardware.

### Step-by-Step Connection Instructions:
1. **Start Ollama Daemon**:
   - Ensure Ollama is installed and running on your host machine:
     ```bash
     ollama serve
     ```
   - Default local API endpoint: `http://127.0.0.1:11434`.
2. **Download Target Models**:
   - Pull your desired models via terminal:
     ```bash
     ollama pull llama3.3:latest
     ollama pull qwen2.5-coder:7b
     ollama pull deepseek-r1:8b
     ```
3. **Configure Agent in Flowork Cockpit**:
   - Click on the target **Agent Node** in the 3D Canvas workspace.
   - Open **Tab 5 (Model & Persona)** in the configuration modal.
   - Set **Provider** dropdown to: `Ollama`.
   - Flowork OS will automatically query `http://127.0.0.1:9099/auth/router/models?provider=ollama` and enumerate all models installed on your local daemon.
   - Select your preferred model using the radio button.
   - Click **Save Node**. The agent immediately switches to local inference.

---

## 3. 9Router (Unified Upstream Cloud Gateway)

9Router acts as a unified upstream gateway, delivering streamlined access to premier global models (Claude 3.7 Sonnet, DeepSeek R1, GPT-4o, GLM-5) through a single resilient pipe.

### Step-by-Step Connection Instructions:
1. **Acquire Credentials**:
   - Obtain your API Key or Access Token from your 9Router provider dashboard.
2. **Configure in Flowork Cockpit**:
   - Open the target **Agent Node** modal and select **Tab 5 (Model & Persona)**.
   - Set **Provider** to: `9Router`.
   - The available remote models will automatically populate:
     - `clinepass/cline-pass/glm-5.2`
     - `deepseek/deepseek-r1`
     - `openai/gpt-4o`
     - `anthropic/claude-3-7-sonnet`
   - Paste your API Key into the **API Key / Token** input field.
3. **Apply & Deploy**:
   - Click **Save Node**. The agent routing table updates instantaneously with end-to-end TLS encryption.

---

## 📁 Connection Configuration Directory Structure

The `connection/` folder maintains identity schemas and upstream endpoint definitions:

| File | Purpose |
|---|---|
| `providers.json` | Catalog of supported AI providers, upstream endpoints, and default models. |
| `endpoints.json` | Internal client identity manifest, IPC router endpoints, and connection health targets. |
| `README.md` | This architectural reference and connection operational manual. |

---

## 🛡️ Security & Zero-Trust Notice

- **No Remote Telemetry**: Flowork OS operates under a strict sovereign zero-telemetry doctrine.
- **Credential Segregation**: Tokens, private keys, and session cookies are quarantined in `portable-home/.flowork/` and are never committed to version control.
