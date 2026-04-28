#!/usr/bin/env python3
"""
Llama.cpp Control Center – Full-featured GUI for llama.cpp on Windows.
Adapted for Intel Iris Xe / Intel integrated GPUs using the Vulkan backend.
Works with the pre‑extracted Vulkan build (e.g. llama-b8931-bin-win-vulkan-x64).
Made by Shashin Somanayake aka USDS)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess, threading, os, sys, json, time, webbrowser, tempfile
import glob

# ────────────────────────────────────────────────────────────────────
#  Configuration & persistent settings
# ────────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "llama_gui_config.json")
INSTALL_PS1 = os.path.join(tempfile.gettempdir(), "install_llama_cpp_vulkan.ps1")
VERIFY_PS1  = os.path.join(tempfile.gettempdir(), "verify_llama_vulkan.ps1")

DEFAULTS = {
    "build_bin_dir": "",          # folder containing the Vulkan executables
    "last_model_dir": os.path.expanduser("~"),
    "last_mmproj_dir": os.path.expanduser("~"),
    "server_host": "127.0.0.1",
    "server_port": "8080",
    "server_threads": "8",
    "server_ngl": "99",           # you will likely lower this for Intel iGPU
    "server_ctx": "2048",
    "server_temp": "0.7",
    "server_extra": "",
    "server_mmproj": "",
    "cli_ngl": "99",
    "cli_threads": "8",
    "cli_ctx": "2048",
    "cli_temp": "0.7",
    "perplexity_ngl": "99",
    "perplexity_ctx": "2048",
    "bench_model": "",
    "bench_ngl": "99",
}

# ────────────────────────────────────────────────────────────────────
#  Find the Vulkan build folder
# ────────────────────────────────────────────────────────────────────
def find_llama_bin_dir():
    """
    Locate the folder that contains a Vulkan llama.cpp installation.
    We look for any directory that has both 'ggml-vulkan.dll' and
    an executable like 'llama-cli.exe' (or the typo 'llama-ci.exe').
    """
    # 1) Check the user's home for a folder matching the typical download name
    home = os.path.expanduser("~")
    for d in os.listdir(home):
        full = os.path.join(home, d)
        if os.path.isdir(full) and d.startswith("llama-b") and d.endswith("-vulkan-x64"):
            if os.path.exists(os.path.join(full, "ggml-vulkan.dll")):
                return full

    # 2) Check a 'llama.cpp\build-vulkan' folder (created by our installer)
    default_build = os.path.join(home, "llama.cpp", "build-vulkan")
    if os.path.isdir(default_build) and os.path.exists(os.path.join(default_build, "ggml-vulkan.dll")):
        return default_build

    # 3) Search the current directory
    for d in os.listdir("."):
        full = os.path.join(os.getcwd(), d)
        if os.path.isdir(full) and d.startswith("llama-b") and d.endswith("-vulkan-x64"):
            if os.path.exists(os.path.join(full, "ggml-vulkan.dll")):
                return full

    # 4) Fallback: try to find llama-cli.exe on PATH
    import shutil
    cli = shutil.which("llama-cli.exe")
    if not cli:
        cli = shutil.which("llama-ci.exe")   # handle the typo
    if cli:
        d = os.path.dirname(cli)
        if os.path.exists(os.path.join(d, "ggml-vulkan.dll")):
            return d
    return None

# ────────────────────────────────────────────────────────────────────
#  Embedded PowerShell scripts for installation / verification
# ────────────────────────────────────────────────────────────────────
INSTALL_SCRIPT = r"""
<#
.SYNOPSIS
    Downloads and extracts the latest Vulkan llama.cpp build for Windows.
.DESCRIPTION
    Fetches the newest release from GitHub, downloads the *-vulkan-x64.zip
    asset, and extracts it to $HOME\llama.cpp\build-vulkan.
#>
$ErrorActionPreference = "Stop"
$Home = $env:USERPROFILE
$Dest = "$Home\llama.cpp\build-vulkan"

