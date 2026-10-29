import math

from PySide6.QtCore import QEasingCurve, QPoint, QRectF, Qt, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from hr_overlay.heart_icon import draw_heart
from hr_overlay.settings import Settings, save_settings

FONT_FAMILY = "Segoe UI"
EDGE_MARGIN = 24
PULSE_GROWTH = 0.22
BASE_PADDING_X = 14
BASE_PADDING_Y = 8
CORNERS = ("top_left", "top_right", "bottom_left", "bottom_right")


class OverlayWindow(QWidget):
    visibility_changed = Signal(bool)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._s = settings
        self._shown_value: float | None = None
        self._pulse = 0.0
        self._drag_offset: QPoint | None = None
        self._big_font = QFont(FONT_FAMILY)
        self._small_font = QFont(FONT_FAMILY)
        self._heart_size = 0.0
        self._gap = 0.0
        self._pad_x = 0
        self._pad_y = 0
        self._digits_width = 0

        self.setWindowTitle("Heart Rate Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._count_anim = QVariantAnimation(self)
        self._count_anim.setDuration(350)
        self._count_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._count_anim.valueChanged.connect(self._on_count_tick)

        self._pulse_anim = QVariantAnimation(self)
        self._pulse_anim.setDuration(420)
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pulse_anim.valueChanged.connect(self._on_pulse_tick)

        self._set_window_flags()
        self.apply_settings()

    def apply_settings(self) -> None:
        click_through_active = bool(self.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        if click_through_active != self._s.overlay_click_through:
            self._set_window_flags()
        self.setWindowOpacity(self._s.overlay_opacity)
        self._relayout()
        self.update()

    def set_bpm(self, bpm: int | None) -> None:
        self._count_anim.stop()
        if bpm is None:
            self._shown_value = None
            self.update()
            return
        start = self._shown_value if self._shown_value is not None else float(bpm)
        self._count_anim.setStartValue(start)
        self._count_anim.setEndValue(float(bpm))
        self._count_anim.start()
        if self._s.overlay_heartbeat:
            self._pulse_anim.stop()
            self._pulse_anim.start()

    def toggle_visibility(self) -> None:
        self.setVisible(not self.isVisible())
        self._s.overlay_visible = self.isVisible()
        save_settings(self._s)
        self.visibility_changed.emit(self.isVisible())

    def restore(self) -> None:
        self._place_saved_or_default()
        if self._s.overlay_visible:
            self.show()
        self.visibility_changed.emit(self.isVisible())

    def place_on_screen(self, screen, corner: str) -> None:
        area = screen.availableGeometry()
        x = area.left() + EDGE_MARGIN if corner.endswith("left") else area.right() - EDGE_MARGIN - self.width() + 1
        y = area.top() + EDGE_MARGIN if corner.startswith("top") else area.bottom() - EDGE_MARGIN - self.height() + 1
        self.move(x, y)
        self._remember_position()

    def _set_window_flags(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        if self._s.overlay_click_through:
            flags |= Qt.WindowType.WindowTransparentForInput
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()

    def _relayout(self) -> None:
        scale = self._s.overlay_scale
        size = self._s.overlay_font_size * scale
        self._big_font.setPixelSize(max(8, round(size)))
        self._big_font.setWeight(QFont.Weight.Bold)
        self._small_font.setPixelSize(max(7, round(size * 0.36)))
        self._small_font.setWeight(QFont.Weight.DemiBold)
        self._pad_x = round(BASE_PADDING_X * scale)
        self._pad_y = round(BASE_PADDING_Y * scale)
        self._heart_size = size * 0.8
        self._gap = size * 0.22
        self._digits_width = QFontMetrics(self._big_font).horizontalAdvance("888")
        label_width = QFontMetrics(self._small_font).horizontalAdvance("BPM")
        width = (
            self._pad_x * 2
            + self._heart_size
            + self._gap
            + self._digits_width
            + self._gap * 0.6
            + label_width
        )
        height = max(size * 1.2, self._heart_size) + self._pad_y * 2
        self.setFixedSize(math.ceil(width), math.ceil(height))

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        scale = self._s.overlay_scale
        radius = 14 * scale
        bounds = QRectF(self.rect())

        if self._s.overlay_background:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(12, 14, 18, 180))
            painter.drawRoundedRect(bounds, radius, radius)
        if not self._s.overlay_click_through:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 255, 255, 90), 1, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(bounds.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        pulse = 1 + PULSE_GROWTH * self._pulse if self._s.overlay_heartbeat else 1.0
        heart_x = self._pad_x + self._heart_size / 2
        draw_heart(painter, heart_x, self.height() / 2, self._heart_size * pulse, self._s.overlay_heart_color)

        align = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        number_x = self._pad_x + self._heart_size + self._gap
        number = "--" if self._shown_value is None else str(round(self._shown_value))
        text_color = QColor(self._s.overlay_text_color)
        painter.setFont(self._big_font)
        painter.setPen(text_color)
        painter.drawText(QRectF(number_x, 0, self._digits_width, self.height()), align, number)

        label_color = QColor(text_color)
        label_color.setAlpha(190)
        label_x = number_x + self._digits_width + self._gap * 0.6
        painter.setFont(self._small_font)
        painter.setPen(label_color)
        painter.drawText(QRectF(label_x, 0, self.width() - label_x, self.height()), align, "BPM")
        painter.end()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, _event) -> None:
        if self._drag_offset is not None:
            self._drag_offset = None
            self._remember_position()

    def _on_count_tick(self, value) -> None:
        self._shown_value = float(value)
        self.update()

    def _on_pulse_tick(self, value) -> None:
        self._pulse = float(value)
        self.update()

    def _place_saved_or_default(self) -> None:
        if self._s.overlay_x is not None and self._s.overlay_y is not None:
            point = QPoint(self._s.overlay_x, self._s.overlay_y)
            if any(screen.availableGeometry().contains(point) for screen in QGuiApplication.screens()):
                self.move(point)
                return
        self.place_on_screen(QGuiApplication.primaryScreen(), "top_right")

    def _remember_position(self) -> None:
        self._s.overlay_x = self.x()
        self._s.overlay_y = self.y()
        save_settings(self._s)
