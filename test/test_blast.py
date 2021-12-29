import unittest
from pathlib import Path

import png

from blastimation.blast import Blast, decode_blast_lookup, blast_get_png_writer, blast_is_grayscale
from blastimation.rom import Rom


def save_png_base(name: str, blast_type: Blast, decoded_bytes: bytes, width: int, height: int):
    writer_class = blast_get_png_writer(blast_type)

    png_dir_path = Path("pngs")
    png_dir_path.mkdir(exist_ok=True, parents=True)

    is_gray = blast_is_grayscale(blast_type)
    png_writer = png.Writer(width, height, greyscale=is_gray, alpha=True)
    png_file_path = png_dir_path / f"{name}.png"

    print(f"Writing {png_file_path}...")

    with open(png_file_path, "wb") as f:
        png_writer.write_array(f, writer_class.parse_image(decoded_bytes, width, height, False, True))


def save_png(rom: Rom, address: str, blast_id: int, width: int, height: int):
    blast_type = Blast(blast_id)
    decoded_bytes = rom.blasts[blast_id][address]

    save_png_base(address, blast_type, decoded_bytes, width, height)


def save_png_lut(rom: Rom, address: str, blast_id: int, width: int, height: int, lut_addr: str):
    blast_type = Blast(blast_id)
    encoded_bytes = rom.blasts[blast_id][address]

    match blast_type:
        case Blast.BLAST4_IA16:
            lut = rom.luts[128][lut_addr]
        case Blast.BLAST5_RGBA32:
            lut = rom.luts[256][lut_addr]
        case _:
            return

    decoded_bytes = decode_blast_lookup(blast_type, encoded_bytes, lut)
    save_png_base(address, blast_type, decoded_bytes, width, height)


class TestBlast(unittest.TestCase):
    def test_exporting_pngs(self):
        rom = Rom("baserom.us.v11.z64")
        save_png(rom, "00DB08", 1, 32, 32)
        save_png(rom, "26A1C0", 1, 40, 40)
        save_png(rom, "27DB30", 2, 32, 32)
        save_png(rom, "08EBE8", 3, 64, 64)
        save_png_lut(rom, "1F0BD8", 4, 64, 32, "047480")
        save_png_lut(rom, "1DC880", 5, 32, 32, "152970")
        save_png(rom, "33D7D8", 6, 16, 32)
