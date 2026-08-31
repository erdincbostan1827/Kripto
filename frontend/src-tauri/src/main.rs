#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    // Trading/execution/risk engines intentionally remain server-side. The desktop
    // process is only a presentation shell and exposes no exchange-secret command.
    tauri::Builder::default()
        .plugin(tauri_plugin_notification::init())
        // Signed updater verification is mandatory when updater configuration is supplied.
        .plugin(tauri_plugin_updater::Builder::new().build())
        .run(tauri::generate_context!())
        .expect("desktop shell failed to start");
}
