package main

import (
	"archive/zip"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

type ProgressWriter struct {
	Total      int64
	Downloaded int64
	LastPct    int
	Label      string
}

func (pw *ProgressWriter) Write(p []byte) (int, error) {
	n := len(p)
	pw.Downloaded += int64(n)
	if pw.Total > 0 {
		pct := int((float64(pw.Downloaded) / float64(pw.Total)) * 100)
		if pct != pw.LastPct && pct%5 == 0 {
			pw.LastPct = pct
			mbDown := float64(pw.Downloaded) / (1024 * 1024)
			mbTotal := float64(pw.Total) / (1024 * 1024)
			fmt.Printf("\r[%s] Progress: %3d%% (%.1f MB / %.1f MB)", pw.Label, pct, mbDown, mbTotal)
		}
	} else {
		mbDown := float64(pw.Downloaded) / (1024 * 1024)
		fmt.Printf("\r[%s] Downloaded: %.1f MB", pw.Label, mbDown)
	}
	return n, nil
}

func downloadFile(url string, destPath string, label string) error {
	client := &http.Client{Timeout: 300 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("HTTP error %d: %s", resp.StatusCode, resp.Status)
	}

	out, err := os.Create(destPath)
	if err != nil {
		return err
	}
	defer out.Close()

	pw := &ProgressWriter{
		Total:   resp.ContentLength,
		Label:   label,
		LastPct: -1,
	}

	_, err = io.Copy(out, io.TeeReader(resp.Body, pw))
	fmt.Println()
	return err
}

func getTargetDir() string {
	sysDrive := os.Getenv("SystemDrive")
	if sysDrive == "" {
		sysDrive = "C:"
	}
	target := filepath.Join(sysDrive, "flowork")
	// Test writability
	if err := os.MkdirAll(target, 0755); err != nil {
		// Fallback to userprofile if C:\ is not writable
		userProfile := os.Getenv("USERPROFILE")
		if userProfile != "" {
			return filepath.Join(userProfile, "flowork")
		}
	}
	return target
}

func extractFloworkPayload(zipPath string, targetDir string) error {
	r, err := zip.OpenReader(zipPath)
	if err != nil {
		return err
	}
	defer r.Close()

	const prefix = "FLOWORK-AGENT-main/windows/"
	prefixLower := strings.ToLower(prefix)

	count := 0
	for _, f := range r.File {
		nameNormalized := strings.ReplaceAll(f.Name, "\\", "/")
		if !strings.HasPrefix(strings.ToLower(nameNormalized), prefixLower) {
			continue
		}

		relPath := nameNormalized[len(prefix):]
		if relPath == "" || strings.TrimSpace(relPath) == "/" {
			continue
		}

		destPath := filepath.Join(targetDir, filepath.FromSlash(relPath))

		// Preserve user data if already exists
		if strings.Contains(relPath, "portable-home/.flowork") {
			if _, err := os.Stat(destPath); err == nil {
				continue
			}
		}

		if f.FileInfo().IsDir() {
			os.MkdirAll(destPath, 0755)
			continue
		}

		if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
			return err
		}

		rc, err := f.Open()
		if err != nil {
			return err
		}

		outFile, err := os.OpenFile(destPath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			rc.Close()
			return err
		}

		_, err = io.Copy(outFile, rc)
		outFile.Close()
		rc.Close()
		if err != nil {
			return err
		}
		count++
	}

	fmt.Printf("[Extract] Extracted %d ecosystem components into %s\n", count, targetDir)
	return nil
}

