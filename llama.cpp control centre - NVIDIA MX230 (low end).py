#!/usr/bin/env python3
"""
Llama.cpp Control Center – Adapted for pre‑built binaries in C:/Users/Administrator/llama.cpp (changeas you want)
Manages server, CLI, perplexity, benchmarks, and multimodal models.
This is for Lowend CUDA graphic crads like MX230 
Made by Shashin Somanayake
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess, threading, os, sys, json, time, webbrowser, tempfile

# ────────────────────────────────────────────────────────────────────
#  Configuration & persistent settings
# ────────────────────────────────────────────────────────────────────
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "llama_gui_config.json")
INSTALL_PS1 = os.path.join(tempfile.gettempdir(), "install_llama_cpp.ps1")
VERIFY_PS1 = os.path.join(tempfile.gettempdir(), "verify_llama.ps1")

DEFAULTS = {
    "build_bin_dir": "",          # will be filled automatically
    "last_model_dir": os.path.expanduser("~"),
    "last_mmproj_dir": os.path.expanduser("~"),
    "recent_models": [],          # list of recently used models
    "server_host": "127.0.0.1",
    "server_port": "8080",
    "server_threads": "8",
    "server_ngl": "20",           # conservative start for MX230
    "server_ctx": "2048",
    "server_temp": "0.7",
    "server_extra": "",
    "server_mmproj": "",
    "cli_ngl": "20",
    "cli_threads": "8",
    "cli_ctx": "2048",
    "cli_temp": "0.7",
    "perplexity_ngl": "20",
    "perplexity_ctx": "2048",
    "bench_model": "",
    "bench_ngl": "20",
}

# ────────────────────────────────────────────────────────────────────
#  Find llama.cpp installation
# ────────────────────────────────────────────────────────────────────
def find_llama_bin_dir():
    """
    1. Use the directory where this script is located (C:/Users/Administrator/llama.cpp)
       if it contains llama-cli.exe.
    2. Fallback to other locations.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, "llama-cli.exe")):
        return script_dir

    # Original fallback: build-cuda/bin/Release
    default_path = os.path.join(os.path.expanduser("~"), "llama.cpp", "build-cuda", "bin", "Release")
    if os.path.isdir(default_path) and os.path.exists(os.path.join(default_path, "llama-cli.exe")):
        return default_path

    # Search any build-* directory
    base = os.path.join(os.path.expanduser("~"), "llama.cpp")
    if os.path.isdir(base):
        for d in os.listdir(base):
            if d.startswith("build-"):
                bin_dir = os.path.join(base, d, "bin", "Release")
                if os.path.isdir(bin_dir) and os.path.exists(os.path.join(bin_dir, "llama-cli.exe")):
                    return bin_dir
    # Check system PATH
    import shutil
    cli = shutil.which("llama-cli.exe")
    if cli:
        return os.path.dirname(cli)
    return None

# ────────────────────────────────────────────────────────────────────
#  Embedded installation & verification scripts (PowerShell)
# ────────────────────────────────────────────────────────────────────
INSTALL_SCRIPT = r"""
# Install llama.cpp with CUDA (the same robust script you used)
$ErrorActionPreference = "Stop"
$LlamaDir = "$HOME\llama.cpp"
$BuildDir = "$LlamaDir\build-cuda"
$Jobs = [Environment]::ProcessorCount
Write-Host "Installing llama.cpp..."
Write-Host "[1/5] Checking dependencies..."
$missing = @()
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { $missing += "Git" }
if (-not (Get-Command cmake -ErrorAction SilentlyContinue)) { $missing += "CMake" }
if (-not (Get-Command nvcc -ErrorAction SilentlyContinue)) { $missing += "CUDA Toolkit" }
$vsPath = & "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe" -latest -property installationPath 2>$null
if (-not $vsPath) { $missing += "Visual Studio Build Tools" }
if ($missing.Count -gt 0) { Write-Host "ERROR: Missing $missing"; exit 1 }
Write-Host "[2/5] Preparing repository..."
if (Test-Path $LlamaDir) { Push-Location $LlamaDir; git pull --ff-only; Pop-Location } else { git clone https://github.com/ggerganov/llama.cpp.git $LlamaDir }
Write-Host "[3/5] Configuring CMake..."
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
Push-Location $LlamaDir; New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null; Push-Location $BuildDir
$cmakeArgs = @("..", "-G", "Visual Studio 17 2022", "-A", "x64", "-DCMAKE_BUILD_TYPE=Release", "-DGGML_CUDA=ON", "-DGGML_CUDA_FORCE_MMQ=ON", "-DGGML_CUDA_F16=ON", "-DGGML_NATIVE=ON", "-DGGML_OPENMP=ON", "-DBUILD_SHARED_LIBS=OFF")
& cmake @cmakeArgs; if ($LASTEXITCODE -ne 0) { exit 1 }
Pop-Location; Pop-Location
Write-Host "[4/5] Building..."
Push-Location $BuildDir; & cmake --build . --config Release -j $Jobs; if ($LASTEXITCODE -ne 0) { exit 1 }; Pop-Location
Write-Host "[5/5] Done."
"""

