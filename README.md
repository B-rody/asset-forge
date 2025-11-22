# AssetFurnace 🚀

**One-Click Digital Asset Factory** – An autonomous, schema-driven pipeline that generates complete digital product bundles for marketplaces like Etsy and Gumroad.

---

## 🎯 What It Does

AssetFurnace executes a local AI pipeline that:

1. **Researcher** – Finds and prioritizes profitable digital-product niches
2. **Bundle Planner** – Designs the bundle (plan, assets, pricing, personas)
3. **Asset Maker** – Generates the assets and store metadata; runs QA
4. **Packager** – Merges metadata and assets into final ZIP bundle

**Output**: Complete digital-product bundle (assets + Etsy/Gumroad metadata + QA report + ZIP)

---

## ✨ Features

- 🎨 **Modern Desktop UI**: Tauri + React + TypeScript + Tailwind CSS + shadcn/ui
- 🐍 **Local Python Backend**: Compiled with Nuitka, communicates via JSON-Lines over stdio
- 🔐 **IP Protection**: Encrypted prompts at rest, decrypt in RAM only
- 🔑 **BYOL**: Bring Your Own License – use your OpenAI API key (stored securely in an encrypted local file)
- 🌓 **Light/Dark Mode**: Beautiful UI that adapts to your preference
- 📊 **Real-time Progress**: Live logs and progress tracking for each pipeline step

---

## 🛠️ Tech Stack

### Frontend
- **Tauri** – Rust-based desktop framework
- **Vite** – Lightning-fast build tool
- **React** – UI framework
- **TypeScript** – Type-safe development
- **Tailwind CSS** – Utility-first styling
- **shadcn/ui** – Beautiful, accessible components

### Backend
- **Python 3.11+** – Pipeline orchestration
- **OpenAI API** – AI model integration
- **Pydantic** – Schema validation
- **Nuitka** – Python to binary compilation
- **Keyring** – Secure API key storage

---

## 📋 Prerequisites

### Required Software

