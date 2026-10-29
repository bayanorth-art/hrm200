from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap


def heart_path(center_x: float, center_y: float, size: float) -> QPainterPath:
    left = center_x - size / 2
    top = center_y - size / 2

    def point(u: float, v: float) -> tuple[float, float]:
        return left + u * size, top + v * size

    path = QPainterPath()
    path.moveTo(*point(0.5, 0.92))
    path.cubicTo(*point(0.15, 0.65), *point(0.0, 0.5), *point(0.0, 0.3))
    path.cubicTo(*point(0.0, 0.14), *point(0.12, 0.0), *point(0.28, 0.0))
    path.cubicTo(*point(0.40, 0.0), *point(0.47, 0.08), *point(0.5, 0.18))
    path.cubicTo(*point(0.53, 0.08), *point(0.60, 0.0), *point(0.72, 0.0))
    path.cubicTo(*point(0.88, 0.0), *point(1.0, 0.14), *point(1.0, 0.3))
    path.cubicTo(*point(1.0, 0.5), *point(0.85, 0.65), *point(0.5, 0.92))
    path.closeSubpath()
    return path


def draw_heart(painter: QPainter, center_x: float, center_y: float, size: float, color: str) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    painter.drawPath(heart_path(center_x, center_y, size))


def heart_pixmap(size: int, color: str) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_heart(painter, size / 2, size / 2, size * 0.9, color)
    painter.end()
    return pixmap
