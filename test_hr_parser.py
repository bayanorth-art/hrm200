import unittest

from hr_overlay.hr_parser import parse_hr_measurement


class ParseHeartRateMeasurementTests(unittest.TestCase):
    def test_reads_8_bit_value(self) -> None:
        self.assertEqual(parse_hr_measurement(bytes([0x06, 84])), 84)

    def test_reads_16_bit_value(self) -> None:
        self.assertEqual(parse_hr_measurement(bytes([0x01, 0xC8, 0x00])), 200)

    def test_ignores_reading_when_skin_contact_is_lost(self) -> None:
        self.assertIsNone(parse_hr_measurement(bytes([0x04, 84])))

    def test_accepts_reading_when_contact_is_not_supported(self) -> None:
        self.assertEqual(parse_hr_measurement(bytes([0x00, 72])), 72)

    def test_rejects_short_or_zero_payloads(self) -> None:
        self.assertIsNone(parse_hr_measurement(b""))
        self.assertIsNone(parse_hr_measurement(bytes([0x00])))
        self.assertIsNone(parse_hr_measurement(bytes([0x00, 0])))
        self.assertIsNone(parse_hr_measurement(bytes([0x01, 0xC8])))


if __name__ == "__main__":
    unittest.main()
