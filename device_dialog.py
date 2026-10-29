from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from hr_overlay.ble_monitor import HeartRateMonitor
from hr_overlay.ui_kit import muted_label


class DeviceDialog(QDialog):
    def __init__(self, monitor: HeartRateMonitor, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._monitor = monitor
        self._devices: list[tuple[str, str]] = []
        self.selection: tuple[str, str] | None = None

        self.setWindowTitle("Connect heart rate sensor")
        self.setMinimumSize(440, 380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        layout.addWidget(muted_label("Wear the strap, make sure its contacts are wet, then pick your Garmin HRM 200 below."))
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._update_buttons)
        self._list.itemDoubleClicked.connect(lambda _item: self._accept_selection())
        layout.addWidget(self._list, 1)
        self._status = muted_label("")
        layout.addWidget(self._status)

        buttons = QHBoxLayout()
        self._scan_button = QPushButton("Scan again")
        self._scan_button.clicked.connect(self._start_scan)
        self._connect_button = QPushButton("Connect")
        self._connect_button.setObjectName("primary")
        self._connect_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._connect_button.clicked.connect(self._accept_selection)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self._scan_button)
        buttons.addStretch(1)
        buttons.addWidget(cancel_button)
        buttons.addWidget(self._connect_button)
        layout.addLayout(buttons)

        self._monitor.devices_found.connect(self._on_devices)
        self._update_buttons(-1)
        self._start_scan()

    def done(self, result: int) -> None:
        self._monitor.devices_found.disconnect(self._on_devices)
        super().done(result)

    def _start_scan(self) -> None:
        self._list.clear()
        self._devices = []
        self._scan_button.setEnabled(False)
        self._status.setText("Searching for heart rate sensors...")
        self._update_buttons(-1)
        self._monitor.scan()

    def _on_devices(self, devices: list) -> None:
        self._devices = list(devices)
        self._list.clear()
        for name, address in self._devices:
            self._list.addItem(QListWidgetItem(f"{name}    {address}"))
        self._scan_button.setEnabled(True)
        if self._devices:
            self._status.setText(f"Found {len(self._devices)} sensor(s). Select yours.")
        else:
            self._status.setText("No heart rate sensors found. Check that the strap is worn and Bluetooth is on, then scan again.")
        self._update_buttons(self._list.currentRow())

    def _update_buttons(self, row: int) -> None:
        self._connect_button.setEnabled(0 <= row < len(self._devices))

    def _accept_selection(self) -> None:
        row = self._list.currentRow()
        if not 0 <= row < len(self._devices):
            return
        self.selection = self._devices[row]
        self.accept()
