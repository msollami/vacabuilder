use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;
use reqwest;

struct PythonProcess(Mutex<Option<Child>>);

#[tauri::command]
fn get_backend_url() -> String {
    "http://127.0.0.1:8000".to_string()
}

#[tauri::command]
async fn fetch_backend(url: String, method: String, body: Option<String>) -> Result<String, String> {
    let client = reqwest::Client::new();

    let request = match method.as_str() {
        "GET" => client.get(&url),
        "POST" => {
            let mut req = client.post(&url);
            if let Some(body_content) = body {
                req = req.header("Content-Type", "application/json").body(body_content);
            }
            req
        }
        _ => return Err(format!("Unsupported method: {}", method)),
    };

    let response = request
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let status = response.status();
    let text = response.text().await.map_err(|e| e.to_string())?;

    if status.is_success() {
        Ok(text)
    } else {
        Err(format!("HTTP {}: {}", status.as_u16(), text))
    }
}

#[tauri::command]
async fn open_file(path: String) -> Result<(), String> {
    open_pdf(path).await
}

#[tauri::command]
async fn open_pdf(path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args(&["/C", "start", "", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}

fn start_python_backend(app: &tauri::App) -> Result<Child, String> {
    // In development mode, use the backend directory relative to the project root
    // In production, use the bundled backend from the resource directory
    let backend_path = if cfg!(debug_assertions) {
        // Development mode - backend is in project root
        std::env::current_dir()
            .map_err(|e| e.to_string())?
            .parent()
            .ok_or("Failed to get parent directory")?
            .join("backend")
    } else {
        // Production mode - backend is bundled in resources
        app.path()
            .resource_dir()
            .map_err(|e| e.to_string())?
            .join("backend")
    };

    let venv_python = if cfg!(target_os = "windows") {
        backend_path.join("venv").join("Scripts").join("python.exe")
    } else {
        backend_path.join("venv").join("bin").join("python")
    };

    let main_py = backend_path.join("main.py");

    println!("Starting Python backend at: {:?}", main_py);
    println!("Using Python at: {:?}", venv_python);

    let child = Command::new(venv_python)
        .arg(main_py)
        .current_dir(backend_path)
        .spawn()
        .map_err(|e| format!("Failed to start Python backend: {}", e))?;

    Ok(child)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Start Python backend
            match start_python_backend(app) {
                Ok(child) => {
                    app.manage(PythonProcess(Mutex::new(Some(child))));
                    println!("Python backend started successfully");
                }
                Err(e) => {
                    eprintln!("Failed to start Python backend: {}", e);
                    // Continue anyway - backend might be started separately in dev mode
                    app.manage(PythonProcess(Mutex::new(None)));
                }
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            open_pdf,
            fetch_backend,
            open_file
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                // Kill Python process when app closes
                if let Some(process_state) = window.app_handle().try_state::<PythonProcess>() {
                    if let Ok(mut process) = process_state.0.lock() {
                        if let Some(mut child) = process.take() {
                            let _ = child.kill();
                            println!("Python backend stopped");
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
