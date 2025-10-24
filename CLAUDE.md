# 🧠 AssetForge — Autonomous Digital Asset Factory

---

## Executive Summary

**AssetForge** is a local, offline-first **AI production line** that autonomously researches, designs, and produces ready-to-sell **digital product bundles** — such as Notion templates, AI prompt packs, or productivity kits.

It’s designed for independent creators who want to generate marketplace-ready digital assets **without coding**, using their own OpenAI API key (**BYOL**).

Each product run passes through a structured 4-stage AI pipeline:

1. **Researcher** – finds profitable niches and product opportunities  
2. **Bundle Planner** – designs the digital bundle structure, personas, and pricing  
3. **Asset Maker** – generates the assets, visuals, and store metadata  
4. **Packager** – merges outputs into a ready-to-publish bundle ZIP  

All processing happens **locally** in a secure, compiled Python backend — surfaced through a **modern Tauri desktop interface** built with React, Tailwind, and shadcn/ui.

---

## 🎯 Goal

To deliver a **click-to-create desktop app** that automates every step of digital product creation — from market research to publishable bundle — while keeping user data and API keys completely local.

---

## 🧩 System Architecture

```
[Tauri Frontend (React + Tailwind)]  ⇄  [Python Sidecar (compiled with Nuitka)]
```

### Frontend (Tauri + React + Tailwind + shadcn/ui)
- Provides a clean, modern desktop interface
- Shows progress, logs, and bundle previews
- Stores user settings locally (API key, output folder)
- Communicates with backend using **JSON-Lines via stdio IPC**

### Backend (Python Sidecar)
- Runs all AI logic and agent orchestration
- Executes the pipeline:  
  **Researcher → Bundle Planner → Asset Maker → Packager**
- Uses the **OpenAI Agents SDK** for orchestration and reasoning
- All prompts and schemas are validated and encrypted at rest
- Compiled to a sealed binary with **Nuitka** for IP protection

---

## 🔄 Pipeline Overview

| Step | Agent | Purpose | Output |
|------|--------|----------|--------|
| 1️⃣ | **Researcher** | Finds and prioritizes profitable digital niches | `researcher_output.json` |
| 2️⃣ | **Bundle Planner** | Designs the product bundle structure, personas, and pricing | `planner_output.json` |
| 3️⃣ | **Asset Maker** | Generates digital assets, visuals, and metadata for Etsy/Gumroad | `/maker_output/*`, `qa_report.json` |
| 4️⃣ | **Packager** | Combines all assets + metadata into a ready-to-publish bundle | `/packager_output/*`, `final_bundle.zip` |

---

## 📁 Example Output Structure

```
/data/2025-10-07-focus-planner/
├── researcher_output.json
├── planner_output.json
├── maker_output/
│   ├── asset_01.pdf
│   ├── asset_02.md
│   ├── metadata_etsy.json
│   └── metadata_gumroad.json
├── packager_output/
│   ├── final_bundle.zip
│   └── bundle_metadata.json
└── qa_report.json
```

**Deliverables per run**
- 1–3 sellable assets  
- Store metadata for Etsy and Gumroad  
- QA report for compliance and quality  
- Optional promotional copy (future feature)

---

## 🛰 IPC Contract (Frontend ⇄ Backend)

### Frontend → Backend (commands)
```json
{"cmd":"run_pipeline","mode":"one_click","params":{"model":"gpt-5-mini","reasoning":"normal"}}
{"cmd":"run_pipeline","mode":"focused","params":{"keyword":"notion templates"}}
{"cmd":"re_run_step","params":{"bundle_id":"2025-10-07-focus-journal","step":"maker"}}
```

### Backend → Frontend (events)
```json
{"event":"log","step":"Researcher","message":"Scanning marketplaces..."}
{"event":"progress","step":"Planner","pct":25}
{"event":"qa","status":"pass","score":0.93}
{"event":"done","result":{"bundle_id":"2025-10-07-focus-journal","output_path":"..."}}
{"event":"error","step":"Maker","message":"Validation failed"}
```

All communication is **local only** — no HTTP server or open ports.  
The backend reads JSON commands from `stdin` and writes JSON events to `stdout`.

---

## 🧱 Project Structure

```
AssetForge/
  README.md
  LICENSE
  .gitignore
  scripts/
    build_backend.(bat|sh)
    dev_backend.(bat|sh)
  ui/
    index.html
    src/
      main.tsx
      App.tsx
      components/
        AppShell.tsx
        Sidebar.tsx
        HeaderBar.tsx
        RunPanel.tsx
        ResultPanel.tsx
        StepChips.tsx
        LogStream.tsx
        SettingsDialog.tsx
      lib/ipc.ts
      styles/globals.css
  src-tauri/
    tauri.conf.json
    Cargo.toml
    src/main.rs
  backend/
    pyproject.toml
    nuitka.config.json
    bin/
    app/
      main.py
      ipc.py
      logger.py
      settings.py
      security/
        crypto.py
        license_gate.py
        keyring_store.py
      pipeline/
        orchestrator.py
        agents/
          researcher.py
          planner.py
          maker.py
          packager.py
        paths.py
      prompts/blobs/
      schemas/
        researcher.schema.json
        planner.schema.json
        maker.schema.json
        packager.schema.json
        qa_report.schema.json
```

---

## ⚙️ Dependencies

### Frontend
```
vite react react-dom typescript
tailwindcss postcss autoprefixer
@tauri-apps/api @tauri-apps/cli
clsx lucide-react
@radix-ui/react-dialog @radix-ui/react-tabs @radix-ui/react-dropdown-menu
shadcn/ui
```

### Backend (Python)
```
openai openai-agents
pydantic orjson jsonschema tenacity
cryptography keyring platformdirs rich python-dateutil
```

### Build Tools
```
nuitka ordered-set zstandard
```

---

## 🪄 Development & Build Flow

### Dev (uncompiled backend)
```bash
pnpm install
pnpm dev  # launches Tauri + Python backend (scripts/dev_backend)
```

### Build (compiled backend)
```bash
pnpm build  # runs Nuitka -> bundles app
```

### Backend Build Scripts
`scripts/build_backend.(bat|sh)`  
Compiles backend with Nuitka:

```bash
python -m nuitka --onefile --standalone --follow-imports   --enable-plugin=pyside6=disabled   --output-dir backend/bin backend/app/main.py
```

Tauri runs this before packaging via:

```json
"build": { "beforeBuildCommand": "pnpm --filter ui build && scripts/build_backend.sh" }
```

---

## 🔒 Security Model

- All prompts stored encrypted (`/prompts/blobs/`)
- AES/Fernet decryption only in memory
- API key stored in an encrypted file on local device, managed by the app
- No cloud sync; all data remains local
- No AssetForge servers; API key only transmitted to OpenAI
- Compiled binary hides all logic & prompts

---

## 🧠 Agents SDK Integration

The **OpenAI Agents SDK** runs inside the backend Python environment.

- In dev: use a local `venv` or `uv` virtual environment  
- In production: Nuitka bundles the SDK and dependencies into one executable  
- Works seamlessly with the `Runner.run()` model  
- No runtime dependency on external services beyond OpenAI’s API
