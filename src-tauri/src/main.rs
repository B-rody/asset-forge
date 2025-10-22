// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, Window, AppHandle, State};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio, Child, ChildStdin, ChildStderr};
use std::io::{BufRead, BufReader, Write};
use std::sync::Arc;
use parking_lot::Mutex;
use log::{error, info, LevelFilter};
use simplelog::{WriteLogger, Config as LogConfig};
use chrono::Local;

// State to manage Python backend process
struct PythonBackend {
    stdin: Arc<Mutex<Option<ChildStdin>>>,
    _process: Arc<Mutex<Option<Child>>>,
}

// Tauri commands for database queries (mock for now)
#[tauri::command]
async fn get_bundle_history(_limit: Option<u32>) -> Result<Value, String> {
    Ok(serde_json::json!({
        "bundles": [],
        "total": 0
    }))
}

#[tauri::command]
async fn get_bundle_details(bundle_id: String) -> Result<Value, String> {
    Ok(serde_json::json!({
        "id": bundle_id,
        "status": "completed",
        "mode": "one_click"
    }))
}

#[tauri::command]
async fn get_bundle_stats() -> Result<Value, String> {
    Ok(serde_json::json!({
        "total": 0,
        "by_status": {},
        "avg_qa_score": null
    }))
}

// Simple settings store using JSON file
#[tauri::command]
async fn get_setting(app_handle: AppHandle, key: String) -> Result<Option<Value>, String> {
    let config_path = get_config_path(&app_handle)?;
    if !config_path.exists() {
        return Ok(None);
    }

    let contents = fs::read_to_string(&config_path)
        .map_err(|e| e.to_string())?;
    let settings: Value = serde_json::from_str(&contents)
        .map_err(|e| e.to_string())?;

    Ok(settings.get(&key).cloned())
}

#[tauri::command]
async fn set_setting(app_handle: AppHandle, key: String, value: Value) -> Result<(), String> {
    let config_path = get_config_path(&app_handle)?;

    // Create parent directory if it doesn't exist
    if let Some(parent) = config_path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    // Read existing settings or create new
    let mut settings = if config_path.exists() {
        let contents = fs::read_to_string(&config_path)
            .map_err(|e| e.to_string())?;
        serde_json::from_str(&contents)
            .unwrap_or_else(|_| serde_json::json!({}))
    } else {
        serde_json::json!({})
    };

    // Update setting
    if let Some(obj) = settings.as_object_mut() {
        obj.insert(key, value);
    }

    // Write back to file
    let contents = serde_json::to_string_pretty(&settings)
        .map_err(|e| e.to_string())?;
    fs::write(&config_path, contents)
        .map_err(|e| e.to_string())?;

    Ok(())
}

fn get_config_path(app_handle: &AppHandle) -> Result<PathBuf, String> {
    app_handle
        .path_resolver()
        .app_config_dir()
        .map(|p| p.join("settings.json"))
        .ok_or_else(|| "Failed to resolve config directory".to_string())
}

// Send command to Python backend via stdin
#[tauri::command]
async fn send_to_backend(
    backend: State<'_, Option<PythonBackend>>,
    command: Value
) -> Result<(), String> {
    // Check if backend is available
    let backend = backend.inner().as_ref()
        .ok_or("Backend is offline")?;

    let mut stdin_guard = backend.stdin.lock();

    if let Some(stdin) = stdin_guard.as_mut() {
        // Serialize command to JSON-Lines format
        let json_line = serde_json::to_string(&command)
            .map_err(|e| format!("Failed to serialize command: {}", e))?;

        // Write to Python stdin
        writeln!(stdin, "{}", json_line)
            .map_err(|e| format!("Failed to write to Python backend: {}", e))?;

        stdin.flush()
            .map_err(|e| format!("Failed to flush stdin: {}", e))?;

        Ok(())
    } else {
        Err("Python backend not connected".to_string())
    }
}

