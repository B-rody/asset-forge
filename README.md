# AssetForge 🚀

**One-Click Digital Asset Factory** – An autonomous, schema-driven pipeline that generates complete digital product bundles for marketplaces like Etsy and Gumroad.

## 🎯 What It Does

AssetForge executes a local AI pipeline that:

1. **Researcher** – Finds and prioritizes profitable digital-product niches
2. **Bundle Planner** – Designs the bundle (plan, assets, pricing, personas)
3. **Asset Maker** – Generates the assets and store metadata; runs QA
4. **Packager** – Merges metadata and assets into final ZIP bundle

**Output**: Complete digital-product bundle (assets + Etsy/Gumroad metadata + QA report + ZIP)

## ✨ Features

- 🎨 **Modern Desktop UI**: Tauri + React + TypeScript + Tailwind CSS + shadcn/ui
- 🐍 **Local Python Backend**: Compiled with Nuitka, communicates via JSON-Lines over stdio
- 🔐 **IP Protection**: Encrypted prompts at rest, decrypt in RAM only
- 🔑 **BYOL**: Bring Your Own License – use your OpenAI API key (stored securely via OS keyring)
- 🌓 **Light/Dark Mode**: Beautiful UI that adapts to your preference
- 📊 **Real-time Progress**: Live logs and progress tracking for each pipeline step

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

## 📋 Prerequisites

- **Node.js** 18+ and **pnpm** (or npm)
- **Rust** 1.70+ (for Tauri)
- **Python** 3.11+
- **OpenAI API Key** (for generation)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install frontend dependencies
pnpm install

# Install Python backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Development Mode

```bash
# Run in development mode (hot-reload enabled)
pnpm dev
```

This will:
- Start the Vite dev server
- Launch Tauri in development mode
- Run a mock backend for testing UI

### 3. First Run Setup

1. Click the **Settings** button (⚙️) in the header
2. Paste your **OpenAI API Key**
3. Click **Save**
4. Start generating! 🎉

### 4. Production Build

```bash
# Build the complete application
pnpm build
```

This will:
- Build the optimized React frontend
- Compile Python backend to native binary with Nuitka
- Bundle everything into a standalone executable

## 📁 Project Structure

```
AssetForge/
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
- **OS Keyring**: API keys stored securely via platform keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- **Compiled Binary**: Python backend compiled with Nuitka for IP protection
- **No Network Server**: All communication via stdio (no HTTP server exposure)

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

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 💡 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for digital creators**
