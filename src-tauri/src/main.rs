// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, Window, AppHandle, State};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;
use std::process::{Command, Stdio, Child, ChildStdin};
use std::io::{BufRead, BufReader, Write};
use std::sync::Arc;
use parking_lot::Mutex;

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
    backend: State<'_, PythonBackend>,
    command: Value
) -> Result<(), String> {
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
    // Get absolute path to backend directory
    // Tauri runs from src-tauri, so backend is ../backend
    let backend_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current dir: {}", e))?
        .parent()
        .ok_or("Failed to get parent directory")?
        .join("backend");

    println!("Spawning Python backend from: {:?}", backend_dir);

    let mut command = Command::new("python");
    command
        .args(&["-m", "app.main"])
        .current_dir(&backend_dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::inherit()); // Show Python errors in console

    let mut child = command.spawn()
        .map_err(|e| format!("Failed to spawn Python backend: {}", e))?;

    let stdin = child.stdin.take()
        .ok_or("Failed to capture Python stdin")?;

    let stdout = child.stdout.take()
        .ok_or("Failed to capture Python stdout")?;

    // Spawn background task to read from Python stdout
    let window_clone = window.clone();
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            match line {
                Ok(line) => {
                    // Parse JSON event
                    match serde_json::from_str::<Value>(&line) {
                        Ok(event) => {
                            // Emit event to frontend
                            if let Err(e) = window_clone.emit("backend_event", event) {
                                eprintln!("Failed to emit backend event: {}", e);
                            }
                        }
                        Err(e) => {
                            eprintln!("Failed to parse backend event: {} (line: {})", e, line);
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Error reading from Python stdout: {}", e);
                    break;
                }
            }
        }
        println!("Python stdout reader thread exiting");
    });

    Ok(PythonBackend {
        stdin: Arc::new(Mutex::new(Some(stdin))),
        _process: Arc::new(Mutex::new(Some(child))),
    })
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            let window = app.get_window("main").unwrap();

            #[cfg(debug_assertions)]
            {
                window.open_devtools();
            }

            // Spawn Python backend
            let backend = spawn_python_backend(window.clone())?;
            app.manage(backend);

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
