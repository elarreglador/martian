#!/usr/bin/env python3
"""Scan slots: Build HID_TO_SLOT mapping on MK-Revo Pro from scratch.

Usage: sudo python3 scan_slots.py

Lights up each slot with a colored circle, asks what key it
illuminates, and generates the correct slot map at the end.
"""

from martian.tools.scanner import run

if __name__ == "__main__":
    run()
