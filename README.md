# Heart Rate Overlay for Garmin HRM 200

A Windows 11 desktop app that reads your Garmin HRM 200 chest strap over Bluetooth Low Energy and shows your live heart rate as a small always-on-top overlay for games, plus a local browser overlay for OBS Studio. Everything runs on your PC; no account, subscription, or internet connection is needed.

## Requirements

- Windows 10 or 11 with a Bluetooth LE adapter, and Bluetooth turned on.
- Python 3.11 or newer (only needed if you run from source or build the .exe yourself).

## Run from source

1. Open a Command Prompt in this folder.
2. Install the dependencies:

   ```
   python -m pip install -r requirements.txt
   ```

3. Start the app:

   ```
   python main.py
   ```

## Build a Windows .exe

Double-click `build_exe.bat` or run it from a Command Prompt. When it finishes, `dist\HeartRateOverlay.exe` is a single file you can launch directly or copy anywhere.

## Using the app

1. Wear the HRM 200 and make sure its contacts are moist. Put the strap in its Bluetooth broadcast mode as described in the Garmin manual.
2. Click **Connect Garmin HRM 200**, pick your sensor, and click **Connect**. The sensor is remembered and reconnects automatically on later launches.
3. Click **Show overlay**, then drag it to your preferred corner, or use the quick-position buttons (choose the monitor first if you have several).
4. Turn on **Click-through** (or press the move-mode shortcut) so mouse clicks pass through the overlay during games. Turn it off again to drag.
5. Closing the main window keeps the app running in the system tray. Use the tray menu to quit.

Default shortcuts: `Ctrl+Alt+H` shows or hides the overlay, and `Ctrl+Alt+L` toggles click-through / move mode. Both can be changed in the Overlay card.

## OBS Studio

- **Browser Source (recommended):** Add a Browser Source and paste `http://127.0.0.1:8765/`. Use a size around 400 x 160. The background is transparent, it updates live, and it works offline. The port can be changed in `%APPDATA%\HeartRateOverlay\settings.json`.
- **Window Capture (alternative):** Capture the "Heart Rate Overlay" window. Window capture does not keep the transparent background, so keep the dark background enabled for this method.

## Limitations

- **Exclusive fullscreen:** Games running in exclusive fullscreen block other windows from appearing on top, so the overlay will not show. Set the game to **Borderless Windowed** or **Windowed Fullscreen**, which works reliably.
- **Anti-cheat:** The overlay is a normal Windows window. It does not inject into or modify the game, so it does not interact with Riot Vanguard.
- **Sensor availability:** The app only reads standard Bluetooth Heart Rate broadcasts. If the strap is not worn, is dry, or is not in Bluetooth mode, the sensor will not appear and the overlay shows `--`.
- **Hotkeys:** A shortcut that another program already uses cannot be registered. Pick a different combination in the Overlay card.

## Files

- `main.py`: starts the app, tray icon, and wiring.
- `hr_overlay/ble_monitor.py`: Bluetooth scanning, connection, reconnection, and stale-data handling.
- `hr_overlay/hr_parser.py`: decodes standard heart rate measurement packets.
- `hr_overlay/overlay_window.py`: the floating overlay.
- `hr_overlay/main_window.py`, `appearance_panel.py`, `device_dialog.py`: the control window.
- `hr_overlay/hotkeys.py`: global keyboard shortcuts.
- `hr_overlay/obs_server.py`, `obs_page.py`: local OBS browser overlay.
- `hr_overlay/settings.py`: saves your settings to `%APPDATA%\HeartRateOverlay\settings.json`.
- `tests/test_hr_parser.py`: parser tests (`python -m unittest discover -s tests`).
