#!/usr/bin/env python3
import struct
import sys


def print_usage():
    print("Usage:")
    print(f"{sys.argv[0]} <rom>")


ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


def main():
    if len(sys.argv) != 2:
        print_usage()
        return

    print(f"Opening {sys.argv[1]}...")

    with open(sys.argv[1], "rb") as f:
        rom_bytes = f.read()

    rom_size = len(rom_bytes)

    for i in range(ROM_OFFSET, END_OFFSET, 8):
        start = struct.unpack(">I", rom_bytes[i:i+4])[0]
        size = struct.unpack(">H", rom_bytes[i+4:i+6])[0]
        blast_type = struct.unpack(">H", rom_bytes[i+6:i+8])[0]
        assert rom_size >= start

        if size > 0:
            print("%06X" % (start + ROM_OFFSET), f"blast{blast_type}", size)

main()
