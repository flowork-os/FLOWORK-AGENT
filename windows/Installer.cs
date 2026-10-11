using System;
using System.IO;
using System.Net;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;

namespace FloworkInstaller
{
    class Program
    {
        const string TargetDir = @"C:\flowork";
        const string NodeDownloadUrl = @"https://nodejs.org/dist/v20.18.0/win-x64/node.exe";
        const string UpstreamZipUrl = @"https://codeload.github.com/flowork-os/FLOWORK-WINDOWS/zip/refs/heads/main";

        static void Main(string[] args)
        {
            Console.Title = "Flowork OS - Autonomous Sovereign Agent Installer";
            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine(@"========================================================================");
            Console.WriteLine(@"  🚀 FLOWORK OS — AUTONOMOUS ZERO-SETUP AGENT INSTALLER (WINDOWS)");
            Console.WriteLine(@"  Target Installation Path: C:\flowork");
            Console.WriteLine(@"========================================================================");
            Console.ResetColor();

            try
            {
                // 1. Ensure Target Directory on Drive C:
                Console.WriteLine("\n[1/5] 📁 Setting up installation directory at " + TargetDir + "...");
                if (!Directory.Exists(TargetDir))
                {
                    Directory.CreateDirectory(TargetDir);
                }

                string nodeDir = Path.Combine(TargetDir, "node");
                if (!Directory.Exists(nodeDir)) Directory.CreateDirectory(nodeDir);

                string binDir = Path.Combine(TargetDir, ".FL_BIN");
                if (!Directory.Exists(binDir)) Directory.CreateDirectory(binDir);

                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("      ✅ Directory structure initialized on Drive C:.");
                Console.ResetColor();

                // 2. Check & Auto-Install Node.js
                Console.WriteLine("\n[2/5] ⚡ Checking Node.js runtime prerequisites...");
                string nodeExe = Path.Combine(nodeDir, "node.exe");
                bool nodeReady = false;

                if (File.Exists(nodeExe))
                {
                    nodeReady = true;
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("      ✅ Standalone Node.js detected at: " + nodeExe);
                    Console.ResetColor();
                }
                else if (CheckCommand("node"))
                {
                    nodeReady = true;
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("      ✅ System-wide Node.js detected in PATH.");
                    Console.ResetColor();
                }
                else if (File.Exists(@"C:\Program Files\nodejs\node.exe"))
                {
                    nodeReady = true;
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine(@"      ✅ System Node.js detected in C:\Program Files\nodejs\node.exe.");
                    Console.ResetColor();
                }

                if (!nodeReady)
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("      ⚠️ Node.js runtime not found. Automatically downloading standalone Node.js...");
                    Console.ResetColor();

                    DownloadFileWithProgress(NodeDownloadUrl, nodeExe, "Node.js Runtime");

                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("\n      ✅ Standalone Node.js runtime successfully installed into " + nodeExe);
                    Console.ResetColor();

                    // Optional silent background winget install
                    try
                    {
                        ProcessStartInfo wgPsi = new ProcessStartInfo
                        {
                            FileName = "winget",
                            Arguments = "install --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements",
                            UseShellExecute = false,
                            CreateNoWindow = true
                        };
                        Process.Start(wgPsi);
                    }
                    catch { }
                }

                // 3. Check Flowork Core Components
                Console.WriteLine("\n[3/5] 🌐 Verifying Flowork Core Payload in " + TargetDir + "...");
                string xflowExe = Path.Combine(TargetDir, "x-flow.exe");
                string routerJs = Path.Combine(TargetDir, @"connection\router.js");

                if (!File.Exists(xflowExe) || !File.Exists(routerJs))
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine("      ⚡ Synchronizing Flowork core payload from upstream repository...");
                    Console.ResetColor();

                    string tempZip = Path.Combine(Path.GetTempPath(), "flowork_setup.zip");
                    string tempExt = Path.Combine(Path.GetTempPath(), "flowork_setup_ext");

                    DownloadFileWithProgress(UpstreamZipUrl, tempZip, "Flowork Core Archive");

                    Console.WriteLine("\n      📦 Extracting components directly into " + TargetDir + "...");
                    ExecutePowerShell(string.Format(
                        "$ext = '{0}'; if (Test-Path $ext) {{ Remove-Item $ext -Recurse -Force }}; " +
                        "Expand-Archive -Path '{1}' -DestinationPath $ext -Force; " +
                        "$src = if (Test-Path (Join-Path $ext 'FLOWORK-WINDOWS-main')) { Join-Path $ext 'FLOWORK-WINDOWS-main' } else { Join-Path $ext 'FLOWORK-AGENT-main\\windows' }; " +
                        "Get-ChildItem -Path $src -Recurse | Where-Object {{ $_.FullName -notmatch 'portable-home\\\\\\.flowork' }} | ForEach-Object {{ " +
                        "  $rel = $_.FullName.Substring($src.Length).TrimStart('\\'); " +
                        "  $dest = Join-Path '{2}' $rel; " +
                        "  if ($_.PSIsContainer) {{ [System.IO.Directory]::CreateDirectory($dest) | Out-Null }} " +
                        "  else {{ Copy-Item -Path $_.FullName -Destination $dest -Force }} " +
                        "}}; " +
                        "Remove-Item $ext -Recurse -Force -ErrorAction SilentlyContinue; " +
                        "Remove-Item '{1}' -Force -ErrorAction SilentlyContinue;",
                        tempExt, tempZip, TargetDir
                    ));

                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("      ✅ Core payload successfully synchronized into " + TargetDir);
                    Console.ResetColor();
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("      ✅ Flowork Core Payload is already verified in " + TargetDir);
                    Console.ResetColor();
                }

