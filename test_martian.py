#!/usr/bin/env python3
import unittest
from martian import (
    hex_to_rgb,
    LED_COUNT,
    PAYLOAD_LEN,
    COLORS_START,
    BUILTIN_MODES,
)


class TestHexToRgb(unittest.TestCase):

    def test_red(self):
        self.assertEqual(hex_to_rgb("FF0000"), (255, 0, 0))

    def test_green(self):
        self.assertEqual(hex_to_rgb("00FF00"), (0, 255, 0))

    def test_blue(self):
        self.assertEqual(hex_to_rgb("0000FF"), (0, 0, 255))

    def test_white(self):
        self.assertEqual(hex_to_rgb("FFFFFF"), (255, 255, 255))

    def test_black(self):
        self.assertEqual(hex_to_rgb("000000"), (0, 0, 0))

    def test_orange(self):
        self.assertEqual(hex_to_rgb("FF8800"), (255, 136, 0))

    def test_magenta(self):
        self.assertEqual(hex_to_rgb("FF00FF"), (255, 0, 255))

    def test_cyan(self):
        self.assertEqual(hex_to_rgb("00FFFF"), (0, 255, 255))

    def test_lowercase(self):
        self.assertEqual(hex_to_rgb("ff0000"), (255, 0, 0))

    def test_mixed_case(self):
        self.assertEqual(hex_to_rgb("FfAa00"), (255, 170, 0))

    def test_with_hash(self):
        self.assertEqual(hex_to_rgb("#FF0000"), (255, 0, 0))

    def test_invalid_short(self):
        with self.assertRaises(ValueError):
            hex_to_rgb("FFF")

    def test_invalid_long(self):
        with self.assertRaises(ValueError):
            hex_to_rgb("FFFFFFFF")

    def test_invalid_chars(self):
        with self.assertRaises(ValueError):
            hex_to_rgb("ZZZZZZ")

    def test_empty(self):
        with self.assertRaises(ValueError):
            hex_to_rgb("")

    def test_only_hash(self):
        with self.assertRaises(ValueError):
            hex_to_rgb("#")


class TestConstants(unittest.TestCase):

    def test_builtin_modes_count(self):
        """14 modos hardware + off."""
        self.assertEqual(len(BUILTIN_MODES), 14)

    def test_builtin_modes_have_all_ids(self):
        for name, mode_id in BUILTIN_MODES.items():
            self.assertGreaterEqual(mode_id, 1)
            self.assertLessEqual(mode_id, 14)

    def test_builtin_modes_no_duplicates(self):
        ids = list(BUILTIN_MODES.values())
        self.assertEqual(len(ids), len(set(ids)))

    def test_payload_led_fit(self):
        """Los datos BGR (3 planos × 132 LED) caben en el payload."""
        needed = COLORS_START + LED_COUNT * 3
        self.assertLessEqual(needed, PAYLOAD_LEN)

    def test_led_count_positive(self):
        self.assertGreater(LED_COUNT, 0)

    def test_payload_large_enough(self):
        """1032 bytes > cualquier configuración razonable."""
        self.assertGreaterEqual(PAYLOAD_LEN, 256)

    def test_colors_start_aligned(self):
        """COLORS_START debe ser >= 8 para cabecera."""
        self.assertGreaterEqual(COLORS_START, 8)

    def test_all_mode_names_lowercase(self):
        for name in BUILTIN_MODES:
            self.assertEqual(name, name.lower())


if __name__ == "__main__":
    unittest.main()