- **Node.js** 18+ and **pnpm** (or npm)
  - Install from [nodejs.org](https://nodejs.org/)
  - Install pnpm: `npm install -g pnpm`
- **Rust** 1.70+ (for Tauri)
  - Install from [rustup.rs](https://rustup.rs/)
- **Python** 3.11+
  - Install from [python.org](https://www.python.org/downloads/)
- **OpenAI API Key** (for generation)
  - Get yours at [platform.openai.com](https://platform.openai.com/api-keys)

### External Dependencies

AssetFurnace requires two external tools for document conversion. These are **not included** in the repository due to size constraints:

#### 1. **Pandoc** (Required)
- **Purpose**: Converts Markdown to various document formats
- **Download**: [Pandoc Releases](https://github.com/jgm/pandoc/releases)
- **Version**: 3.x or higher
- **Installation Location**: 
  - Place `pandoc.exe` (Windows) or `pandoc` (macOS/Linux) in `backend/bin/`
  - Example: `backend/bin/pandoc.exe`

#### 2. **wkhtmltopdf** (Required)
- **Purpose**: Converts HTML to PDF with high fidelity
- **Download**: [wkhtmltopdf Downloads](https://wkhtmltopdf.org/downloads.html)
- **Installation Location**:
  - Extract the full `wkhtmltopdf` folder to `backend/bin/`
  - Final structure should be:
    ```
    backend/bin/wkhtmltopdf/
    ├── bin/
    │   ├── wkhtmltopdf.exe
    │   ├── wkhtmltoimage.exe
    │   ├── wkhtmltox.dll
    │   └── vcruntime140.dll
    ├── include/
    ├── lib/
    └── uninstall.exe
    ```

> **Note**: The `.gitignore` already excludes `backend/bin/pandoc.exe` to prevent committing large binaries. Make sure to download these tools before running or building AssetFurnace.

---

## 🚀 Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/B-rody/asset-furnace.git
cd asset-furnace
```

### 2. Install External Dependencies

**Download and place the required tools:**

1. **Pandoc**:
   - Download from [Pandoc Releases](https://github.com/jgm/pandoc/releases)
   - Extract `pandoc.exe` (or `pandoc` on Unix) to `backend/bin/`

2. **wkhtmltopdf**:
   - Download from [wkhtmltopdf Downloads](https://wkhtmltopdf.org/downloads.html)
   - Extract the entire `wkhtmltopdf` folder to `backend/bin/`

**Verify your setup:**
```bash
# Check that the files exist
ls backend/bin/pandoc.exe              # Windows
ls backend/bin/pandoc                  # macOS/Linux
ls backend/bin/wkhtmltopdf/bin/        # Should show wkhtmltopdf.exe and related DLLs
```

### 3. Install Project Dependencies

```bash
# Install frontend dependencies
pnpm install

# Install Python backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### 4. Run in Development Mode

```bash
# Run the full app in development mode (hot-reload enabled)
pnpm dev
```

This will:
- Start the Vite dev server at `http://localhost:1420`
- Launch Tauri in development mode
- Run the Python backend with live reload

**Alternative: Run components separately**

```bash
# Terminal 1: Run frontend only
pnpm ui:dev

# Terminal 2: Run backend only
pnpm backend:dev

# Terminal 3: Run Tauri (after frontend is running)
pnpm tauri dev
```

### 5. First Run Setup

1. Launch the app
2. Click the **Settings** button (⚙️) in the header
3. Paste your **OpenAI API Key**
4. Click **Save**
5. Start generating! 🎉

Your API key is stored encrypted locally at:
- Windows: `%APPDATA%\AssetFurnace\.api_key.enc`
- macOS: `~/Library/Application Support/AssetFurnace/.api_key.enc`
- Linux: `~/.local/share/AssetFurnace/.api_key.enc`

---

## 📦 Building for Production

### Prerequisites for Building

1. Complete all steps in **Development Setup** above
2. Ensure external dependencies (Pandoc, wkhtmltopdf) are in place
3. Install Python build dependencies:
   ```bash
   cd backend
   pip install nuitka ordered-set zstandard
   cd ..
   ```

### Build Process

#### Full Build (Recommended)

```bash
# Build everything: frontend, backend, and portable ZIP
pnpm build
```

This will:
1. Build the optimized React frontend (`ui/dist/`)
2. Compile Python backend to native binary with Nuitka (`backend/bin/main.dist/`)
3. Create a portable ZIP at `dist/AssetFurnace-Portable.zip`

# Build backend only (Nuitka compilation)
pnpm backend:build
# Or use platform-specific scripts:
# Windows: scripts\build_backend.bat
# Unix: ./scripts/build_backend.sh

# Build Tauri app only (requires frontend + backend already built)
pnpm tauri build
```

### Build Configuration

The build process is configured in:
- **Tauri**: `src-tauri/tauri.conf.json`
- **Nuitka**: `scripts/build_backend.bat` or `scripts/build_backend.sh`
- **Frontend**: `vite.config.ts`

**What gets bundled:**
- Compiled Python backend (`backend/bin/main.dist/`)
- External tools (Pandoc, wkhtmltopdf) embedded in the binary
- Encrypted prompts and schemas
- React frontend assets

### Troubleshooting Builds

**Issue**: `pandoc.exe not found` during build
- **Solution**: Ensure `backend/bin/pandoc.exe` exists before building

**Issue**: `wkhtmltopdf` errors
- **Solution**: Verify the full `backend/bin/wkhtmltopdf/` folder structure is present

**Issue**: Nuitka compilation fails
- **Solution**: 
  1. Install Visual Studio Build Tools (Windows) or GCC (Linux/macOS)
  2. Ensure Python 3.11+ is installed
  3. Try building with `--jobs=1` flag in build script for better error messages

**Issue**: ZIP file size is large
- **Solution**: This is expected (~120MB) due to bundled Python runtime, AI dependencies, and external tools

---

## 🎯 Usage

## 📁 Project Structure

```
AssetFurnace/
├── ui/                       # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── lib/              # Utilities & IPC
│   │   └── styles/           # Global styles
│   └── index.html
├── src-tauri/                # Tauri desktop app
│   ├── src/main.rs          # Rust entry point
│   └── tauri.conf.json      # App configuration
├── backend/                  # Python pipeline
│   ├── app/
│   │   ├── main.py          # Stdio IPC entrypoint
│   │   ├── pipeline/        # Pipeline agents
│   │   ├── security/        # Encryption & keyring
│   │   └── schemas/         # JSON schemas
│   └── pyproject.toml
└── scripts/                  # Build utilities
```

## 🔄 Pipeline Modes

### One-Click Mode
Fully autonomous – the AI decides everything:
```json
{"cmd":"run_pipeline","mode":"one_click","params":{"model":"gpt-4o","reasoning":"normal"}}
```

### Focused Mode
You provide a keyword or niche:
```json
{"cmd":"run_pipeline","mode":"focused","params":{"keyword":"notion templates"}}
```

### Re-run Single Step
Re-execute a specific pipeline step:
```json
{"cmd":"re_run_step","params":{"bundle_id":"2025-10-07-focus-journal","step":"maker"}}
```

## 🔐 Security

- **Encrypted Prompts**: All prompts encrypted at rest with Fernet (AES-128)
- **Encrypted API Key**: API keys stored in an encrypted file on your local device, managed entirely by the app
- **Compiled Binary**: Python backend compiled with Nuitka for IP protection
- **No Network Server**: All communication via stdio (no HTTP server exposure)
- **No AssetFurnace Servers**: Your data and API key never leave your device except to call OpenAI's API

## 📊 IPC Protocol

Backend communicates with frontend via **JSON-Lines** over stdio:

```json
{"event":"log","step":"Researcher","message":"Scanning marketplaces..."}
{"event":"progress","step":"Planner","pct":25}
{"event":"qa","status":"pass","score":0.93}
{"event":"done","result":{"bundle_id":"2025-10-07-focus-journal","output_path":"..."}}
{"event":"error","step":"Maker","message":"Validation failed"}
```

## 🛠️ Development

```bash
# Frontend only (with mock backend)
pnpm ui:dev

# Build frontend only
pnpm ui:build

# Run Python backend directly (for testing)
cd backend
python -m app.main

# Compile backend with Nuitka
pnpm backend:build
```

## 📝 License

This project is open-source. Contributions and feedback are welcome!

## 💡 Support

For questions about using AssetFurnace, click the Help button (?) in the app's header bar for comprehensive documentation and tutorials.

---

**Built with ❤️ for digital creators**
