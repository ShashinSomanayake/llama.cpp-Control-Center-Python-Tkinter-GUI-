═══════════════════════════════════════════════════════════════════════
              🦙 LLAMA.CPP CONTROL CENTER – THREE GUIs
═══════════════════════════════════════════════════════════════════════

Three ready‑to‑run Python scripts that give you a complete desktop GUI 
for llama.cpp on Windows. Each script is tuned for a specific GPU class.

┌─────────────────────────────────────────────────────────────────────┐
│ SCRIPT                               │ TARGET GPU         │ BACKEND │
├──────────────────────────────────────┼────────────────────┼─────────┤
│ llama.cpp Control center - Intel...  │ Intel Iris Xe, UHD │ Vulkan  │
│ llama.cpp control centre - MX230...  │ MX230, GTX 1050    │ CUDA    │
│ llama.cpp control centre - RTX4060...│ RTX 4060, 4070+    │ CUDA    │
└─────────────────────────────────────────────────────────────────────┘

All scripts include:
  ✅ llama-server (web UI)
  ✅ llama-cli (interactive chat)
  ✅ llama-perplexity (model evaluation)
  ✅ llama-bench (performance testing)
  ✅ Multimodal (MMPROJ) support
  ✅ One‑click installation & GPU verification

═══════════════════════════════════════════════════════════════════════
📋 BEFORE YOU START – PREREQUISITES (all scripts)
═══════════════════════════════════════════════════════════════════════

  * Windows 10 / 11 (64‑bit)
  * Python 3.8+ (includes tkinter on Windows)
  * PowerShell 5.1+ (default on Windows)
  * Git and CMake – only if you use the built‑in Install button

  🔵 For CUDA scripts (MX230 / RTX4060):
     - CUDA Toolkit 11.8 or 12.x (nvcc must be in PATH)
     - Visual Studio 2022 Build Tools with “Desktop development with C++”

  🟢 For Vulkan script (Intel):
     - Latest Intel GPU driver with Vulkan support
     - No extra SDK needed – pre‑built binaries include ggml-vulkan.dll

═══════════════════════════════════════════════════════════════════════
📦 GETTING THE RIGHT LLAMA.CPP BINARIES
═══════════════════════════════════════════════════════════════════════

🔹 INTEL VULKAN SCRIPT – no compilation needed.
   The script automatically finds a pre‑extracted Vulkan build folder,
   for example:
        %USERPROFILE%\llama-b8931-bin-win-vulkan-x64\
   If not found, click the “⬇ Download Vulkan Build” button in the GUI.
   It will fetch the latest *-vulkan-x64.zip and extract it to:
        %USERPROFILE%\llama.cpp\build-vulkan\

🔹 NVIDIA CUDA SCRIPTS (both low‑end and RTX) – two options:

   ▶ Option A – One‑click build (recommended)
       1. Install Git, CMake, CUDA Toolkit and VS2022.
       2. Run the GUI → click “🔧 Install llama.cpp”.
       3. The PowerShell script will clone llama.cpp into
          %USERPROFILE%\llama.cpp, create build-cuda, and compile.
       4. Final executables are placed in:
          %USERPROFILE%\llama.cpp\build-cuda\bin\Release\

   ▶ Option B – Manual download
       Download a pre‑built *-cuda-x64.zip from the llama.cpp releases
       page. Extract it so that llama-cli.exe is inside:
          %USERPROFILE%\llama.cpp\build-cuda\bin\Release\

═══════════════════════════════════════════════════════════════════════
🗂️ WHERE TO PLACE THE SCRIPTS
═══════════════════════════════════════════════════════════════════════

  * Save any .py file ANYWHERE (Desktop, Documents, etc.).
  * When you run a script, it creates a llama_gui_config.json right
    next to it – that file stores your last settings.

  For the Vulkan script to auto‑detect a manual download:
     - Extract the Vulkan .zip into %USERPROFILE%\llama-b...-vulkan-x64
     - OR move it to %USERPROFILE%\llama.cpp\build-vulkan

═══════════════════════════════════════════════════════════════════════
🚀 RUNNING THE GUI
═══════════════════════════════════════════════════════════════════════

  Open a Command Prompt or PowerShell in the script’s folder and type:

      python "llama.cpp Control center - Intel iris -VULKAN.py"

  (Replace with the script you want.) You can also double‑click the .py
  file if .py is associated with Python.

═══════════════════════════════════════════════════════════════════════
🧪 PER‑SCRIPT SETUP & TWEAKS
═══════════════════════════════════════════════════════════════════════

