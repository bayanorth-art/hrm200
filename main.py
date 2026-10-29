import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from hr_overlay.ble_monitor import HeartRateMonitor
from hr_overlay.heart_icon import heart_pixmap
from hr_overlay.main_window import MainWindow
from hr_overlay.obs_server import ObsOverlayServer, build_obs_state
from hr_overlay.overlay_window import OverlayWindow
from hr_overlay.settings import load_settings

APP_NAME = "Heart Rate Overlay"
TRAY_HEART_COLOR = "#E53935"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    settings = load_settings()
    monitor = HeartRateMonitor()
    overlay = OverlayWindow(settings)
    obs = ObsOverlayServer(settings.obs_port, lambda: build_obs_state(monitor.snapshot(), settings))
    obs.start()
    window = MainWindow(settings, monitor, overlay, obs)

    tray = QSystemTrayIcon(QIcon(heart_pixmap(64, TRAY_HEART_COLOR)), app)
    tray.setToolTip(APP_NAME)
    menu = QMenu()
    open_action = menu.addAction("Open window")
    overlay_action = menu.addAction("Show overlay")
    menu.addSeparator()
    quit_action = menu.addAction("Quit")
    tray.setContextMenu(menu)

    def show_window() -> None:
        window.show()
        window.raise_()
        window.activateWindow()

    def on_tray_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            show_window()

    def quit_app() -> None:
        window.allow_close = True
        app.quit()

    def shutdown() -> None:
        window.shutdown()
        monitor.stop()
        obs.stop()
        tray.hide()

    open_action.triggered.connect(show_window)
    overlay_action.triggered.connect(overlay.toggle_visibility)
    overlay.visibility_changed.connect(lambda visible: overlay_action.setText("Hide overlay" if visible else "Show overlay"))
    quit_action.triggered.connect(quit_app)
    tray.activated.connect(on_tray_activated)
    monitor.reading_changed.connect(lambda bpm: tray.setToolTip(f"{APP_NAME}: {bpm} BPM" if bpm is not None else APP_NAME))
    app.aboutToQuit.connect(shutdown)

    monitor.start()
    if settings.sensor_address:
        monitor.connect_sensor(settings.sensor_address, settings.sensor_name or settings.sensor_address)

    tray.show()
    window.show()
    overlay.restore()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
