Here is a **single, polished README.md** file for your GitHub repository. It covers all three scripts, their hardware targets, installation, usage, and troubleshooting – written in a clear, developer-friendly style.

```markdown
# 🦙 llama.cpp Control Center

**Three ready‑to‑run Python GUIs for llama.cpp on Windows** – each tuned for a different GPU class.

| Script | Target Hardware | Backend |
|--------|----------------|---------|
| `llama.cpp Control center - Intel iris -VULKAN.py` | Intel Iris Xe, UHD, Arc | Vulkan |
| `llama.cpp control centre - NVIDIA MX230 (low end).py` | MX230, GTX 1050/1650 (low VRAM) | CUDA |
| `llama.cpp control centre - NVIDIA RTX4060 +.py` | RTX 4060, 4070, 4080, 4090 | CUDA |

All scripts include:
- `llama-server` (web UI)
- `llama-cli` (command line chat)
- `llama-perplexity` (model evaluation)
- `llama-bench` (performance testing)
- Multimodal (MMPROJ) support
- One‑click installation & GPU verification

---

## 📋 Table of Contents

1. [Before you start](#-before-you-start)
2. [Getting the right llama.cpp binaries](#-getting-the-right-llamacpp-binaries)
3. [Where to place the scripts](#-where-to-place-the-scripts)
4. [Running the GUI](#-running-the-gui)
5. [Per‑script setup & tweaks](#-per-script-setup--tweaks)
6. [Using the tabs (server / CLI / perplexity / benchmark)](#-using-the-tabs)
7. [Persistent settings](#-persistent-settings)
8. [Troubleshooting](#-troubleshooting)
9. [Credits & license](#-credits--license)

---

## 🧠 Before you start

All scripts require:

- **Windows 10/11** (64‑bit)
- **Python 3.8+** (includes `tkinter` on Windows)
- **PowerShell 5.1+** (default)
- **Git**, **CMake** – only if you use the built‑in **Install** button

For **CUDA scripts** (MX230 / RTX4060):
- [CUDA Toolkit 11.8 or 12.x](https://developer.nvidia.com/cuda-downloads) + `nvcc` in PATH
- [Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022) with “Desktop development with C++”

For **Vulkan script** (Intel):
- Latest Intel GPU driver with Vulkan support (most Iris Xe drivers are fine)
- No extra SDK – the pre‑built binaries include `ggml-vulkan.dll`

---

## 📦 Getting the right llama.cpp binaries

### 🟢 Intel Vulkan script
**No compilation needed.** The script either:
- Finds a pre‑extracted Vulkan build folder (e.g. `%USERPROFILE%\llama-b8931-bin-win-vulkan-x64`), or
- Downloads the latest `*-vulkan-x64.zip` when you click **⬇ Download Vulkan Build**.

Extracted location after using the download button:
```
%USERPROFILE%\llama.cpp\build-vulkan\
```

### 🔵 NVIDIA CUDA scripts (both low‑end and RTX)
You have two options:

#### Option A – One‑click build (recommended)
1. Ensure Git, CMake, CUDA Toolkit and VS2022 are installed.
2. Run the GUI → click **🔧 Install llama.cpp**.
3. The PowerShell script will:
   - Clone `ggerganov/llama.cpp` into `%USERPROFILE%\llama.cpp`
   - Create `build-cuda` and compile with `-DGGML_CUDA=ON`
   - Place executables in `%USERPROFILE%\llama.cpp\build-cuda\bin\Release`

#### Option B – Manual download
Grab a pre‑built `*-cuda-x64.zip` from the [llama.cpp releases](https://github.com/ggerganov/llama.cpp/releases).  
Extract it so that `llama-cli.exe` is inside:
```
%USERPROFILE%\llama.cpp\build-cuda\bin\Release\
```

> Both CUDA scripts search exactly that path.

---

## 🗂️ Where to place the scripts

Save any `.py` file **anywhere** – Desktop, `Documents`, etc.  
When you run it, a `llama_gui_config.json` is created **next to the script** storing your last settings.

For the Vulkan script to auto‑detect a manual download:
- Extract the Vulkan `.zip` into `%USERPROFILE%\llama-b...-vulkan-x64`
- Or move it to `%USERPROFILE%\llama.cpp\build-vulkan`

---

## 🚀 Running the GUI

Open a **Command Prompt** or **PowerShell** in the script’s folder and run:

```cmd
python "llama.cpp Control center - Intel iris -VULKAN.py"
```

Replace with the script you want.  
You can also double‑click the `.py` file if `.py` is associated with Python.

---

## 🧪 Per‑script setup & tweaks

### Intel Iris / Vulkan script
- **First run**: Wait for status “Vulkan build found” (green).  
- If not found → click **⬇ Download Vulkan Build** (takes ~1 minute).  
- Click **✅ Verify GPU** – you should see your Intel GPU in the device list.  
- **GPU layers (`-ngl`)** → start with `20` (Iris Xe has shared memory). Do **not** use `99` unless you have an Arc discrete GPU.  
- Best models: up to 7B quantized (Q4_K_M) – 13B may be slow.

### MX230 low‑end CUDA script
- Click **🔧 Install llama.cpp** (requires Git, CMake, CUDA, VS2022).  
- After build (~5‑10 min), click **✅ Verify CUDA**.  
- **GPU layers** → `15-20` (MX230 has only 2‑4 GB VRAM).  
- Use Q4_K_M or IQ4_XS models ≤ 7B.  
- This script also keeps a **dropdown of recent models** – handy.

### RTX 4060+ CUDA script
- Same install & verify as above.  
- Verification runs `test-backend-ops.exe test -b cuda` – expects “CUDA backend: OK”.  
- **GPU layers** → `99` (full offload) works for up to 13B, even 32B with Q4.  
- For 70B models reduce to 60‑80 layers to avoid OOM.

---

## 🧭 Using the tabs

All scripts share the same tab layout. The **Output** panel shows live logs from the running command.

### 1. Server tab
- **Model** – your `.gguf` file  
- **MMPROJ** – optional, for multimodal (e.g. LLaVA)  
- **GPU layers** – set according to your GPU (see per‑script notes)  
- **Threads** – number of CPU cores (e.g. `8`)  
- **Context** – start with `2048`, increase if VRAM allows  
- Click **▶ Start Server** → open browser to `http://127.0.0.1:8080`  
- Click **🌐 Open Browser** to open the web UI automatically

