import unittest

from PySide6.QtWidgets import QApplication

from blastimation.blast import Blast
from blastimation.rom import Rom


class TestRom(unittest.TestCase):
    def test_decode(self):
        QApplication()
        rom = Rom("baserom.us.v11.z64")
        for blast_id, images_dict in rom.images.items():
            blast_type = Blast(blast_id)
            for address, image in images_dict.items():
                match blast_type:
                    case Blast.BLAST4_IA16:
                        image.decode_lut(rom.luts[128]["047480"])
                    case Blast.BLAST5_RGBA32:
                        image.decode_lut(rom.luts[256]["152970"])
                    case _:
                        image.decode()
