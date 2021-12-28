#!/usr/bin/env python3
import struct
import sys
from pathlib import Path

from blast import Blast, decode_blast, decode_blast_lookup
from tex64 import N64SegRgba16, N64SegRgba32, N64SegIa8, N64SegIa16


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


ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


class Blastimation:
    def __init__(self):
        self.luts = {
            128: {},
            256: {}
        }

        self.blasts = {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {}
        }

    def read_rom(self, rom_bytes):
        for i in range(ROM_OFFSET, END_OFFSET, 8):
            start = struct.unpack(">I", rom_bytes[i:i + 4])[0]
            size = struct.unpack(">H", rom_bytes[i + 4:i + 6])[0]
            blast_type = Blast(struct.unpack(">H", rom_bytes[i + 6:i + 8])[0])
            assert len(rom_bytes) >= start

            if size > 0:
                address = "%06X" % (start + ROM_OFFSET)
                # to_address = "%06X" % (start + size + ROM_OFFSET)
                # print(address, to_address, blast_type, size)

                encoded_bytes = rom_bytes[start + ROM_OFFSET: start + ROM_OFFSET + size]

                assert len(encoded_bytes) == size

                match blast_type:
                    case Blast.BLAST0:
                        if size == 128 or size == 256:
                            self.luts[size][address] = encoded_bytes
                    case (Blast.BLAST1_RGBA16 | Blast.BLAST2_RGBA32 | Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
                        self.blasts[blast_type.value][address] = decode_blast(blast_type, encoded_bytes)
                    case _:
                        self.blasts[blast_type.value][address] = encoded_bytes

    def print_stats(self):
        print("LUTs:")
        for lut_size, lut_dict in self.luts.items():
            print(f"  {lut_size} ({len(lut_dict)}):")
            for addr in lut_dict.keys():
                print("    ", addr)

        print("Blasts:")
        for blast_id, blast_dict in self.blasts.items():
            print(f"  {Blast(blast_id)} ({len(blast_dict)})")

    @staticmethod
    def save_png_base(name: str, blast_type: Blast, decoded_bytes: bytes, width: int, height: int):
        writer_class = blast_get_png_writer(blast_type)

        png_dir_path = Path("test")
        png_dir_path.mkdir(exist_ok=True, parents=True)

        png_writer = writer_class.get_writer(width, height)
        png_file_path = png_dir_path / f"{name}.png"

        print(f"Writing {png_file_path}...")

        with open(png_file_path, "wb") as f:
            png_writer.write_array(f, writer_class.parse_image(decoded_bytes, width, height, False, True))

    def save_png(self, address: str, blast_id: int, width: int, height: int):
        blast_type = Blast(blast_id)
        decoded_bytes = self.blasts[blast_id][address]

        self.save_png_base(address, blast_type, decoded_bytes, width, height)

    def save_png_lut(self, address: str, blast_id: int, width: int, height: int, lut_addr: str):
        blast_type = Blast(blast_id)
        encoded_bytes = self.blasts[blast_id][address]

        match blast_type:
            case Blast.BLAST4_IA16:
                lut = self.luts[128][lut_addr]
            case Blast.BLAST5_RGBA32:
                lut = self.luts[256][lut_addr]
            case _:
                return

        decoded_bytes = decode_blast_lookup(blast_type, encoded_bytes, lut)
        self.save_png_base(address, blast_type, decoded_bytes, width, height)


def print_usage():
    print("Usage:")
    print(f"{sys.argv[0]} <rom>")


def main():
    if len(sys.argv) != 2:
        print_usage()
        return

    print(f"Opening {sys.argv[1]}...")

    with open(sys.argv[1], "rb") as f:
        rom_bytes = f.read()

    app = Blastimation()
    app.read_rom(rom_bytes)
    app.print_stats()

    # Test
    app.save_png("00DB08", 1, 32, 32)
    app.save_png("26A1C0", 1, 40, 40)
    app.save_png("27DB30", 2, 32, 32)
    app.save_png("08EBE8", 3, 64, 64)
    app.save_png_lut("1F0BD8", 4, 64, 32, "047480")
    app.save_png_lut("1DC880", 5, 32, 32, "152970")
    app.save_png("33D7D8", 6, 16, 32)


main()