func ensureNodeInstalled(targetDir string) error {
	// 1. Check if node is in system PATH
	checkCmd := exec.Command("node", "-v")
	if out, err := checkCmd.Output(); err == nil {
		ver := strings.TrimSpace(string(out))
		fmt.Printf("[Node.js] ✅ Detected existing system Node.js: %s\n", ver)
		return nil
	}

	nodeDir := filepath.Join(targetDir, "node")
	nodeExe := filepath.Join(nodeDir, "node.exe")

	// 2. Check if portable node already exists in targetDir\node
	if _, err := os.Stat(nodeExe); err == nil {
		testCmd := exec.Command(nodeExe, "-v")
		if out, err := testCmd.Output(); err == nil {
			ver := strings.TrimSpace(string(out))
			fmt.Printf("[Node.js] ✅ Detected existing portable Node.js in %s: %s\n", nodeDir, ver)
			appendNodeToPath(nodeDir)
			return nil
		}
	}

	// 3. Node.js is missing - download and configure portable Node.js LTS
	fmt.Println("[Node.js] ⚡ Node.js is required for Flowork AI nano-plugs and connection router.")
	fmt.Println("[Node.js] 📥 Automatically downloading portable Node.js LTS (v20.18.0 x64)...")

	tempZip := filepath.Join(os.TempDir(), "node_lts_win64.zip")
	defer os.Remove(tempZip)

	nodeUrl := "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip"
	if err := downloadFile(nodeUrl, tempZip, "Node.js LTS"); err != nil {
		fmt.Printf("[Node.js] ⚠️ Direct download failed: %v. Attempting fallback via winget...\n", err)
		wingetCmd := exec.Command("winget", "install", "OpenJS.NodeJS.LTS", "-h", "--accept-source-agreements", "--accept-package-agreements")
		if wErr := wingetCmd.Run(); wErr == nil {
			fmt.Println("[Node.js] ✅ Successfully installed Node.js via winget.")
			return nil
		}
		return fmt.Errorf("failed to download and install Node.js: %w", err)
	}

	fmt.Printf("[Node.js] 📦 Extracting portable Node.js into %s...\n", nodeDir)
	if err := extractNodeZip(tempZip, nodeDir); err != nil {
		return fmt.Errorf("failed to extract Node.js: %w", err)
	}

	// Verify extraction
	if _, err := os.Stat(nodeExe); err != nil {
		return fmt.Errorf("node.exe not found after extraction at %s", nodeExe)
	}

	vCmd := exec.Command(nodeExe, "-v")
	if out, err := vCmd.Output(); err == nil {
		ver := strings.TrimSpace(string(out))
		fmt.Printf("[Node.js] ✅ Portable Node.js installed successfully: %s\n", ver)
	}

	// Register in Windows User PATH
	appendNodeToPath(nodeDir)
	return nil
}

func extractNodeZip(zipPath string, targetNodeDir string) error {
	r, err := zip.OpenReader(zipPath)
	if err != nil {
		return err
	}
	defer r.Close()

	if err := os.MkdirAll(targetNodeDir, 0755); err != nil {
		return err
	}

	for _, f := range r.File {
		nameNormalized := strings.ReplaceAll(f.Name, "\\", "/")
		// Strip top-level directory (e.g. node-v20.18.0-win-x64/)
		parts := strings.SplitN(nameNormalized, "/", 2)
		if len(parts) < 2 || parts[1] == "" {
			continue
		}

		relPath := parts[1]
		destPath := filepath.Join(targetNodeDir, filepath.FromSlash(relPath))

		if f.FileInfo().IsDir() {
			os.MkdirAll(destPath, 0755)
			continue
		}

		if err := os.MkdirAll(filepath.Dir(destPath), 0755); err != nil {
			return err
		}

		rc, err := f.Open()
		if err != nil {
			return err
		}

		outFile, err := os.OpenFile(destPath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			rc.Close()
			return err
		}

		_, err = io.Copy(outFile, rc)
		outFile.Close()
		rc.Close()
		if err != nil {
			return err
		}
	}
	return nil
}

func appendNodeToPath(nodeDir string) {
	// Add to process environment
	currentPath := os.Getenv("PATH")
	if !strings.Contains(strings.ToLower(currentPath), strings.ToLower(nodeDir)) {
		os.Setenv("PATH", nodeDir+";"+currentPath)
	}

	// Persist to Windows User PATH via PowerShell
	psScript := fmt.Sprintf(`
		$p = '%s';
		$u = [Environment]::GetEnvironmentVariable('Path', 'User');
		if ($u -notlike "*$p*") {
			[Environment]::SetEnvironmentVariable('Path', "$u;$p", 'User')
		}
	`, nodeDir)
	exec.Command("powershell", "-NoProfile", "-Command", psScript).Run()
}