### 2. CLI Chat tab
- Choose a model and type a prompt.  
- Optionally set an MMPROJ file for vision models.  
- Click **▶ Run CLI** – output streams directly into the log.  
- Use **⏹ Stop** to kill long generations.

### 3. Perplexity tab
- Provide a model and a `.txt` file (e.g. `wikitext-test.txt`).  
- The script runs `llama-perplexity.exe` and outputs the final perplexity score (lower = better).  
- Useful for comparing quantizations.

### 4. Benchmark tab
- **Leave model blank** – runs internal tensor ops benchmark (CPU/GPU).  
- Or select a model to measure real prompt processing speed (pp512, tg128).  
- Add extra flags like `-pp 512 -tg 128 -n 10` in the **Extra Args** field.

---

## ⚙️ Persistent settings

Each script creates `llama_gui_config.json` next to itself. Example content:

```json
{
  "build_bin_dir": "C:\\Users\\You\\llama.cpp\\build-cuda\\bin\\Release",
  "last_model_dir": "D:\\models",
  "server_host": "127.0.0.1",
  "server_port": "8080",
  "server_ngl": "20",
  "cli_ngl": "20",
  "recent_models": ["D:\\models\\phi-3.Q4_K_M.gguf", ...]
}
```

Edit this file manually to reset everything or to fix a wrong binary path.

> The **MX230 script** stores `recent_models` – the others don’t.

---

## 🐞 Troubleshooting

| Issue | Likely fix |
|-------|-------------|
| `llama-server.exe not found` (Vulkan) | Make sure `ggml-vulkan.dll` is in the same folder as `llama-server.exe`. Use **Refresh detection**. |
| CUDA build fails (NVCC not found) | Add `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x\bin` to PATH. Restart PowerShell. |
| Out of memory on MX230 | Lower `-ngl` to `12` or `10`. Use Q4_K_S or IQ2_XS models. Reduce context to `1024`. |
| Intel Vulkan very slow | Do NOT use `-ngl 99`. Set `20` or lower. Update Intel graphics driver. |
| Install script hangs | First build takes 15+ minutes. If it fails, run the generated `.ps1` from `%TEMP%` manually. |
| “Threads” setting ignored | Some llama.cpp builds ignore `-t` when GPU is heavily used – that’s normal. |
| Browser can’t connect to server | Check that the server is running (see log). Use `--host 0.0.0.0` in Extra Args to allow remote access. |

---

## 📄 Credits & license

- Scripts by **Shashin Somanayake (USDS)** – free to use, modify, share.  
- Built on [llama.cpp](https://github.com/ggerganov/llama.cpp) by Georgi Gerganov and contributors.  
- Uses only Python standard library – no extra `pip` installs.

---

## 🤝 Contributing

Found a bug? Want ROCm/HIP support or a dark theme?  
Open an issue or a pull request. Keep the code simple and dependency‑free.

**Happy prompting!** 🦙
```