🟢 INTEL IRIS / VULKAN SCRIPT
   * First run: Wait for status “Vulkan build found” (green).
   * If not found → click “⬇ Download Vulkan Build” (takes ~1 min).
   * Click “✅ Verify GPU” – you should see your Intel GPU listed.
   * GPU layers (-ngl): START WITH 20. Do not use 99 unless you have an
     Arc discrete GPU (Iris Xe shares system memory).
   * Best models: up to 7B quantized (Q4_K_M). 13B may be slow.

🔵 MX230 LOW‑END CUDA SCRIPT
   * Click “🔧 Install llama.cpp” (needs Git, CMake, CUDA, VS2022).
   * After build (5‑10 min), click “✅ Verify CUDA”.
   * GPU layers: 15‑20 (MX230 has only 2‑4 GB VRAM).
   * Use Q4_K_M or IQ4_XS models up to 7B.
   * This script also keeps a dropdown of recent models.

🟣 RTX 4060+ CUDA SCRIPT
   * Same install & verify as above.
   * Verification uses test-backend-ops.exe – expects “CUDA backend: OK”.
   * GPU layers: 99 (full offload) works for up to 13B, even 32B with Q4.
   * For 70B models reduce to 60‑80 layers to avoid OOM.

═══════════════════════════════════════════════════════════════════════
🧭 USING THE TABS (Server / CLI / Perplexity / Benchmark)
═══════════════════════════════════════════════════════════════════════

All scripts share the same 4 tabs. The Output panel shows live logs.

▶ SERVER TAB
   - Model: your .gguf file
   - MMPROJ: optional for multimodal (e.g. LLaVA)
   - GPU layers: set according to your GPU (see per‑script notes)
   - Threads: number of CPU cores (e.g. 8)
   - Context: start with 2048, increase if VRAM allows
   - Click “▶ Start Server” → open browser to http://127.0.0.1:8080
   - “🌐 Open Browser” opens the web UI automatically

▶ CLI CHAT TAB
   - Choose a model and type a prompt.
   - Optionally set an MMPROJ file for vision models.
   - Click “▶ Run CLI” – output streams into the log.
   - Use “⏹ Stop” to kill long generations.

▶ PERPLEXITY TAB
   - Provide a model and a .txt file (e.g. wikitext-test.txt).
   - Runs llama-perplexity.exe – final score (lower = better).
   - Useful for comparing quantizations.

▶ BENCHMARK TAB
   - Leave model blank → runs internal tensor ops benchmark (CPU/GPU).
   - Or select a model to measure real prompt processing speed.
   - Add extra flags like “-pp 512 -tg 128 -n 10” in Extra Args.

═══════════════════════════════════════════════════════════════════════
⚙️ PERSISTENT SETTINGS
═══════════════════════════════════════════════════════════════════════

Each script creates a llama_gui_config.json next to itself. Example:

{
  "build_bin_dir": "C:\\Users\\You\\llama.cpp\\build-cuda\\bin\\Release",
  "last_model_dir": "D:\\models",
  "server_host": "127.0.0.1",
  "server_port": "8080",
  "server_ngl": "20",
  "cli_ngl": "20",
  "recent_models": ["D:\\models\\phi-3.Q4_K_M.gguf"]
}

* The MX230 script stores “recent_models” – the others don’t.
* Edit this file manually to reset everything or fix a wrong path.

═══════════════════════════════════════════════════════════════════════
🐞 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════

Issue                                      Fix
───────────────────────────────────────────────────────────────────────
llama-server.exe not found (Vulkan)       Make sure ggml-vulkan.dll is
                                           in the same folder as 
                                           llama-server.exe. Use 
                                           “Refresh detection”.

CUDA build fails (NVCC not found)         Add C:\Program Files\NVIDIA
                                           GPU Computing Toolkit\CUDA\
                                           v12.x\bin to PATH. Restart.

Out of memory on MX230                    Lower -ngl to 12 or 10.
                                           Use Q4_K_S or IQ2_XS models.
                                           Reduce context to 1024.

Intel Vulkan very slow                     Do NOT use -ngl 99. Set 20
                                           or lower. Update graphics
                                           driver.

Install script hangs                       First build takes 15+ minutes.
                                           If it fails, run the generated
                                           .ps1 from %TEMP% manually.

“Threads” setting ignored                  Some builds ignore -t when
                                           GPU is heavily used – normal.

Browser can’t connect to server            Check log for server errors.
                                           Use --host 0.0.0.0 in Extra
                                           Args to allow remote access.

═══════════════════════════════════════════════════════════════════════
📄 CREDITS & LICENSE
═══════════════════════════════════════════════════════════════════════

  * Scripts by Shashin Somanayake (USDS) – free to use, modify, share.
  * Built on llama.cpp by Georgi Gerganov and contributors.
  * Uses only Python standard library – no extra pip installs.

  Happy prompting! 🦙
═══════════════════════════════════════════════════════════════════════
