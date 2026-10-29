from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from hr_overlay.appearance_panel import AppearancePanel
from hr_overlay.ble_monitor import HeartRateMonitor
from hr_overlay.device_dialog import DeviceDialog
from hr_overlay.hotkeys import HotkeyManager
from hr_overlay.obs_server import ObsOverlayServer
from hr_overlay.overlay_window import CORNERS, OverlayWindow
from hr_overlay.settings import Settings, save_settings
from hr_overlay.ui_kit import APP_STYLESHEET, make_card, muted_label

CORNER_LABELS = {
    "top_left": "Top left",
    "top_right": "Top right",
    "bottom_left": "Bottom left",
    "bottom_right": "Bottom right",
}
HOTKEY_FAILED_NOTICE = "One of the keyboard shortcuts could not be registered. It may already be used by another app."


class MainWindow(QWidget):
    def __init__(self, settings: Settings, monitor: HeartRateMonitor, overlay: OverlayWindow, obs: ObsOverlayServer) -> None:
        super().__init__()
        self.allow_close = False
        self._s = settings
        self._monitor = monitor
        self._overlay = overlay
        self._hotkeys = HotkeyManager(self._on_hotkey)
        QApplication.instance().installNativeEventFilter(self._hotkeys)

        self.setObjectName("root")
        self.setWindowTitle("Heart Rate Overlay")
        self.setMinimumWidth(480)
        self.resize(500, 780)
        self.setStyleSheet(APP_STYLESHEET)

        self._notice = QLabel()
        self._notice.setObjectName("notice")
        self._notice.setWordWrap(True)
        self._notice.hide()

        content = QWidget()
        content.setObjectName("root")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(self._notice)
        layout.addWidget(self._build_sensor_card())
        layout.addWidget(self._build_overlay_card())
        self._appearance = AppearancePanel(settings)
        self._appearance.changed.connect(self._on_appearance_changed)
        layout.addWidget(self._appearance)
        layout.addWidget(self._build_obs_card(obs))
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        monitor.reading_changed.connect(self._on_reading)
        monitor.status_changed.connect(self._on_status)
        monitor.error_occurred.connect(self._on_bluetooth_error)
        overlay.visibility_changed.connect(self._on_overlay_visibility)
        app = QGuiApplication.instance()
        app.screenAdded.connect(self._refresh_monitors)
        app.screenRemoved.connect(self._refresh_monitors)

        self._refresh_monitors()
        self._refresh_sensor_label()
        self._on_status(monitor.snapshot()["status"])
        self._register_hotkeys()

    def shutdown(self) -> None:
        self._hotkeys.unregister_all()
        QApplication.instance().removeNativeEventFilter(self._hotkeys)

    def closeEvent(self, event) -> None:
        if self.allow_close:
            event.accept()
        else:
            event.ignore()
            self.hide()

    def _build_sensor_card(self) -> QFrame:
        card, layout = make_card("Garmin HRM 200")

        top = QHBoxLayout()
        bpm_column = QVBoxLayout()
        bpm_column.setSpacing(0)
        self._bpm_value = QLabel("--")
        self._bpm_value.setObjectName("bpmValue")
        bpm_column.addWidget(self._bpm_value)
        bpm_column.addWidget(muted_label("BPM"))
        top.addLayout(bpm_column)
        top.addStretch(1)
        self._status_pill = QLabel("Disconnected")
        self._status_pill.setObjectName("statusPill")
        top.addWidget(self._status_pill, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        self._sensor_label = muted_label("")
        layout.addWidget(self._sensor_label)
        self._bluetooth_message = QLabel()
        self._bluetooth_message.setObjectName("warning")
        self._bluetooth_message.setWordWrap(True)
        self._bluetooth_message.hide()
        layout.addWidget(self._bluetooth_message)

        buttons = QHBoxLayout()
        connect_button = QPushButton("Connect Garmin HRM 200")
        connect_button.setObjectName("primary")
        connect_button.setCursor(Qt.CursorShape.PointingHandCursor)
        connect_button.clicked.connect(self._open_device_dialog)
        self._forget_button = QPushButton("Forget sensor")
        self._forget_button.clicked.connect(self._forget_sensor)
        buttons.addWidget(connect_button)
        buttons.addWidget(self._forget_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return card

    def _build_overlay_card(self) -> QFrame:
        card, layout = make_card("Overlay")

        self._toggle_button = QPushButton()
        self._toggle_button.setObjectName("primary")
        self._toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_button.clicked.connect(self._overlay.toggle_visibility)
        layout.addWidget(self._toggle_button)

        layout.addWidget(muted_label("Quick position"))
        monitor_row = QHBoxLayout()
        monitor_row.addWidget(QLabel("Monitor"))
        self._monitor_combo = QComboBox()
        monitor_row.addWidget(self._monitor_combo, 1)
        layout.addLayout(monitor_row)

        corners = QGridLayout()
        corners.setHorizontalSpacing(8)
        corners.setVerticalSpacing(8)
        for index, corner in enumerate(CORNERS):
            button = QPushButton(CORNER_LABELS[corner])
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, c=corner: self._place_overlay(c))
            corners.addWidget(button, index // 2, index % 2)
        layout.addLayout(corners)

        layout.addWidget(muted_label("Keyboard shortcuts"))
        shortcuts = QGridLayout()
        shortcuts.setHorizontalSpacing(12)
        shortcuts.setVerticalSpacing(8)
        self._visibility_key = QKeySequenceEdit(QKeySequence(self._s.hotkey_visibility))
        self._visibility_key.keySequenceChanged.connect(lambda seq: self._set_hotkey("hotkey_visibility", seq))
        self._click_key = QKeySequenceEdit(QKeySequence(self._s.hotkey_click_through))
        self._click_key.keySequenceChanged.connect(lambda seq: self._set_hotkey("hotkey_click_through", seq))
        shortcuts.addWidget(QLabel("Show / hide overlay"), 0, 0)
        shortcuts.addWidget(self._visibility_key, 0, 1)
        shortcuts.addWidget(QLabel("Move mode on / off"), 1, 0)
        shortcuts.addWidget(self._click_key, 1, 1)
        shortcuts.setColumnStretch(1, 1)
        layout.addLayout(shortcuts)
        layout.addWidget(muted_label("Move mode lets you drag the overlay. Click-through mode locks it in place so clicks go to your game."))
        return card

    def _build_obs_card(self, obs: ObsOverlayServer) -> QFrame:
        card, layout = make_card("OBS Studio")
        layout.addWidget(muted_label(
            "Recommended: in OBS, add a Browser Source and paste this address. "
            "It shows your live BPM on a transparent background and works offline. "
            "Suggested size: 400 x 160."
        ))
        row = QHBoxLayout()
        url_field = QLineEdit(obs.url)
        url_field.setReadOnly(True)
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(obs.url))
        row.addWidget(url_field, 1)
        row.addWidget(copy_button)
        layout.addLayout(row)
        layout.addWidget(muted_label(
            "Alternative: add a Window Capture of the Heart Rate Overlay window. "
            "Window capture does not keep the transparent background, so the Browser Source is the cleaner option."
        ))
        if not obs.running:
            self._show_notice(f"The OBS overlay address could not start because port {obs.port} is already in use. Close the other program or change the port in settings.json.")
        return card

    def _on_reading(self, bpm: int | None) -> None:
        self._bpm_value.setText("--" if bpm is None else str(bpm))

    def _on_status(self, status: str) -> None:
        self._status_pill.setText(status)
        self._status_pill.setProperty("state", status.lower())
        self._status_pill.style().unpolish(self._status_pill)
        self._status_pill.style().polish(self._status_pill)
        if status == "Disconnected":
            self._bpm_value.setText("--")

    def _on_bluetooth_error(self, message: str) -> None:
        self._bluetooth_message.setText(message)
        self._bluetooth_message.setVisible(bool(message))

    def _on_overlay_visibility(self, visible: bool) -> None:
        self._toggle_button.setText("Hide overlay" if visible else "Show overlay")

    def _refresh_sensor_label(self) -> None:
        if self._s.sensor_address:
            self._sensor_label.setText(f"Remembered sensor: {self._s.sensor_name or self._s.sensor_address}")
        else:
            self._sensor_label.setText("No sensor selected yet.")
        self._forget_button.setVisible(bool(self._s.sensor_address))

    def _open_device_dialog(self) -> None:
        dialog = DeviceDialog(self._monitor, self)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.selection is None:
            return
        address, name = dialog.selection
        self._s.sensor_address = address
        self._s.sensor_name = name
        save_settings(self._s)
        self._monitor.connect_sensor(address, name)
        self._refresh_sensor_label()

    def _forget_sensor(self) -> None:
        self._s.sensor_address = None
        self._s.sensor_name = None
        save_settings(self._s)
        self._monitor.forget_sensor()
        self._refresh_sensor_label()

    def _place_overlay(self, corner: str) -> None:
        screens = QGuiApplication.screens()
        index = self._monitor_combo.currentIndex()
        if 0 <= index < len(screens):
            self._overlay.place_on_screen(screens[index], corner)

    def _refresh_monitors(self, *_args) -> None:
        screens = QGuiApplication.screens()
        self._monitor_combo.clear()
        for index, screen in enumerate(screens):
            geometry = screen.geometry()
            self._monitor_combo.addItem(f"Monitor {index + 1} ({geometry.width()} x {geometry.height()})")
        current = self._overlay.screen()
        if current in screens:
            self._monitor_combo.setCurrentIndex(screens.index(current))

    def _set_hotkey(self, field: str, sequence: QKeySequence) -> None:
        setattr(self._s, field, sequence.toString(QKeySequence.SequenceFormat.PortableText))
        self._register_hotkeys()

    def _register_hotkeys(self) -> None:
        visibility_ok = self._hotkeys.register("visibility", self._s.hotkey_visibility)
        click_ok = self._hotkeys.register("click_through", self._s.hotkey_click_through)
        save_settings(self._s)
        if visibility_ok and click_ok:
            self._notice.hide()
        else:
            self._show_notice(HOTKEY_FAILED_NOTICE)

    def _on_hotkey(self, name: str) -> None:
        if name == "visibility":
            self._overlay.toggle_visibility()
        elif name == "click_through":
            self._s.overlay_click_through = not self._s.overlay_click_through
            self._appearance.refresh()
            self._on_appearance_changed()

    def _on_appearance_changed(self) -> None:
        save_settings(self._s)
        self._overlay.apply_settings()

    def _show_notice(self, text: str) -> None:
        self._notice.setText(text)
        self._notice.show()
