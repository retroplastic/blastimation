#!/usr/bin/env python3
import struct
import sys

from blast import Blast, decode_blast


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

    luts128 = {}
    luts256 = {}

    for i in range(ROM_OFFSET, END_OFFSET, 8):
        start = struct.unpack(">I", rom_bytes[i:i+4])[0]
        size = struct.unpack(">H", rom_bytes[i+4:i+6])[0]
        blast_type = Blast(struct.unpack(">H", rom_bytes[i+6:i+8])[0])
        assert rom_size >= start

        if size > 0:
            address = "%06X" % (start + ROM_OFFSET)
            to_address = "%06X" % (start + size + ROM_OFFSET)
            print(address, to_address, blast_type, size)

            encoded_bytes = rom_bytes[start + ROM_OFFSET: start + ROM_OFFSET + size]

            assert len(encoded_bytes) == size

            match blast_type:
                case Blast.BLAST0:
                    if size == 128:
                        luts128[address] = encoded_bytes
                    elif size == 256:
                        luts256[address] = encoded_bytes
                case (Blast.BLAST1_RGBA16 | Blast.BLAST2_RGBA32 | Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
                    decoded_bytes = decode_blast(blast_type, encoded_bytes)


main()