                // 4. Ensure Desktop Shortcut Points Strictly to C:\flowork\flowork.bat
                Console.WriteLine("\n[4/5] 🔗 Creating Windows Desktop Shortcut...");
                string desktopDir = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                string shortcutPath = Path.Combine(desktopDir, "Flowork Agent.lnk");
                string targetBat = Path.Combine(TargetDir, "flowork.bat");
                string iconPath = Path.Combine(TargetDir, @"canvas-ui\favicon.ico");

                CreateShortcut(shortcutPath, targetBat, TargetDir, iconPath, "Flowork OS Sovereign Agent");

                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("      ✅ Shortcut 'Flowork Agent' created on Desktop -> " + targetBat);
                Console.ResetColor();

                // 5. Launch Flowork
                Console.WriteLine("\n[5/5] 🚀 Launching Flowork OS...");
                string runBat = Path.Combine(TargetDir, "run.bat");
                if (File.Exists(runBat))
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo
                    {
                        FileName = "cmd.exe",
                        Arguments = "/c \"" + runBat + "\"",
                        WorkingDirectory = TargetDir,
                        UseShellExecute = true
                    };
                    Process.Start(startInfo);
                }

                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine(@"========================================================================");
                Console.WriteLine(@"  🎉 FLOWORK OS INSTALLATION COMPLETE!");
                Console.WriteLine(@"  Host URL: http://127.0.0.1:19890");
                Console.WriteLine(@"  Location: " + TargetDir);
                Console.WriteLine(@"========================================================================");
                Console.ResetColor();
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine("\n[Installer Error] " + ex.Message);
                Console.ResetColor();
                Console.WriteLine("\nPress any key to exit...");
                Console.ReadKey();
            }
        }

        static bool CheckCommand(string command)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = "where",
                    Arguments = command,
                    RedirectStandardOutput = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                };
                using (Process p = Process.Start(psi))
                {
                    p.WaitForExit(3000);
                    return p.ExitCode == 0;
                }
            }
            catch
            {
                return false;
            }
        }

        static void DownloadFileWithProgress(string url, string destination, string label)
        {
            ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12 | (SecurityProtocolType)3072;
            using (WebClient client = new WebClient())
            {
                client.Headers.Add("User-Agent", "Flowork-Installer/1.0");
                long lastPercent = -1;

                client.DownloadProgressChanged += (s, e) =>
                {
                    if (e.ProgressPercentage != lastPercent && e.ProgressPercentage % 10 == 0)
                    {
                        lastPercent = e.ProgressPercentage;
                        Console.Write("\r      ⏳ Downloading " + label + ": " + e.ProgressPercentage + "% (" + (e.BytesReceived / 1024 / 1024) + " MB)...");
                    }
                };

                AutoResetEvent done = new AutoResetEvent(false);
                Exception dlError = null;

                client.DownloadFileCompleted += (s, e) =>
                {
                    if (e.Error != null) dlError = e.Error;
                    done.Set();
                };

                client.DownloadFileAsync(new Uri(url), destination);
                done.WaitOne();

                if (dlError != null) throw dlError;
            }
        }

        static void ExecutePowerShell(string script)
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = "-NoProfile -ExecutionPolicy Bypass -Command \"" + script.Replace("\"", "\\\"") + "\"",
                UseShellExecute = false,
                CreateNoWindow = true
            };
            using (Process p = Process.Start(psi))
            {
                p.WaitForExit();
            }
        }

        static void CreateShortcut(string shortcutPath, string targetPath, string workingDir, string iconPath, string description)
        {
            string psScript = string.Format(
                "$w = New-Object -ComObject WScript.Shell; " +
                "$s = $w.CreateShortcut('{0}'); " +
                "$s.TargetPath = '{1}'; " +
                "$s.WorkingDirectory = '{2}'; " +
                "$s.Description = '{3}'; " +
                "if (Test-Path '{4}') {{ $s.IconLocation = '{4}' }}; " +
                "$s.Save();",
                shortcutPath.Replace("'", "''"),
                targetPath.Replace("'", "''"),
                workingDir.Replace("'", "''"),
                description.Replace("'", "''"),
                iconPath.Replace("'", "''")
            );
            ExecutePowerShell(psScript);
        }
    }
}
