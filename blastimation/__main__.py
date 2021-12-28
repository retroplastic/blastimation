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

    luts = {
        128: {},
        256: {}
    }

    blasts = {
        1: {},
        2: {},
        3: {},
        4: {},
        5: {},
        6: {}
    }

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
                    if size == 128 or size == 256:
                        luts[size][address] = encoded_bytes
                case (Blast.BLAST1_RGBA16 | Blast.BLAST2_RGBA32 | Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
                    blasts[blast_type.value][address] = decode_blast(blast_type, encoded_bytes)
                case _:
                    blasts[blast_type.value][address] = encoded_bytes

    print("LUTs:")
    for lut_size, lut_dict in luts.items():
        print(f"  {lut_size} ({len(lut_dict)}):")
        for addr in lut_dict.keys():
            print("    ", addr)

    print("Blasts:")
    for blast_id, blast_dict in blasts.items():
        print(f"  {Blast(blast_id)} ({len(blast_dict)})")


main()
