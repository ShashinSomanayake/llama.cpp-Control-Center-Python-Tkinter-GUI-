---

# 🦙 LLAMA.CPP CONTROL CENTER – Desktop GUI Suite

A set of **ready-to-run Python GUIs** for managing and running `llama.cpp` on Windows.
Each script is optimized for a specific GPU class, giving you a smooth, one-click experience.

---

## 📦 Available Scripts

| Script               | Target GPU         | Backend |
| -------------------- | ------------------ | ------- |
| **Intel Vulkan GUI** | Intel Iris Xe, UHD | Vulkan  |
| **MX230 CUDA GUI**   | MX230, GTX 1050    | CUDA    |
| **RTX CUDA GUI**     | RTX 4060 / 4070+   | CUDA    |

---

## ✨ Features

* ✅ Built-in **llama-server** (Web UI)
* ✅ **llama-cli** for interactive chat
* ✅ **llama-perplexity** for evaluation
* ✅ **llama-bench** for performance testing
* ✅ 🖼️ **Multimodal (MMPROJ) support**
* ✅ ⚡ **One-click installation**
* ✅ 🔍 **GPU verification tools**
* ✅ 💾 Persistent configuration (auto-saved)

---

## ⚙️ Prerequisites

### 🖥️ General (All Scripts)

* Windows 10 / 11 (64-bit)
* Python 3.8+ (includes tkinter)
* PowerShell 5.1+

### 🔵 CUDA Scripts (MX230 / RTX)

* CUDA Toolkit 11.8 or 12.x
* Visual Studio 2022 Build Tools
  *(Desktop development with C++)*
* Git & CMake

### 🟢 Intel Vulkan Script

* Latest Intel GPU drivers (with Vulkan support)
* No SDK required (prebuilt binaries included)

---

## 📥 Getting llama.cpp Binaries

### 🟢 Intel Vulkan (No Build Required)

* Auto-detects prebuilt Vulkan binaries:

  ```
  %USERPROFILE%\llama-b8931-bin-win-vulkan-x64\
  ```
* Or download via GUI:

  * Click **⬇ Download Vulkan Build**
  * Extracts to:

  ```
  %USERPROFILE%\llama.cpp\build-vulkan\
  ```

---

### 🔵 CUDA (MX230 / RTX)

#### ▶ Option A – One-Click Install (Recommended)

1. Install dependencies (Git, CMake, CUDA, VS2022)
2. Open GUI → click **🔧 Install llama.cpp**
3. Script will:

   * Clone repo
   * Build with CUDA
4. Output:

   ```
   %USERPROFILE%\llama.cpp\build-cuda\bin\Release\
   ```

#### ▶ Option B – Manual Download

* Download prebuilt `*-cuda-x64.zip`
* Extract so `llama-cli.exe` is located at:

  ```
  %USERPROFILE%\llama.cpp\build-cuda\bin\Release\
  ```

---

## 📁 Script Location

* Save `.py` files anywhere (Desktop, Documents, etc.)
* A config file is auto-created:

  ```
  llama_gui_config.json
  ```

### Vulkan Auto-Detection Paths:

```
%USERPROFILE%\llama-b...-vulkan-x64
%USERPROFILE%\llama.cpp\build-vulkan
```

---

## 🚀 Running the GUI

```bash
python "llama.cpp Control center - Intel iris -VULKAN.py"
```

Or simply **double-click** the `.py` file.

---

## 🧪 GPU-Specific Setup Tips

### 🟢 Intel Iris (Vulkan)

* Click **⬇ Download Vulkan Build** if needed
* Click **✅ Verify GPU**
* Recommended:

  * `-ngl 20` (NOT 99)
* Best models:

  * 7B (Q4_K_M)
  * 13B = slower

---

### 🔵 MX230 (Low-End CUDA)

* Click **🔧 Install llama.cpp**
* Then **✅ Verify CUDA**
* Recommended:

  * `-ngl 15–20`
* Use:

  * Q4_K_M / IQ4_XS models (≤7B)

---

### 🟣 RTX 4060+

* Full GPU offload supported
* Recommended:

  * `-ngl 99`
* Supports:

  * 13B–32B easily
  * 70B → reduce to `60–80`

---

## 🧭 GUI Tabs Overview

### ▶ Server Tab

* Launch Web UI (`http://127.0.0.1:8080`)
* Configure:

  * Model (.gguf)
  * GPU layers
  * Threads
  * Context size

---

### ▶ CLI Chat Tab

* Interactive prompt mode
* Live output streaming
* Stop anytime with **⏹**

---

### ▶ Perplexity Tab

* Evaluate model quality
* Lower score = better

---

### ▶ Benchmark Tab

* Measure CPU/GPU performance
* Example args:

  ```
  -pp 512 -tg 128 -n 10
  ```

---

## 💾 Persistent Settings

Example `llama_gui_config.json`:

```json
{
  "build_bin_dir": "C:\\Users\\You\\llama.cpp\\build-cuda\\bin\\Release",
  "last_model_dir": "D:\\models",
  "server_host": "127.0.0.1",
  "server_port": "8080",
  "server_ngl": "20",
  "cli_ngl": "20",
  "recent_models": ["D:\\models\\phi-3.Q4_K_M.gguf"]
}
```

✔ Auto-saves last used settings
✔ Editable manually if needed

---

## 🐞 Troubleshooting

| Issue                     | Fix                                 |
| ------------------------- | ----------------------------------- |
| Vulkan build not detected | Ensure `ggml-vulkan.dll` is present |
| CUDA build fails          | Add CUDA `bin` to PATH              |
| Out of memory (MX230)     | Lower `-ngl`, reduce context        |
| Intel slow performance    | Use `-ngl 20`, update drivers       |
| Install hangs             | Run `.ps1` manually from `%TEMP%`   |
| Browser can't connect     | Use `--host 0.0.0.0`                |

---

## 📄 Credits & License

* 👨‍💻 **Shashin Somanayake (USDS)** – Creator
* 🧠 Built on **llama.cpp** by Georgi Gerganov & contributors
* 📦 Uses only Python standard library

---

## ❤️ Support

If you find this useful:

* ⭐ Star the repo
* 🍴 Fork & improve
* 🧠 Share your setups

---

**Happy Prompting! 🦙**
