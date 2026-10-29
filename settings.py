import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "HeartRateOverlay"
SETTINGS_PATH = SETTINGS_DIR / "settings.json"


@dataclass
class Settings:
    sensor_address: str | None = None
    sensor_name: str | None = None
    overlay_visible: bool = False
    overlay_x: int | None = None
    overlay_y: int | None = None
    overlay_font_size: int = 40
    overlay_text_color: str = "#FFFFFF"
    overlay_heart_color: str = "#E53935"
    overlay_opacity: float = 0.95
    overlay_scale: float = 1.0
    overlay_background: bool = True
    overlay_heartbeat: bool = True
    overlay_click_through: bool = False
    hotkey_visibility: str = "Ctrl+Alt+H"
    hotkey_click_through: str = "Ctrl+Alt+L"
    obs_port: int = 8765


def load_settings() -> Settings:
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    known = {field.name for field in fields(Settings)}
    return Settings(**{key: value for key, value in raw.items() if key in known})


def save_settings(settings: Settings) -> None:
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = SETTINGS_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    temp_path.replace(SETTINGS_PATH)
