#!/usr/bin/env python3
import struct
import sys

from blast import Blast, decode_blast
from splat_img.rgba16 import N64SegRgba16
from splat_img.rgba32 import N64SegRgba32
from splat_img.ia8 import N64SegIa8
from splat_img.ia16 import N64SegIa16


def print_usage():
    print("Usage:")
    print(f"{sys.argv[0]} <rom>")


ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


def blast_get_png_writer(blast_type: Blast):
    match blast_type:
        case Blast.BLAST1_RGBA16:
            return N64SegRgba16
        case (Blast.BLAST2_RGBA32 | Blast.BLAST5_RGBA32):
            return N64SegRgba32
        case (Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
            return N64SegIa8
        case Blast.BLAST4_IA16:
            return N64SegIa16
        case _:
            return None


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

    blast_type = Blast(3)

    decoded_bytes = blasts[3]["08EBE8"]
    writer_class = blast_get_png_writer(blast_type)

    width = 64
    height = 64

    png_writer = writer_class.get_writer(width, height)
    png_file_path = f"{address}.png"

    print(f"Writing {png_file_path}...")

    with open(png_file_path, "wb") as f:
        match blast_type:
            case Blast.BLAST4_IA16:
                png_writer.write_array(f, decoded_bytes)
            case _:
                png_writer.write_array(f, writer_class.parse_image(decoded_bytes, width, height, False, True))


main()