VERIFY_SCRIPT = r"""
$BinDir = "$HOME\llama.cpp"
$cli = Join-Path $BinDir "llama-cli.exe"
if (-not (Test-Path $cli)) { Write-Host "FAIL: llama-cli.exe not found"; exit 1 }
Write-Host "Testing GPU offload with empty run..."
$cmd = "& `"$cli`" -m `"$HOME\Documents\Qwen3.5-2B.Q4_K_M.gguf`" -ngl 20 -t 8 -n 1 --no-warmup 2>&1"
$out = Invoke-Expression $cmd | Out-String
if ($LASTEXITCODE -eq 0 -and $out -match "offloaded .* layers to GPU") {
    Write-Host "CUDA backend: OK (GPU offloading confirmed)"
} else {
    Write-Host "CUDA backend: FAIL"
    Write-Host $out
    exit 1
}
Write-Host "Verification complete."
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
        self.root.title("Llama.cpp Control Center (MX230 Hybrid) by Shashin Somanayake")
        self.root.geometry("1100x800")
        self.root.minsize(900, 650)

        self.load_config()
        self.bin_dir = find_llama_bin_dir()
        if not self.bin_dir:
            self.bin_dir = self.config.get("build_bin_dir", "")
        else:
            self.config["build_bin_dir"] = self.bin_dir

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
        file_menu.add_command(label="Refresh status", command=self.update_status)
        file_menu.add_command(label="Clear log", command=self.clear_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Top status frame
        status_frame = ttk.Frame(self.root, padding=5)
        status_frame.pack(fill=tk.X, side=tk.TOP)

        self.status_label = ttk.Label(status_frame, text="Checking llama.cpp...", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.install_btn = ttk.Button(status_frame, text="🔧 Install llama.cpp", command=self.run_install_ps1)
        self.install_btn.pack(side=tk.RIGHT, padx=5)
        self.install_btn.pack_forget()  # shown only when not installed

        self.verify_btn = ttk.Button(status_frame, text="✅ Verify CUDA", command=self.run_verify_ps1)
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

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state=tk.NORMAL)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.runner = TaskRunner(self.log_text, self.on_task_finished)

    # ── Server Tab ────────────────────────────────
    def setup_server_tab(self):
        frame = self.tab_server
        # Model selection with recent combobox
        ttk.Label(frame, text="Model File (.gguf):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.server_model_var = tk.StringVar()
        # Combobox for recent models
        recent_models = self.config.get("recent_models", [])
        self.server_model_combo = ttk.Combobox(frame, textvariable=self.server_model_var, values=recent_models, width=58)
        self.server_model_combo.grid(row=0, column=1, padx=5)
        self.server_model_combo.bind('<<ComboboxSelected>>', lambda e: self.server_model_var.set(self.server_model_combo.get()))
        ttk.Button(frame, text="Browse", command=lambda: self.browse_model(self.server_model_var)).grid(row=0, column=2, padx=5)

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
        recent_models = self.config.get("recent_models", [])
        self.cli_model_combo = ttk.Combobox(frame, textvariable=self.cli_model_var, values=recent_models, width=58)
        self.cli_model_combo.grid(row=0, column=1, padx=5)
        self.cli_model_combo.bind('<<ComboboxSelected>>', lambda e: self.cli_model_var.set(self.cli_model_combo.get()))
        ttk.Button(frame, text="Browse", command=lambda: self.browse_model(self.cli_model_var)).grid(row=0, column=2)

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
        recent_models = self.config.get("recent_models", [])
        self.ppl_model_combo = ttk.Combobox(frame, textvariable=self.ppl_model_var, values=recent_models, width=58)
        self.ppl_model_combo.grid(row=0, column=1, padx=5)
        self.ppl_model_combo.bind('<<ComboboxSelected>>', lambda e: self.ppl_model_var.set(self.ppl_model_combo.get()))
        ttk.Button(frame, text="Browse", command=lambda: self.browse_model(self.ppl_model_var)).grid(row=0, column=2)

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
        recent_models = self.config.get("recent_models", [])
        self.bench_model_combo = ttk.Combobox(frame, textvariable=self.bench_model_var, values=recent_models, width=58)
        self.bench_model_combo.grid(row=0, column=1, padx=5)
        self.bench_model_combo.bind('<<ComboboxSelected>>', lambda e: self.bench_model_var.set(self.bench_model_combo.get()))
        ttk.Button(frame, text="Browse", command=lambda: self.browse_model(self.bench_model_var)).grid(row=0, column=2)

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

    def browse_model(self, var):
        """Browse for a model file and add to recent list."""
        initial_dir = self.config.get("last_model_dir", os.path.expanduser("~"))
        path = filedialog.askopenfilename(title="Select Model (.gguf)", filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")], initialdir=initial_dir)
        if path:
            var.set(path)
            self.add_recent_model(path)
            self.config["last_model_dir"] = os.path.dirname(path)
            self.save_config()
            self.update_recent_combos()

    def add_recent_model(self, model_path):
        recent = self.config.get("recent_models", [])
        if model_path in recent:
            recent.remove(model_path)
        recent.insert(0, model_path)
        recent = recent[:10]  # keep last 10
        self.config["recent_models"] = recent
        self.save_config()

    def update_recent_combos(self):
        recent = self.config.get("recent_models", [])
        for combo in [self.server_model_combo, self.cli_model_combo, self.ppl_model_combo, self.bench_model_combo]:
            combo['values'] = recent

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
            self.status_label.config(text=f"✓ llama.cpp found: {self.bin_dir}", foreground="green")
            self.install_btn.pack_forget()
            self.config["build_bin_dir"] = self.bin_dir
            self.save_config()
        else:
            self.status_label.config(text="✗ llama.cpp NOT FOUND", foreground="red")
            self.install_btn.pack(side=tk.RIGHT, padx=5)

    def run_install_ps1(self):
        if messagebox.askyesno("Install llama.cpp", "This will download and build llama.cpp with CUDA. Continue?"):
            try:
                with open(INSTALL_PS1, "w") as f:
                    f.write(INSTALL_SCRIPT)
                self.clear_log()
                self.runner.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{INSTALL_PS1}"')
                self.root.after(10000, self.update_status)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def run_verify_ps1(self):
        try:
            with open(VERIFY_PS1, "w") as f:
                f.write(VERIFY_SCRIPT)
            self.clear_log()
            self.runner.run_cmd(f'powershell -ExecutionPolicy Bypass -File "{VERIFY_PS1}"')
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── Build command abstractions ───────────────
    def build_server_cmd(self):
        if not self.bin_dir:
            messagebox.showerror("Error", "llama.cpp not found.")
            return None
        exe = os.path.join(self.bin_dir, "llama-server.exe")
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
        if not self.bin_dir:
            return None
        exe = os.path.join(self.bin_dir, "llama-cli.exe")
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
        if not self.bin_dir:
            return None
        exe = os.path.join(self.bin_dir, "llama-perplexity.exe")
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
        if not self.bin_dir:
            return None
        exe = os.path.join(self.bin_dir, "llama-bench.exe")
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