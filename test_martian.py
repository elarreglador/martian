#!/usr/bin/env python3
import unittest
from martian import (
    hex_to_rgb,
    LED_COUNT,
    PAYLOAD_LEN,
    COLORS_START,
    BUILTIN_MODES,
)
from slots import (
    HID_TO_SLOT,
    HID_TO_SLOT_AMBIGUOUS,
    MODIFIER_SLOTS,
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


class TestHidToSlot(unittest.TestCase):

    def test_esc_slot_0(self):
        self.assertEqual(HID_TO_SLOT[0x29], 0)

    def test_f1_slot_2(self):
        self.assertEqual(HID_TO_SLOT[0x3A], 2)

    def test_f12_slot_14(self):
        self.assertEqual(HID_TO_SLOT[0x45], 14)

    def test_a_slot_67(self):
        self.assertEqual(HID_TO_SLOT[0x04], 67)

    def test_s_slot_68(self):
        self.assertEqual(HID_TO_SLOT[0x16], 68)

    def test_d_slot_69(self):
        self.assertEqual(HID_TO_SLOT[0x07], 69)

    def test_w_slot_46(self):
        self.assertEqual(HID_TO_SLOT[0x1A], 46)

    def test_space_slot_115(self):
        self.assertEqual(HID_TO_SLOT[0x2C], 115)

    def test_enter_main_slot_79(self):
        self.assertEqual(HID_TO_SLOT[0x28], 79)

    def test_lshift_slot_88(self):
        self.assertEqual(HID_TO_SLOT[0xE1], 88)

    def test_no_duplicates_in_main(self):
        """Ningún slot se repite en HID_TO_SLOT (los duplicados van en AMBIGUOUS)."""
        slots = list(HID_TO_SLOT.values())
        self.assertEqual(len(slots), len(set(slots)))

    def test_no_duplicate_ambiguous_with_main(self):
        """Los slots ambiguos no están en HID_TO_SLOT."""
        for slots in HID_TO_SLOT_AMBIGUOUS.values():
            for s in slots:
                self.assertNotIn(s, HID_TO_SLOT.values())

    def test_all_slots_in_range(self):
        """Todos los slots están en 0..LED_COUNT-1."""
        for slot in HID_TO_SLOT.values():
            self.assertGreaterEqual(slot, 0)
            self.assertLess(slot, LED_COUNT)

    def test_all_modifier_slots_valid(self):
        """Todos los modifier slots están en rango."""
        for slot in MODIFIER_SLOTS.values():
            self.assertGreaterEqual(slot, 0)
            self.assertLess(slot, LED_COUNT)

    def test_modifier_slots_no_duplicates(self):
        slots = list(MODIFIER_SLOTS.values())
        self.assertEqual(len(slots), len(set(slots)))

    def test_enter_slot_79_not_in_ambiguous(self):
        """Enter principal (0x28) no debe estar en ambiguos."""
        self.assertNotIn(0x28, HID_TO_SLOT_AMBIGUOUS)

    def test_numpad_enter_ambiguous(self):
        """Numpad Enter (0x58) tiene dos slots."""
        self.assertIn(0x58, HID_TO_SLOT_AMBIGUOUS)
        self.assertEqual(len(HID_TO_SLOT_AMBIGUOUS[0x58]), 2)

    def test_numpad_plus_ambiguous(self):
        """Numpad + (0x57) tiene dos slots."""
        self.assertIn(0x57, HID_TO_SLOT_AMBIGUOUS)
        self.assertEqual(len(HID_TO_SLOT_AMBIGUOUS[0x57]), 2)


if __name__ == "__main__":
    unittest.main()