func createDesktopShortcut(targetDir string) {
	batPath := filepath.Join(targetDir, "flowork.bat")
	iconPath := filepath.Join(targetDir, "canvas-ui", "favicon.ico")
	if _, err := os.Stat(iconPath); os.IsNotExist(err) {
		iconPath = filepath.Join(targetDir, "x-flow.exe")
	}

	psScript := fmt.Sprintf(`
		$desktop = [Environment]::GetFolderPath('Desktop');
		$shortcutPath = Join-Path $desktop 'Flowork OS.lnk';
		$WshShell = New-Object -ComObject WScript.Shell;
		$Shortcut = $WshShell.CreateShortcut($shortcutPath);
		$Shortcut.TargetPath = '%s';
		$Shortcut.WorkingDirectory = '%s';
		if (Test-Path '%s') { $Shortcut.IconLocation = '%s' };
		$Shortcut.Description = 'Flowork OS Sovereign AI Agent (Portable)';
		$Shortcut.Save()
	`, batPath, targetDir, iconPath, iconPath)

	err := exec.Command("powershell", "-NoProfile", "-Command", psScript).Run()
	if err == nil {
		fmt.Println("[Shortcut] ✅ Desktop shortcut created: Flowork OS.lnk")
	} else {
		fmt.Printf("[Shortcut] ⚠️ Notice creating shortcut: %v\n", err)
	}
}

func waitForExit() {
	fmt.Println("\nPress Enter to exit or wait 3 seconds...")
	done := make(chan bool)
	go func() {
		var input string
		fmt.Scanln(&input)
		done <- true
	}()

	select {
	case <-done:
	case <-time.After(3 * time.Second):
	}
}

func main() {
	fmt.Println("========================================================================")
	fmt.Println(" 🚀 FLOWORK OS — PORTABLE SOVEREIGN AGENT INSTALLER (WINDOWS) ")
	fmt.Println(" Co-authored-by: Flowork OS <agent@floworkos.com>")
	fmt.Println("========================================================================")

	targetDir := getTargetDir()
	fmt.Printf("[Target] Destination folder: %s\n", targetDir)

	if err := os.MkdirAll(targetDir, 0755); err != nil {
		fmt.Printf("[Error] Failed to create installation directory: %v\n", err)
		waitForExit()
		return
	}

	// 1. Download Flowork repository archive
	fmt.Println("[Status] Connecting to official Flowork OS repository (main branch)...")
	tempZip := filepath.Join(os.TempDir(), "flowork_agent_main.zip")
	defer os.Remove(tempZip)

	archiveUrl := "https://codeload.github.com/flowork-os/FLOWORK-AGENT/zip/refs/heads/main"
	err := downloadFile(archiveUrl, tempZip, "Flowork Agent")
	if err != nil {
		fmt.Printf("[Warning] Upstream primary fetch failed: %v. Retrying backup endpoint...\n", err)
		archiveUrl = "https://github.com/flowork-os/FLOWORK-AGENT/archive/refs/heads/main.zip"
		err = downloadFile(archiveUrl, tempZip, "Flowork Agent")
		if err != nil {
			fmt.Printf("[Error] Failed to download Flowork Agent: %v\n", err)
			waitForExit()
			return
		}
	}

	// 2. Extract Flowork Windows payload
	fmt.Printf("[Status] Extracting portable Windows payload into %s...\n", targetDir)
	if err := extractFloworkPayload(tempZip, targetDir); err != nil {
		fmt.Printf("[Error] Extraction failed: %v\n", err)
		waitForExit()
		return
	}

	// 3. Ensure Node.js is installed
	if err := ensureNodeInstalled(targetDir); err != nil {
		fmt.Printf("[Warning] Node.js configuration alert: %v\n", err)
	}

	// 4. Create Desktop Shortcut
	createDesktopShortcut(targetDir)

	// 5. Launch Flowork Agent
	fmt.Println("========================================================================")
	fmt.Printf(" ✅ INSTALLATION COMPLETE! Flowork OS is ready in %s\n", targetDir)
	fmt.Println("========================================================================")
	fmt.Println("[Status] Launching Flowork Agent...")

	batPath := filepath.Join(targetDir, "flowork.bat")
	if _, err := os.Stat(batPath); err == nil {
		cmd := exec.Command("cmd.exe", "/c", "start", "", batPath)
		cmd.Dir = targetDir
		cmd.Start()
	} else {
		exePath := filepath.Join(targetDir, "x-flow.exe")
		if _, err := os.Stat(exePath); err == nil {
			cmd := exec.Command(exePath)
			cmd.Dir = targetDir
			cmd.Start()
		}
	}

	waitForExit()
}