Write-Host "=========================================="
Write-Host " Downloading Vulkan llama.cpp build"
Write-Host "=========================================="

# Get the latest release tag using the GitHub API
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
$tag = $release.tag_name
Write-Host "Latest release: $tag"

# Find the Vulkan asset
$asset = $release.assets | Where-Object { $_.name -like "*vulkan-x64.zip" } | Select-Object -First 1
if (-not $asset) {
    Write-Host "ERROR: Could not find a Vulkan asset in the latest release." -ForegroundColor Red
    exit 1
}
$url = $asset.browser_download_url
$zip = Join-Path $env:TEMP "llama-vulkan.zip"
Write-Host "Downloading $($asset.name)..."
Invoke-WebRequest -Uri $url -OutFile $zip

# Extract and move
Write-Host "Extracting to $Dest..."
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
Expand-Archive -Path $zip -DestinationPath $Dest -Force
Remove-Item $zip

Write-Host "Vulkan build installed to: $Dest"
Write-Host "Done."
"""

VERIFY_SCRIPT = r"""
<#
.SYNOPSIS
    Verifies that the Vulkan backend can see your Intel GPU.
#>
$ErrorActionPreference = "Stop"
$BinDir = $args[0]   # passed by the GUI

# Locate the CLI executable (handles typo)
$cli = if (Test-Path "$BinDir\llama-cli.exe") { "$BinDir\llama-cli.exe" }
       elseif (Test-Path "$BinDir\llama-ci.exe") { "$BinDir\llama-ci.exe" }
       else { Write-Host "ERROR: llama-cli.exe not found in $BinDir"; exit 1 }

Write-Host "Running: $cli --list-devices"
& $cli --list-devices 2>&1 | Write-Host