fn spawn_python_backend(window: Window) -> Result<PythonBackend, String> {
    #[cfg(debug_assertions)]
    {
        // DEV MODE: Run Python directly from source
        let backend_dir = std::env::current_dir()
            .map_err(|e| format!("Failed to get current dir: {}", e))?
            .parent()
            .ok_or("Failed to get parent directory")?
            .join("backend");

        info!("DEV MODE: Spawning Python backend from: {:?}", backend_dir);

        let mut command = Command::new("python");
        command
            .args(&["-m", "app.main"])
            .current_dir(&backend_dir)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let mut child = command.spawn()
            .map_err(|e| format!("Failed to spawn Python backend: {}", e))?;

        let stdin = child.stdin.take()
            .ok_or("Failed to capture Python stdin")?;

        let stdout = child.stdout.take()
            .ok_or("Failed to capture Python stdout")?;

        let stderr = child.stderr.take()
            .ok_or("Failed to capture Python stderr")?;

        spawn_output_reader(window, stdout);
        spawn_stderr_logger(stderr);

        return Ok(PythonBackend {
            stdin: Arc::new(Mutex::new(Some(stdin))),
            _process: Arc::new(Mutex::new(Some(child))),
        });
    }

    #[cfg(not(debug_assertions))]
    {
        // PRODUCTION MODE: Run compiled backend from resources
        let app_handle = window.app_handle();

        // Try to resolve resource - Tauri extracts to _up_ directory on Windows
        let resource_path = app_handle
            .path_resolver()
            .resolve_resource("_up_/backend/bin/assetforge_backend.exe")
            .or_else(|| {
                // Fallback: try without _up_ prefix (for other platforms)
                app_handle.path_resolver().resolve_resource("backend/bin/assetforge_backend.exe")
            })
            .ok_or("Failed to resolve backend binary path. Tried: _up_/backend/bin/assetforge_backend.exe")?;

        info!("PRODUCTION MODE: Spawning backend from: {:?}", resource_path);

        let mut command = Command::new(&resource_path);
        command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        let mut child = command.spawn()
            .map_err(|e| format!("Failed to spawn backend binary: {}", e))?;

        let stdin = child.stdin.take()
            .ok_or("Failed to capture backend stdin")?;

        let stdout = child.stdout.take()
            .ok_or("Failed to capture backend stdout")?;

        let stderr = child.stderr.take()
            .ok_or("Failed to capture backend stderr")?;

        spawn_output_reader(window, stdout);
        spawn_stderr_logger(stderr);

        return Ok(PythonBackend {
            stdin: Arc::new(Mutex::new(Some(stdin))),
            _process: Arc::new(Mutex::new(Some(child))),
        });
    }
}

fn spawn_output_reader(window: Window, stdout: std::process::ChildStdout) {
    // Spawn background task to read from backend stdout
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    // Parse JSON event
                    match serde_json::from_str::<Value>(&line) {
                        Ok(event) => {
                            // Emit event to frontend
                            if let Err(e) = window.emit("backend_event", event) {
                                error!("Failed to emit backend event: {}", e);
                            }
                        }
                        Err(e) => {
                            error!("Failed to parse backend event: {} (line: {})", e, line);
                        }
                    }
                }
                Err(e) => {
                    error!("Error reading from backend stdout: {}", e);
                    break;
                }
            }
        }
        info!("Backend stdout reader thread exiting");
    });
}

fn spawn_stderr_logger(stderr: ChildStderr) {
    // Spawn background task to log backend stderr
    std::thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    error!("Backend stderr: {}", line);
                }
                Err(e) => {
                    error!("Error reading backend stderr: {}", e);
                    break;
                }
            }
        }
    });
}

fn setup_logging(app_handle: &AppHandle) -> Result<(), String> {
    // Get logs directory
    let app_data = app_handle
        .path_resolver()
        .app_data_dir()
        .ok_or("Failed to resolve app data directory")?;

    let logs_dir = app_data.join("logs");
    fs::create_dir_all(&logs_dir)
        .map_err(|e| format!("Failed to create logs directory: {}", e))?;

    // Create log file with current date
    let date = Local::now().format("%Y-%m-%d").to_string();
    let log_file_path = logs_dir.join(format!("{}.log", date));

    let log_file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_file_path)
        .map_err(|e| format!("Failed to open log file: {}", e))?;

    // Setup logger
    WriteLogger::init(LevelFilter::Info, LogConfig::default(), log_file)
        .map_err(|e| format!("Failed to initialize logger: {}", e))?;

    Ok(())
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Setup logging first
            if let Err(e) = setup_logging(&app.handle()) {
                eprintln!("Warning: Failed to setup logging: {}", e);
            }

            info!("AssetForge v1.0.4 starting");

            let window = app.get_window("main")
                .ok_or("Failed to get main window")?;

            #[cfg(debug_assertions)]
            {
                window.open_devtools();
            }

            // Spawn Python backend (non-fatal if it fails)
            match spawn_python_backend(window.clone()) {
                Ok(backend) => {
                    info!("Backend spawned successfully");
                    app.manage(Some(backend));
                }
                Err(e) => {
                    error!("Failed to spawn backend: {}", e);
                    // Show error dialog but continue launching
                    let _ = tauri::api::dialog::message(
                        Some(&window),
                        "AssetForge - Backend Error",
                        format!(
                            "Failed to start backend process:\n\n{}\n\nThe app will run in limited mode. Check logs at:\n%APPDATA%\\AssetForge\\logs\\",
                            e
                        )
                    );
                    // Store None to indicate backend is offline
                    app.manage(None::<PythonBackend>);
                }
            };

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_bundle_history,
            get_bundle_details,
            get_bundle_stats,
            get_setting,
            set_setting,
            send_to_backend
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
