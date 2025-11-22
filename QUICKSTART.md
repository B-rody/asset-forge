# AssetFurnace - Quick Start Guide

## Prerequisites

Before you begin, ensure you have:

- ✅ **Node.js** 18+ ([download](https://nodejs.org/))
- ✅ **pnpm** (recommended) or npm
  ```powershell
  npm install -g pnpm
  ```
- ✅ **Python** 3.11+ ([download](https://www.python.org/downloads/))
- ✅ **Rust** 1.70+ ([download](https://rustup.rs/))
- ✅ **OpenAI API Key** ([get one](https://platform.openai.com/api-keys))

## Step-by-Step Setup

### 1️⃣ Install Frontend Dependencies

```powershell
# Install all Node.js packages
pnpm install

# This installs:
# - React, TypeScript, Vite
# - Tailwind CSS, shadcn/ui
# - Tauri CLI
# - All UI dependencies
```

⏱️ **Takes:** ~2-3 minutes

### 2️⃣ Install Backend Dependencies

```powershell
# Navigate to backend
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Return to project root
cd ..
```

⏱️ **Takes:** ~3-5 minutes

### 3️⃣ First Run - Development Mode

```powershell
# From project root, run:
pnpm dev
```

This command will:
1. ✅ Start Vite dev server (port 1420)
2. ✅ Compile Rust/Tauri (first time: 5-10 minutes ☕)
3. ✅ Launch the desktop application

**Note:** The first run compiles all Rust dependencies. Subsequent runs are much faster (~10 seconds).

### 4️⃣ Configure Your API Key

Once the app opens:

1. Click the **⚙️ Settings** icon in the top-right
2. Enter your **OpenAI API Key** (starts with `sk-...`)
3. Click **Save**

Your key is now stored securely in Windows Credential Manager.

### 5️⃣ Test the UI

Try the **One-Click** mode:

1. Click the **One-Click** tab in the sidebar
2. Select your AI model (GPT-4o recommended)
3. Click **Generate Bundle**
4. Watch the pipeline execute with real-time logs! 🎉

**Current Status:** MVP mock mode - returns simulated data

## 🎨 UI Overview

### Sidebar Tabs
- **One-Click** - Fully autonomous generation
- **Focused** - Target a specific keyword/niche
- **History** - View previous runs (coming soon)

### Main Panel
- **Pipeline Status** - Visual progress chips for each step
- **Logs** - Real-time output from the backend
- **Results** - Bundle details and download link

### Theme Toggle
Click the 🌙/☀️ icon to switch between light and dark themes.

## 🐍 Backend Development

### Run Backend Standalone

```powershell
# Activate venv
cd backend
.\venv\Scripts\activate

# Run backend directly
python app/main.py

# The backend listens on stdin for JSON commands
```

### Test IPC Manually

Send a command via stdin:
```json
{"cmd":"run_pipeline","mode":"one_click","params":{"model":"gpt-4o"}}
```

You'll see JSON-Lines events printed to stdout.

## 🔧 Common Commands

```powershell
# Development
pnpm dev              # Run full app in dev mode
pnpm ui:dev           # Run frontend only
pnpm backend:dev      # Run backend only

# Building
pnpm ui:build         # Build frontend to ui/dist
pnpm backend:build    # Compile Python to binary with Nuitka
pnpm build            # Build everything + create portable ZIP

# Previewing
pnpm ui:preview       # Preview built frontend
```

## 🏗️ Project Structure

```
AssetFurnace/
├── ui/src/              # React frontend
│   ├── components/      # UI components
│   ├── lib/             # Utilities & IPC
│   └── styles/          # Global CSS
├── src-tauri/           # Tauri/Rust layer
├── backend/app/         # Python backend
│   ├── pipeline/        # AI agents
│   ├── security/        # Crypto & keyring
│   └── schemas/         # JSON validation
└── scripts/             # Build scripts
```

## 🚨 Troubleshooting

### "Cannot find module 'vite'"
**Solution:** Run `pnpm install` first

### "Python module not found"
**Solution:** Activate venv and run `pip install -r requirements.txt`

### Tauri takes forever to compile
**Answer:** First compile takes 5-10 minutes. This is normal! Grab a coffee ☕

### Backend not responding in UI
**Solution:** Check that your OpenAI API key is configured in Settings. The backend communicates via stdio IPC.

### TypeScript errors everywhere
**Solution:** Install dependencies with `pnpm install`. Errors will disappear.

## 🎯 Next Steps

### For Development
1. ✅ Explore the codebase
2. ✅ Modify UI components in `ui/src/components/`
3. ✅ Test agent logic in `backend/app/pipeline/agents/`
4. ✅ Integrate real OpenAI API calls

### For Production
1. ✅ Backend integrated with OpenAI API
2. ✅ Asset generation (PDF, images) working
3. ✅ Tauri communicates with Python backend via stdio
4. ⬜ Add more error handling and retry logic
5. ⬜ Create custom app icons
6. ⬜ Test portable ZIP on different systems

## 📖 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Backend Details**: See [backend/README.md](backend/README.md)
- **Setup Summary**: See [SETUP_SUMMARY.md](SETUP_SUMMARY.md)

## 💬 Need Help?

1. Check the [Tauri Discord](https://discord.gg/tauri)
2. Read [Tauri docs](https://tauri.app/)
3. Review [Vite docs](https://vitejs.dev/)

---

**Happy Building! 🚀**
