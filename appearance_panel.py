from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox, QColorDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from hr_overlay.settings import Settings
from hr_overlay.ui_kit import make_card, muted_label


class AppearancePanel(QWidget):
    changed = Signal()

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._s = settings
        self._checks: list[tuple[QCheckBox, str]] = []

        card, layout = make_card("Appearance")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        self._add_slider(grid, 0, "Font size", "overlay_font_size", 16, 96, 1, "px")
        self._add_slider(grid, 1, "Overlay scale", "overlay_scale", 50, 200, 100, "%")
        self._add_slider(grid, 2, "Opacity", "overlay_opacity", 30, 100, 100, "%")
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        self._add_color_row(layout, "Number color", "overlay_text_color")
        self._add_color_row(layout, "Heart color", "overlay_heart_color")

        self._add_check(layout, "Dark background behind the overlay", "overlay_background")
        self._add_check(layout, "Heartbeat pulse on each beat", "overlay_heartbeat")
        self._add_check(layout, "Click-through (mouse clicks pass through the overlay)", "overlay_click_through")
        layout.addWidget(muted_label("Turn on click-through so the overlay never gets in the way while you play. Turn it off to drag the overlay."))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

    def refresh(self) -> None:
        for box, field in self._checks:
            box.blockSignals(True)
            box.setChecked(getattr(self._s, field))
            box.blockSignals(False)

    def _add_slider(self, grid: QGridLayout, row: int, label: str, field: str, minimum: int, maximum: int, divisor: int, suffix: str) -> None:
        grid.addWidget(QLabel(label), row, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(round(getattr(self._s, field) * divisor))
        readout = QLabel(f"{slider.value()}{suffix}")
        readout.setObjectName("muted")
        readout.setMinimumWidth(56)
        readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        def on_change(value: int) -> None:
            setattr(self._s, field, value if divisor == 1 else value / divisor)
            readout.setText(f"{value}{suffix}")
            self.changed.emit()

        slider.valueChanged.connect(on_change)
        grid.addWidget(slider, row, 1)
        grid.addWidget(readout, row, 2)

    def _add_check(self, layout: QVBoxLayout, text: str, field: str) -> None:
        box = QCheckBox(text)
        box.setChecked(getattr(self._s, field))
        box.toggled.connect(lambda checked: self._set(field, checked))
        self._checks.append((box, field))
        layout.addWidget(box)

    def _set(self, field: str, value: bool) -> None:
        setattr(self._s, field, value)
        self.changed.emit()

    def _add_color_row(self, layout: QVBoxLayout, label: str, field: str) -> None:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addStretch(1)
        hex_label = QLabel(getattr(self._s, field))
        hex_label.setObjectName("muted")
        swatch = QPushButton()
        swatch.setFixedSize(56, 28)
        swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self._paint_swatch(swatch, getattr(self._s, field))
        swatch.clicked.connect(lambda: self._pick_color(field, swatch, hex_label))
        row.addWidget(hex_label)
        row.addWidget(swatch)
        layout.addLayout(row)

    def _pick_color(self, field: str, swatch: QPushButton, hex_label: QLabel) -> None:
        color = QColorDialog.getColor(QColor(getattr(self._s, field)), self, "Choose color")
        if not color.isValid():
            return
        value = color.name()
        setattr(self._s, field, value)
        hex_label.setText(value)
        self._paint_swatch(swatch, value)
        self.changed.emit()

    @staticmethod
    def _paint_swatch(swatch: QPushButton, color: str) -> None:
        swatch.setStyleSheet(f"background: {color}; border: 1px solid #CBD2D9; border-radius: 6px;")
