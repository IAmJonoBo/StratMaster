// StratMaster Desktop Library
// Shared functionality for the Tauri application

pub mod system;
pub mod bridge;

use serde::{Deserialize, Serialize};

// Application configuration structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub api_base_url: String,
    pub auto_start_services: bool,
    pub theme: String,
    pub hardware_profile: HardwareProfile,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum HardwareProfile {
    HighPerformance,
    Standard,
    Lightweight,
    Custom(CustomHardwareConfig),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CustomHardwareConfig {
    pub max_memory_mb: u64,
    pub cpu_threads: usize,
    pub enable_gpu: bool,
    pub model_preference: String,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            api_base_url: "http://localhost:8080".to_string(),
            auto_start_services: false,
            theme: "auto".to_string(),
            hardware_profile: HardwareProfile::Standard,
        }
    }
}

// Error types for the application
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("API connection failed: {0}")]
    ApiConnectionFailed(String),
    
    #[error("Configuration error: {0}")]
    ConfigError(String),
    
    #[error("File system error: {0}")]
    FileSystemError(String),
    
    #[error("System detection error: {0}")]
    SystemDetectionError(String),
}

pub type Result<T> = std::result::Result<T, AppError>;