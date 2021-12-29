import unittest

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QApplication
from tabulate import tabulate

from blastimation.blast import Blast, blast_parse_image
from blastimation.rom import Rom


def print_pixmap_details(data_pixmap: QPixmap, png_pixmap: QPixmap):
    table = [
        ("QPixmap", "Data", "PNG"),
        ("depth", data_pixmap.depth(), png_pixmap.depth()),
        ("hasAlpha", data_pixmap.hasAlpha(), png_pixmap.hasAlpha()),
        ("hasAlphaChannel", data_pixmap.hasAlphaChannel(), png_pixmap.hasAlphaChannel()),
    ]
    print(tabulate(table))


def print_image_details(data_image: QImage, png_image: QImage):
    table = [
        ("QImage", "Data", "PNG"),
        ("depth", data_image.depth(), png_image.depth()),
        ("allGray", data_image.allGray(), png_image.allGray()),
        ("format", data_image.format(), png_image.format()),
        ("isGrayscale", data_image.isGrayscale(), png_image.isGrayscale()),
        ("pixelFormat", data_image.pixelFormat(), png_image.pixelFormat()),
        ("size", data_image.size(), png_image.size()),
        ("sizeInBytes", data_image.sizeInBytes(), png_image.sizeInBytes()),
        ("hasAlphaChannel", data_image.hasAlphaChannel(), png_image.hasAlphaChannel()),
    ]
    print(tabulate(table))


class TestQImage(unittest.TestCase):
    def test_grayscale_import(self):
        QApplication()

        address = "08EBE8"

        # Load from ROM
        blast_id = 3
        width = 64
        height = 64

        rom = Rom("baserom.us.v11.z64")

        decoded_bytes = rom.blasts[blast_id][address]

        image_data = blast_parse_image(Blast(blast_id), decoded_bytes, width, height, False, True)

        bytes_per_pixel = 2
        image_format = QImage.Format_Grayscale8

        data_image = QImage(image_data, width, height, bytes_per_pixel * width, image_format)
        data_image.setAlphaChannel(data_image)
        data_pixmap = QPixmap.fromImage(data_image)

        # Load from PNG
        png_pixmap = QPixmap(f"pngs/{address}.png")
        png_image = QImage(f"pngs/{address}.png")

        print_pixmap_details(data_pixmap, png_pixmap)
        print_image_details(data_image, png_image)
