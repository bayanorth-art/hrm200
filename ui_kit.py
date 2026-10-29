from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

APP_STYLESHEET = """
QWidget { font-family: "Segoe UI"; font-size: 10pt; color: #1F2933; }
QWidget#root { background: #F3F5F8; }
QFrame#card { background: #FFFFFF; border: 1px solid #E4E7EB; border-radius: 12px; }
QLabel#sectionTitle { font-size: 11pt; font-weight: 600; }
QLabel#muted { color: #52606D; }
QLabel#bpmValue { font-size: 44pt; font-weight: 700; color: #E53935; }
QLabel#notice, QLabel#warning { color: #78350F; background: #FEF3C7; border-radius: 8px; padding: 10px 12px; }
QLabel#statusPill { border-radius: 11px; padding: 4px 12px; font-weight: 600; background: #E4E7EB; color: #323F4B; }
QLabel#statusPill[state="connected"] { background: #DCFCE7; color: #14532D; }
QLabel#statusPill[state="connecting"], QLabel#statusPill[state="searching"] { background: #FEF3C7; color: #78350F; }
QLabel#statusPill[state="disconnected"] { background: #FEE2E2; color: #7F1D1D; }
QPushButton { background: #FFFFFF; border: 1px solid #CBD2D9; border-radius: 8px; padding: 8px 14px; }
QPushButton:hover { background: #F0F4F8; }
QPushButton:pressed { background: #E4E7EB; }
QPushButton:disabled { color: #9AA5B1; background: #F5F7FA; }
QPushButton#primary { background: #2563EB; border: 1px solid #2563EB; color: #FFFFFF; font-weight: 600; }
QPushButton#primary:hover { background: #1D4ED8; }
QPushButton#primary:pressed { background: #1E40AF; }
QPushButton#primary:disabled { background: #93B4F5; border: 1px solid #93B4F5; color: #FFFFFF; }
QComboBox, QKeySequenceEdit, QLineEdit { background: #FFFFFF; border: 1px solid #CBD2D9; border-radius: 8px; padding: 6px 10px; min-height: 20px; }
QListWidget { background: #FFFFFF; border: 1px solid #CBD2D9; border-radius: 8px; padding: 4px; }
QListWidget::item { padding: 8px; border-radius: 6px; }
QListWidget::item:selected { background: #DBEAFE; color: #1E3A8A; }
QSlider::groove:horizontal { height: 4px; background: #D9E2EC; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #2563EB; border-radius: 2px; }
QSlider::handle:horizontal { background: #2563EB; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
QCheckBox { spacing: 8px; }
"""


def make_card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)
    heading = QLabel(title)
    heading.setObjectName("sectionTitle")
    layout.addWidget(heading)
    return frame, layout


def muted_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("muted")
    label.setWordWrap(True)
    return label
