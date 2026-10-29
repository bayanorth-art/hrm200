import ctypes
from ctypes import wintypes
from collections.abc import Callable

from PySide6.QtCore import QAbstractNativeEventFilter

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

HOTKEY_IDS = {"visibility": 1, "click_through": 2}


def parse_hotkey(text: str) -> tuple[int, int] | None:
    modifiers = 0
    key = None
    for part in (piece.strip().lower() for piece in text.split("+")):
        if part in ("ctrl", "control"):
            modifiers |= MOD_CONTROL
        elif part == "alt":
            modifiers |= MOD_ALT
        elif part == "shift":
            modifiers |= MOD_SHIFT
        elif part in ("meta", "win"):
            modifiers |= MOD_WIN
        elif part:
            key = part
    if modifiers == 0 or key is None:
        return None
    virtual_key = _virtual_key(key)
    if virtual_key is None:
        return None
    return modifiers, virtual_key


def _virtual_key(key: str) -> int | None:
    if len(key) == 1 and (key.isalpha() or key.isdigit()):
        return ord(key.upper())
    if key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        return 0x70 + int(key[1:]) - 1
    return None


class HotkeyManager(QAbstractNativeEventFilter):
    def __init__(self, on_triggered: Callable[[str], None]) -> None:
        super().__init__()
        self._on_triggered = on_triggered
        self._names_by_id: dict[int, str] = {}

    def register(self, name: str, text: str) -> bool:
        hotkey_id = HOTKEY_IDS[name]
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey(None, hotkey_id)
        self._names_by_id.pop(hotkey_id, None)
        parsed = parse_hotkey(text)
        if parsed is None:
            return False
        modifiers, virtual_key = parsed
        if not user32.RegisterHotKey(None, hotkey_id, modifiers | MOD_NOREPEAT, virtual_key):
            return False
        self._names_by_id[hotkey_id] = name
        return True

    def unregister_all(self) -> None:
        for hotkey_id in HOTKEY_IDS.values():
            ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)
        self._names_by_id.clear()

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam in self._names_by_id:
                self._on_triggered(self._names_by_id[msg.wParam])
        return False, 0
