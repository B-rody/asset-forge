// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use serde_json::Value;
use std::fs;
use std::path::PathBuf;

// Tauri commands for database queries
#[tauri::command]
async fn get_bundle_history(limit: Option<u32>) -> Result<Value, String> {
    // TODO: In production, this will invoke the Python backend via sidecar
    // For now, return mock data for development
    Ok(serde_json::json!({
        "bundles": [],
        "total": 0
    }))
}

#[tauri::command]
async fn get_bundle_details(bundle_id: String) -> Result<Value, String> {
    // TODO: In production, this will invoke the Python backend via sidecar
    // For now, return mock data for development
    Ok(serde_json::json!({
        "id": bundle_id,
        "status": "completed",
        "mode": "one_click"
    }))
}

#[tauri::command]
async fn get_bundle_stats() -> Result<Value, String> {
    // TODO: In production, this will invoke the Python backend via sidecar
    // For now, return mock data for development
    Ok(serde_json::json!({
        "total": 0,
        "by_status": {},
        "avg_qa_score": null
    }))
}

// Simple settings store using JSON file
#[tauri::command]
async fn get_setting(app_handle: tauri::AppHandle, key: String) -> Result<Option<Value>, String> {
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
async fn set_setting(app_handle: tauri::AppHandle, key: String, value: Value) -> Result<(), String> {
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

fn get_config_path(app_handle: &tauri::AppHandle) -> Result<PathBuf, String> {
    app_handle
        .path_resolver()
        .app_config_dir()
        .map(|p| p.join("settings.json"))
        .ok_or_else(|| "Failed to resolve config directory".to_string())
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_bundle_history,
            get_bundle_details,
            get_bundle_stats,
            get_setting,
            set_setting
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
