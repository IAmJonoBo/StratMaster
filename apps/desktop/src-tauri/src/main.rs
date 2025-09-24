// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use log::{info, warn, error};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use tauri::{AppHandle, Manager, State, Window};

// External dependencies
use sys_info;
use num_cpus;
use webbrowser;

// Application state for managing backend connections
#[derive(Default)]
struct AppState {
    api_base_url: std::sync::Mutex<String>,
    health_status: std::sync::Mutex<HashMap<String, bool>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct HealthResponse {
    status: String,
    services: Option<HashMap<String, String>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct SystemInfo {
    platform: String,
    arch: String,
    cpu_count: usize,
    memory_total: u64,
    has_gpu: bool,
    recommended_config: String,
}

// Tauri commands for frontend-backend communication

#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String> {
    info!("Getting system information");
    
    let platform = std::env::consts::OS.to_string();
    let arch = std::env::consts::ARCH.to_string();
    let cpu_count = num_cpus::get();
    
    // Estimate memory (simplified)
    let memory_total = match sys_info::mem_info() {
        Ok(mem) => mem.total * 1024, // Convert KB to bytes
        Err(_) => 8_000_000_000, // Default to 8GB
    };
    
    // GPU detection (simplified - would need platform-specific implementations)
    let has_gpu = std::env::var("CUDA_VISIBLE_DEVICES").is_ok() || 
                  std::env::var("GPU_DEVICE").is_ok();
    
    // Recommend configuration based on specs
    let recommended_config = if memory_total > 16_000_000_000 && has_gpu {
        "high-performance".to_string()
    } else if memory_total > 8_000_000_000 {
        "standard".to_string()
    } else {
        "lightweight".to_string()
    };
    
    Ok(SystemInfo {
        platform,
        arch,
        cpu_count,
        memory_total,
        has_gpu,
        recommended_config,
    })
}

#[tauri::command]
async fn check_api_health(state: State<'_, AppState>) -> Result<HealthResponse, String> {
    let base_url = state.api_base_url.lock().unwrap().clone();
    let health_url = if base_url.is_empty() {
        "http://localhost:8080/healthz".to_string()
    } else {
        format!("{}/healthz", base_url)
    };
    
    info!("Checking API health at: {}", health_url);
    
    match reqwest::get(&health_url).await {
        Ok(response) => {
            if response.status().is_success() {
                match response.json::<HealthResponse>().await {
                    Ok(health) => {
                        info!("API health check successful: {:?}", health);
                        Ok(health)
                    }
                    Err(e) => {
                        warn!("Failed to parse health response: {}", e);
                        Err(format!("Failed to parse health response: {}", e))
                    }
                }
            } else {
                let error_msg = format!("API health check failed with status: {}", response.status());
                warn!("{}", error_msg);
                Err(error_msg)
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to connect to API: {}", e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}

#[tauri::command]
async fn set_api_base_url(state: State<'_, AppState>, url: String) -> Result<(), String> {
    info!("Setting API base URL to: {}", url);
    *state.api_base_url.lock().unwrap() = url;
    Ok(())
}

#[tauri::command]
async fn get_app_data_dir(app: AppHandle) -> Result<String, String> {
    match app.path().app_data_dir() {
        Ok(path) => {
            let path_str = path.to_string_lossy().to_string();
            info!("App data directory: {}", path_str);
            Ok(path_str)
        }
        Err(e) => {
            let error_msg = format!("Failed to get app data directory: {}", e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}

#[tauri::command]
async fn open_external_url(url: String) -> Result<(), String> {
    info!("Opening external URL: {}", url);
    
    match webbrowser::open(&url) {
        Ok(_) => Ok(()),
        Err(e) => {
            let error_msg = format!("Failed to open URL: {}", e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}

#[tauri::command] 
async fn show_file_in_folder(path: String) -> Result<(), String> {
    info!("Showing file in folder: {}", path);
    
    let path_buf = PathBuf::from(&path);
    if !path_buf.exists() {
        return Err(format!("File does not exist: {}", path));
    }
    
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .args(["/select,", &path])
            .spawn()
            .map_err(|e| format!("Failed to open explorer: {}", e))?;
    }
    
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .args(["-R", &path])
            .spawn()
            .map_err(|e| format!("Failed to open finder: {}", e))?;
    }
    
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(path_buf.parent().unwrap_or(&path_buf))
            .spawn()
            .map_err(|e| format!("Failed to open file manager: {}", e))?;
    }
    
    Ok(())
}

#[tauri::command]
async fn get_local_server_status() -> Result<HashMap<String, bool>, String> {
    let mut status = HashMap::new();
    
    // Check common local services
    let services = vec![
        ("api", "http://localhost:8080/healthz"),
        ("research-mcp", "http://localhost:8081/health"),  
        ("knowledge-mcp", "http://localhost:8082/health"),
        ("router-mcp", "http://localhost:8083/health"),
    ];
    
    for (service, url) in services {
        let is_healthy = match reqwest::get(url).await {
            Ok(response) => response.status().is_success(),
            Err(_) => false,
        };
        status.insert(service.to_string(), is_healthy);
    }
    
    Ok(status)
}

// Window management
#[tauri::command]
async fn toggle_devtools(window: Window) {
    if window.is_devtools_open() {
        let _ = window.close_devtools();
    } else {
        let _ = window.open_devtools();
    }
}

fn main() {
    env_logger::init();
    info!("Starting StratMaster Desktop Application");
    
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            get_system_info,
            check_api_health,
            set_api_base_url, 
            get_app_data_dir,
            open_external_url,
            show_file_in_folder,
            get_local_server_status,
            toggle_devtools
        ])
        .setup(|app| {
            info!("Application setup complete");
            
            // Set default API base URL
            let state: State<AppState> = app.state();
            *state.api_base_url.lock().unwrap() = "http://localhost:8080".to_string();
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}