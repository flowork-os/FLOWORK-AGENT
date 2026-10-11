# 🚀 FLOWORK OS — OFFICIAL WINDOWS DISTRIBUTION

Sovereign Multi-OS AI Agent & Native Desktop Canvas Host for Windows.

---

## ⚡ Zero-Setup Installation (Windows)

### Option 1: Double-Click Standalone Installer
1. Download **`Flowork-Agent-Installer.exe`** from releases or this repository.
2. Double-click the installer.
3. The installer will automatically:
   - Target and initialize **`C:\flowork`**.
   - Auto-install and configure the Node.js runtime environment.
   - Extract and verify all Flowork Core components.
   - Create the **Flowork Agent** desktop shortcut.
   - Launch the Canvas Host interface at **`http://127.0.0.1:19890`**.

### Option 2: Clone & Launch
```cmd
git clone https://github.com/flowork-os/FLOWORK-WINDOWS C:\flowork
cd /d C:\flowork
flowork.bat
```

---

## 🏛️ Architecture Overview

- **Canvas Host Engine (`x-flow.exe`)**: Port `19890`
- **Sovereign Switchboard (`connection/router.js`)**: Port `9099`
- **Portable Home Root**: `C:\flowork\portable-home`
- **Standalone Node Runtime**: `C:\flowork\node\node.exe`

---

## 🛡️ License
Licensed under the **MIT License**. Built with sovereign engineering discipline by the Flowork OS Community.
Co-authored-by: Flowork OS <agent@floworkos.com>
