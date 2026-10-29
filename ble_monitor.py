import asyncio
import concurrent.futures
import contextlib
import logging
import threading
import time

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError
from PySide6.QtCore import QObject, Signal

from hr_overlay.hr_parser import HR_MEASUREMENT_UUID, HR_SERVICE_UUID, parse_hr_measurement

SCAN_SECONDS = 6.0
SEARCH_TIMEOUT_S = 10.0
CONNECT_TIMEOUT_S = 15.0
STALE_AFTER_S = 5.0
WATCHDOG_TICK_S = 0.5
IDLE_POLL_S = 0.5
RETRY_MIN_S = 2.0
RETRY_MAX_S = 15.0
BLUETOOTH_HINT = "Bluetooth connection problem. Make sure Bluetooth is on and the strap is worn and awake. Retrying..."

log = logging.getLogger(__name__)


def _looks_like_heart_sensor(name: str, service_uuids: list[str]) -> bool:
    if HR_SERVICE_UUID in service_uuids:
        return True
    lowered = name.lower()
    return "hrm" in lowered or "garmin" in lowered


class HeartRateMonitor(QObject):
    reading_changed = Signal(object)
    status_changed = Signal(str)
    devices_found = Signal(list)
    error_occurred = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="ble-monitor", daemon=True)
        self._lock = threading.Lock()
        self._target: tuple[str, str] | None = None
        self._status = "Disconnected"
        self._bpm: int | None = None
        self._beats = 0
        self._last_beat_at = 0.0
        self._supervisor: concurrent.futures.Future | None = None

    def start(self) -> None:
        self._thread.start()
        self._supervisor = asyncio.run_coroutine_threadsafe(self._supervise(), self._loop)

    def stop(self) -> None:
        if self._supervisor is not None:
            self._supervisor.cancel()
            concurrent.futures.wait([self._supervisor], timeout=5)
        self._loop.call_soon_threadsafe(self._loop.stop)

    def connect_sensor(self, address: str, name: str) -> None:
        self._loop.call_soon_threadsafe(self._set_target, (address, name))

    def forget_sensor(self) -> None:
        self._loop.call_soon_threadsafe(self._set_target, None)

    def scan(self) -> None:
        asyncio.run_coroutine_threadsafe(self._scan(), self._loop)

    def snapshot(self) -> dict:
        with self._lock:
            return {"bpm": self._bpm, "status": self._status, "beats": self._beats}

    def _set_target(self, target: tuple[str, str] | None) -> None:
        self._target = target

    async def _scan(self) -> None:
        try:
            found = await BleakScanner.discover(timeout=SCAN_SECONDS, return_adv=True)
        except Exception:
            log.exception("Bluetooth scan failed")
            self.error_occurred.emit(BLUETOOTH_HINT)
            self.devices_found.emit([])
            return
        devices = []
        for device, advertisement in found.values():
            name = advertisement.local_name or device.name or "Unnamed device"
            service_uuids = [uuid.lower() for uuid in advertisement.service_uuids]
            if _looks_like_heart_sensor(name, service_uuids):
                devices.append((name, device.address))
        devices.sort(key=lambda item: item[0].lower())
        self.devices_found.emit(devices)

    async def _supervise(self) -> None:
        delay = RETRY_MIN_S
        while True:
            target = self._target
            if target is None:
                self._set_status("Disconnected")
                await asyncio.sleep(IDLE_POLL_S)
                continue
            connected = False
            try:
                connected = await self._session(target)
            except BleakError:
                log.warning("Bluetooth error while using sensor", exc_info=True)
                self.error_occurred.emit(BLUETOOTH_HINT)
            except Exception:
                log.exception("Unexpected Bluetooth error")
                self.error_occurred.emit(BLUETOOTH_HINT)
            self._publish(None)
            self._set_status("Disconnected")
            if self._target != target:
                delay = RETRY_MIN_S
                continue
            if connected:
                delay = RETRY_MIN_S
            await asyncio.sleep(delay)
            delay = min(delay * 2, RETRY_MAX_S)

    async def _session(self, target: tuple[str, str]) -> bool:
        address, _name = target
        self._set_status("Searching")
        device = await BleakScanner.find_device_by_address(address, timeout=SEARCH_TIMEOUT_S)
        if device is None or self._target != target:
            return False

        self._set_status("Connecting")
        lost = asyncio.Event()
        async with BleakClient(device, disconnected_callback=lambda _client: lost.set(), timeout=CONNECT_TIMEOUT_S) as client:
            await client.start_notify(HR_MEASUREMENT_UUID, self._on_measurement)
            self._last_beat_at = time.monotonic()
            self._set_status("Connected")
            self.error_occurred.emit("")
            while not lost.is_set() and self._target == target:
                await asyncio.sleep(WATCHDOG_TICK_S)
                if self._bpm is not None and time.monotonic() - self._last_beat_at > STALE_AFTER_S:
                    self._publish(None)
            if client.is_connected:
                with contextlib.suppress(BleakError):
                    await client.stop_notify(HR_MEASUREMENT_UUID)
        return True

    def _on_measurement(self, _sender, data: bytearray) -> None:
        bpm = parse_hr_measurement(bytes(data))
        if bpm is None:
            return
        self._last_beat_at = time.monotonic()
        self._publish(bpm)

    def _publish(self, bpm: int | None) -> None:
        with self._lock:
            if bpm is None and self._bpm is None:
                return
            self._bpm = bpm
            if bpm is not None:
                self._beats += 1
        self.reading_changed.emit(bpm)

    def _set_status(self, status: str) -> None:
        with self._lock:
            if status == self._status:
                return
            self._status = status
        self.status_changed.emit(status)
