HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

_CONTACT_NOT_DETECTED = 0b10
_MAX_PLAUSIBLE_BPM = 300


def parse_hr_measurement(data: bytes) -> int | None:
    if len(data) < 2:
        return None
    flags = data[0]
    if ((flags >> 1) & 0b11) == _CONTACT_NOT_DETECTED:
        return None
    if flags & 0x01:
        if len(data) < 3:
            return None
        bpm = int.from_bytes(data[1:3], "little")
    else:
        bpm = data[1]
    return bpm if 0 < bpm < _MAX_PLAUSIBLE_BPM else None
