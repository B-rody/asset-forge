# AssetForge Backend

This directory contains the Python backend for AssetForge.

## Structure

- `app/` - Main application code
  - `main.py` - Entry point for stdio IPC loop
  - `ipc.py` - JSON-Lines IPC communication layer
  - `logger.py` - Logging configuration
  - `settings.py` - Application settings
  - `pipeline/` - Pipeline agents and orchestrator
    - `orchestrator.py` - Pipeline coordinator
    - `agents/` - Individual pipeline agents
      - `researcher.py` - Market research agent
      - `planner.py` - Bundle planning agent
      - `maker.py` - Asset generation agent
      - `packager.py` - Final packaging agent
    - `paths.py` - Path utilities
  - `security/` - Security modules
    - `crypto.py` - Encryption utilities
    - `keyring_store.py` - Secure API key storage
    - `license_gate.py` - License validation (placeholder)
  - `schemas/` - JSON schemas for validation
  - `prompts/blobs/` - Encrypted prompt templates

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate.bat

# Activate (Unix/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run in Development Mode

```bash
# Run directly
python app/main.py

# Or use the dev script (Windows)
scripts\dev_backend.bat

# Or use the dev script (Unix/Mac)
./scripts/dev_backend.sh
```

### Build Production Binary

```bash
# Install build dependencies
pip install nuitka ordered-set zstandard

# Build with Nuitka (Windows)
scripts\build_backend.bat

# Build with Nuitka (Unix/Mac)
./scripts/build_backend.sh

# Or use npm script
npm run backend:build
```

## IPC Protocol

The backend communicates with the frontend via JSON-Lines over stdio.

### Commands (Frontend → Backend)

```json
{"cmd":"run_pipeline","mode":"one_click","params":{"model":"gpt-4o"}}
{"cmd":"run_pipeline","mode":"focused","params":{"keyword":"notion templates"}}
{"cmd":"re_run_step","params":{"bundle_id":"2025-10-07-bundle","step":"maker"}}
```

### Events (Backend → Frontend)

```json
{"event":"log","step":"Researcher","message":"Starting research..."}
{"event":"progress","step":"Planner","pct":50}
{"event":"qa","status":"pass","score":0.93}
{"event":"done","result":{"bundle_id":"...","output_path":"..."}}
{"event":"error","step":"Maker","message":"Error message"}
```

## Security

- API keys stored in OS keyring (Windows Credential Manager, macOS Keychain, Linux Secret Service)
- Prompts encrypted at rest with Fernet (AES-128)
- Backend compiled with Nuitka for IP protection

## License

MIT