# Optionally, check the output for "Intel" or "GPU" to give a clear status
$output = & $cli --list-devices 2>&1 | Out-String
if ($output -match "Intel" -or $output -match "GPU") {
    Write-Host "`n[OK] Intel GPU detected – Vulkan offloading should work."
} else {
    Write-Host "`n[WARNING] No Intel GPU found in the device list. Check your drivers."
}
"""

# ────────────────────────────────────────────────────────────────────
#  Worker class to run external processes and stream output
# ────────────────────────────────────────────────────────────────────
class TaskRunner:
    def __init__(self, log_widget, on_finish=None):
        self.log = log_widget
        self.process = None
        self.on_finish = on_finish
        self._stopped = False

    def run_cmd(self, cmd, cwd=None, env=None):
        """Run command in a background thread and stream output."""
        def task():
            try:
                self.process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, shell=True, cwd=cwd, env=env, bufsize=1
                )
                for line in self.process.stdout:
                    if self._stopped:
                        self.process.terminate()
                        break
                    self.log.insert(tk.END, line)
                    self.log.see(tk.END)
                    self.log.update()
                self.process.wait()
                if not self._stopped and self.on_finish:
                    self.log.after(0, self.on_finish, self.process.returncode)
            except Exception as e:
                self.log.insert(tk.END, f"\n[Error] {e}\n")
        threading.Thread(target=task, daemon=True).start()

    def stop(self):
        self._stopped = True
        if self.process and self.process.poll() is None:
            self.process.terminate()

# ────────────────────────────────────────────────────────────────────
#  Main Application
# ────────────────────────────────────────────────────────────────────
class LlamaGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama.cpp Control Center (Vulkan Version) made by Shashin Somanayake")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self.load_config()
        self.bin_dir = find_llama_bin_dir()
        if not self.bin_dir:
            self.bin_dir = self.config.get("build_bin_dir", "")

        self.setup_ui()
        self.update_status()

    # ── Config ────────────────────────────────────
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
        else:
            self.config = DEFAULTS.copy()

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    # ── UI Setup ──────────────────────────────────
    def setup_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Refresh installation detection", command=self.update_status)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Top status frame
        status_frame = ttk.Frame(self.root, padding=5)
        status_frame.pack(fill=tk.X, side=tk.TOP)

        self.status_label = ttk.Label(status_frame, text="Checking Vulkan build...", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.install_btn = ttk.Button(status_frame, text="⬇ Download Vulkan Build", command=self.run_install_ps1)
        self.install_btn.pack(side=tk.RIGHT, padx=5)
        self.install_btn.pack_forget()  # only shown when not found

        self.verify_btn = ttk.Button(status_frame, text="✅ Verify GPU", command=self.run_verify_ps1)
        self.verify_btn.pack(side=tk.RIGHT, padx=5)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.tab_server = ttk.Frame(self.notebook)
        self.tab_cli = ttk.Frame(self.notebook)
        self.tab_perplexity = ttk.Frame(self.notebook)
        self.tab_bench = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_server, text="Server")
        self.notebook.add(self.tab_cli, text="CLI Chat")
        self.notebook.add(self.tab_perplexity, text="Perplexity")
        self.notebook.add(self.tab_bench, text="Benchmark")

        self.setup_server_tab()
        self.setup_cli_tab()
        self.setup_perplexity_tab()
        self.setup_bench_tab()

        # Bottom log
        log_frame = ttk.LabelFrame(self.root, text="Output", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.NORMAL)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.runner = TaskRunner(self.log_text, self.on_task_finished)

    # ── Server Tab ────────────────────────────────
    def setup_server_tab(self):
        frame = self.tab_server
        ttk.Label(frame, text="Model File (.gguf):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.server_model_var = tk.StringVar(value=self.config.get("last_model", ""))
        ttk.Entry(frame, textvariable=self.server_model_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.server_model_var, "GGUF files", "*.gguf")).grid(row=0, column=2, padx=5)

        ttk.Label(frame, text="MMPROJ File (for multimodal):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.server_mmproj_var = tk.StringVar(value=self.config.get("server_mmproj", ""))
        ttk.Entry(frame, textvariable=self.server_mmproj_var, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.server_mmproj_var, "MMPROJ files", "*.gguf")).grid(row=1, column=2, padx=5)

        # Options
        opts = ttk.LabelFrame(frame, text="Server Options", padding=5)
        opts.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(opts, text="Host:").grid(row=0, column=0, sticky=tk.W)
        self.host_var = tk.StringVar(value=self.config["server_host"])
        ttk.Entry(opts, textvariable=self.host_var, width=15).grid(row=0, column=1, padx=5)

        ttk.Label(opts, text="Port:").grid(row=0, column=2, sticky=tk.W)
        self.port_var = tk.StringVar(value=self.config["server_port"])
        ttk.Entry(opts, textvariable=self.port_var, width=6).grid(row=0, column=3, padx=5)

        ttk.Label(opts, text="GPU Layers (-ngl):").grid(row=1, column=0, sticky=tk.W)
        self.server_ngl_var = tk.StringVar(value=self.config["server_ngl"])
        ttk.Entry(opts, textvariable=self.server_ngl_var, width=5).grid(row=1, column=1, padx=5)

        ttk.Label(opts, text="Threads (-t):").grid(row=1, column=2, sticky=tk.W)
        self.server_threads_var = tk.StringVar(value=self.config["server_threads"])
        ttk.Entry(opts, textvariable=self.server_threads_var, width=5).grid(row=1, column=3, padx=5)

        ttk.Label(opts, text="Context (-c):").grid(row=2, column=0, sticky=tk.W)
        self.server_ctx_var = tk.StringVar(value=self.config["server_ctx"])
        ttk.Entry(opts, textvariable=self.server_ctx_var, width=8).grid(row=2, column=1, padx=5)

        ttk.Label(opts, text="Temperature:").grid(row=2, column=2, sticky=tk.W)
        self.server_temp_var = tk.StringVar(value=self.config["server_temp"])
        ttk.Entry(opts, textvariable=self.server_temp_var, width=5).grid(row=2, column=3, padx=5)

        ttk.Label(opts, text="Extra Args:").grid(row=3, column=0, sticky=tk.W)
        self.server_extra_var = tk.StringVar(value=self.config["server_extra"])
        ttk.Entry(opts, textvariable=self.server_extra_var, width=50).grid(row=3, column=1, columnspan=3, padx=5, sticky="ew")

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="▶ Start Server", command=self.start_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🌐 Open Browser", command=lambda: webbrowser.open(f"http://{self.host_var.get()}:{self.port_var.get()}")).pack(side=tk.LEFT, padx=5)

    # ── CLI Tab ───────────────────────────────────
    def setup_cli_tab(self):
        frame = self.tab_cli
        ttk.Label(frame, text="Model File (.gguf):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.cli_model_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.cli_model_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.cli_model_var, "GGUF", "*.gguf")).grid(row=0, column=2)

        ttk.Label(frame, text="MMPROJ File:").grid(row=1, column=0, sticky=tk.W)
        self.cli_mmproj_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.cli_mmproj_var, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.cli_mmproj_var, "MMPROJ", "*.gguf")).grid(row=1, column=2)

        ttk.Label(frame, text="Prompt / Instruction:").grid(row=2, column=0, sticky=tk.W)
        self.cli_prompt_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.cli_prompt_var, width=60).grid(row=2, column=1, padx=5)

        opts = ttk.LabelFrame(frame, text="Options", padding=5)
        opts.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(opts, text="GPU Layers:").grid(row=0, column=0, sticky=tk.W)
        self.cli_ngl_var = tk.StringVar(value=self.config["cli_ngl"])
        ttk.Entry(opts, textvariable=self.cli_ngl_var, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(opts, text="Threads:").grid(row=0, column=2, sticky=tk.W)
        self.cli_threads_var = tk.StringVar(value=self.config["cli_threads"])
        ttk.Entry(opts, textvariable=self.cli_threads_var, width=5).grid(row=0, column=3, padx=5)

        ttk.Label(opts, text="Context:").grid(row=1, column=0, sticky=tk.W)
        self.cli_ctx_var = tk.StringVar(value=self.config["cli_ctx"])
        ttk.Entry(opts, textvariable=self.cli_ctx_var, width=8).grid(row=1, column=1, padx=5)

        ttk.Label(opts, text="Temperature:").grid(row=1, column=2, sticky=tk.W)
        self.cli_temp_var = tk.StringVar(value=self.config["cli_temp"])
        ttk.Entry(opts, textvariable=self.cli_temp_var, width=5).grid(row=1, column=3, padx=5)

        ttk.Label(opts, text="Extra Args:").grid(row=2, column=0, sticky=tk.W)
        self.cli_extra_var = tk.StringVar()
        ttk.Entry(opts, textvariable=self.cli_extra_var, width=50).grid(row=2, column=1, columnspan=3, padx=5, sticky="ew")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="▶ Run CLI", command=self.run_cli).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_task).pack(side=tk.LEFT, padx=5)

    # ── Perplexity Tab ───────────────────────────
    def setup_perplexity_tab(self):
        frame = self.tab_perplexity
        ttk.Label(frame, text="Model File:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ppl_model_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ppl_model_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.ppl_model_var, "GGUF", "*.gguf")).grid(row=0, column=2)

        ttk.Label(frame, text="Input Text File:").grid(row=1, column=0, sticky=tk.W)
        self.ppl_input_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.ppl_input_var, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.ppl_input_var, "Text", "*.txt")).grid(row=1, column=2)

        opts = ttk.LabelFrame(frame, text="Options", padding=5)
        opts.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(opts, text="GPU Layers:").grid(row=0, column=0, sticky=tk.W)
        self.ppl_ngl_var = tk.StringVar(value=self.config["perplexity_ngl"])
        ttk.Entry(opts, textvariable=self.ppl_ngl_var, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(opts, text="Context:").grid(row=0, column=2, sticky=tk.W)
        self.ppl_ctx_var = tk.StringVar(value=self.config["perplexity_ctx"])
        ttk.Entry(opts, textvariable=self.ppl_ctx_var, width=8).grid(row=0, column=3, padx=5)

        ttk.Label(opts, text="Extra Args:").grid(row=1, column=0, sticky=tk.W)
        self.ppl_extra_var = tk.StringVar()
        ttk.Entry(opts, textvariable=self.ppl_extra_var, width=50).grid(row=1, column=1, columnspan=3, padx=5, sticky="ew")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="▶ Run Perplexity", command=self.run_perplexity).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_task).pack(side=tk.LEFT, padx=5)

    # ── Benchmark Tab ────────────────────────────
    def setup_bench_tab(self):
        frame = self.tab_bench
        ttk.Label(frame, text="Model (optional, leave blank for internal test):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.bench_model_var = tk.StringVar(value=self.config["bench_model"])
        ttk.Entry(frame, textvariable=self.bench_model_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=lambda: self.browse_file(self.bench_model_var, "GGUF", "*.gguf")).grid(row=0, column=2)

        opts = ttk.LabelFrame(frame, text="Options", padding=5)
        opts.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        ttk.Label(opts, text="GPU Layers:").grid(row=0, column=0, sticky=tk.W)
        self.bench_ngl_var = tk.StringVar(value=self.config["bench_ngl"])
        ttk.Entry(opts, textvariable=self.bench_ngl_var, width=5).grid(row=0, column=1, padx=5)

        ttk.Label(opts, text="Extra Args:").grid(row=1, column=0, sticky=tk.W)
        self.bench_extra_var = tk.StringVar()
        ttk.Entry(opts, textvariable=self.bench_extra_var, width=50).grid(row=1, column=1, columnspan=3, padx=5, sticky="ew")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="▶ Run Benchmark", command=self.run_benchmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="⏹ Stop", command=self.stop_task).pack(side=tk.LEFT, padx=5)

    # ── Helpers ──────────────────────────────────
    def browse_file(self, var, description, pattern):
        path = filedialog.askopenfilename(title=f"Select {description}", filetypes=[(description, pattern), ("All files", "*.*")])
        if path:
            var.set(path)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def stop_task(self):
        self.runner.stop()
        self.log_text.insert(tk.END, "\n[User stopped]\n")

    def on_task_finished(self, returncode):
        if returncode == 0:
            self.log_text.insert(tk.END, "\n[Process completed successfully]\n")
        else:
            self.log_text.insert(tk.END, f"\n[Process exited with code {returncode}]\n")

    def update_status(self):
        self.bin_dir = find_llama_bin_dir()
        if self.bin_dir:
            self.status_label.config(text=f"Vulkan build found: {self.bin_dir}", foreground="green")
            self.install_btn.pack_forget()
            self.config["build_bin_dir"] = self.bin_dir
            self.save_config()
        else:
            self.status_label.config(text="Vulkan build NOT FOUND", foreground="red")
            self.install_btn.pack(side=tk.RIGHT, padx=5)

    # ── Installation & verification (Vulkan) ─────
    def run_install_ps1(self):
        """Download the latest Vulkan build from GitHub."""
        if messagebox.askyesno("Download Vulkan Build", "This will download the latest Vulkan llama.cpp build (about 50 MB). Continue?"):
            try:
                with open(INSTALL_PS1, "w") as f:
                    f.write(INSTALL_SCRIPT)
                self.clear_log()
                self.runner.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{INSTALL_PS1}"')
                # After a short delay, rescan for the new installation
                self.root.after(15000, self.update_status)  # 15 seconds
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def run_verify_ps1(self):
        """Run --list-devices to confirm the Intel GPU is detected."""
        if not self.bin_dir:
            messagebox.showerror("Error", "Vulkan build not found. Please install or select a directory.")
            return
        try:
            with open(VERIFY_PS1, "w") as f:
                f.write(VERIFY_SCRIPT)
            self.clear_log()
            # Pass the binary directory as an argument
            self.runner.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{VERIFY_PS1}" "{self.bin_dir}"')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Command builders ─────────────────────────
    def _get_exe(self, name):
        """Return the full path to an executable, handling the llama-ci typo."""
        if not self.bin_dir:
            return None
        # Try exact name first
        full = os.path.join(self.bin_dir, name)
        if os.path.exists(full):
            return full
        # If it's llama-cli.exe, also try llama-ci.exe
        if name == "llama-cli.exe":
            alt = os.path.join(self.bin_dir, "llama-ci.exe")
            if os.path.exists(alt):
                return alt
        return None

    def build_server_cmd(self):
        exe = self._get_exe("llama-server.exe")
        if not exe:
            messagebox.showerror("Error", "llama-server.exe not found.")
            return None
        model = self.server_model_var.get()
        if not model:
            messagebox.showerror("Error", "No model selected.")
            return None
        mmproj = self.server_mmproj_var.get()
        cmd = f'"{exe}" -m "{model}" --host {self.host_var.get()} --port {self.port_var.get()}'
        cmd += f' -ngl {self.server_ngl_var.get()} -t {self.server_threads_var.get()} -c {self.server_ctx_var.get()} --temp {self.server_temp_var.get()}'
        if mmproj:
            cmd += f' --mmproj "{mmproj}"'
        extra = self.server_extra_var.get().strip()
        if extra:
            cmd += " " + extra
        return cmd

    def start_server(self):
        cmd = self.build_server_cmd()
        if cmd:
            self.clear_log()
            self.runner.run_cmd(cmd)

    def build_cli_cmd(self):
        exe = self._get_exe("llama-cli.exe")  # handles typo
        if not exe:
            messagebox.showerror("Error", "llama-cli.exe / llama-ci.exe not found.")
            return None
        model = self.cli_model_var.get()
        if not model:
            messagebox.showerror("Error", "No model selected.")
            return None
        prompt = self.cli_prompt_var.get()
        mmproj = self.cli_mmproj_var.get()
        cmd = f'"{exe}" -m "{model}" -p "{prompt}" -ngl {self.cli_ngl_var.get()} -t {self.cli_threads_var.get()} -c {self.cli_ctx_var.get()} --temp {self.cli_temp_var.get()}'
        if mmproj:
            cmd += f' --mmproj "{mmproj}"'
        extra = self.cli_extra_var.get().strip()
        if extra:
            cmd += " " + extra
        return cmd

    def run_cli(self):
        cmd = self.build_cli_cmd()
        if cmd:
            self.clear_log()
            self.runner.run_cmd(cmd)

    def build_perplexity_cmd(self):
        exe = self._get_exe("llama-perplexity.exe")
        if not exe:
            messagebox.showerror("Error", "llama-perplexity.exe not found.")
            return None
        model = self.ppl_model_var.get()
        if not model:
            messagebox.showerror("Error", "No model selected.")
            return None
        input_file = self.ppl_input_var.get()
        if not input_file:
            messagebox.showerror("Error", "No input text file.")
            return None
        cmd = f'"{exe}" -m "{model}" -f "{input_file}" -ngl {self.ppl_ngl_var.get()} -c {self.ppl_ctx_var.get()}'
        extra = self.ppl_extra_var.get().strip()
        if extra:
            cmd += " " + extra
        return cmd

    def run_perplexity(self):
        cmd = self.build_perplexity_cmd()
        if cmd:
            self.clear_log()
            self.runner.run_cmd(cmd)

    def build_bench_cmd(self):
        exe = self._get_exe("llama-bench.exe")
        if not exe:
            messagebox.showerror("Error", "llama-bench.exe not found.")
            return None
        model = self.bench_model_var.get()
        cmd = f'"{exe}"'
        if model:
            cmd += f' -m "{model}"'
        cmd += f' -ngl {self.bench_ngl_var.get()}'
        extra = self.bench_extra_var.get().strip()
        if extra:
            cmd += " " + extra
        return cmd

    def run_benchmark(self):
        cmd = self.build_bench_cmd()
        if cmd:
            self.clear_log()
            self.runner.run_cmd(cmd)

# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = LlamaGuiApp(root)
    root.mainloop()