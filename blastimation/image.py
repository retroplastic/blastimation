from PySide6.QtGui import QImage, QPixmap

from blastimation.blast import Blast, blast_guess_resolution, blast_parse_image, decode_blast, decode_blast_lookup


class BlastImage:
    def __init__(self, blast_type: Blast, address: str, encoded: bytes,
                 width: int = 0, height: int = 0):
        self.address = address
        self.width = width
        self.height = height

        self.blast = blast_type
        self.encoded = encoded
        self.decoded = None
        self.raw = None
        self.pixmap = None

    def decode(self):
        assert self.encoded
        assert self.blast not in [Blast.BLAST4_IA16, Blast.BLAST5_RGBA32]
        self.decoded = decode_blast(self.blast, self.encoded)

        self.guess_resolution()
        self.parse()
        self.generate_pixmap()

    def decode_lut(self, lut: bytes):
        assert self.encoded
        print(self.blast)
        assert self.blast in [Blast.BLAST4_IA16, Blast.BLAST5_RGBA32]
        self.decoded = decode_blast_lookup(self.blast, self.encoded, lut)

        self.guess_resolution()
        self.parse()
        self.generate_pixmap()

    def guess_resolution(self):
        assert self.decoded
        self.width, self.height = blast_guess_resolution(self.blast, len(self.decoded))

    def parse(self):
        assert self.decoded
        self.raw = blast_parse_image(self.blast, self.decoded, self.width, self.height, False, True)

    def generate_pixmap(self):
        match self.blast:
            case (Blast.BLAST6_IA8 | Blast.BLAST3_IA8 | Blast.BLAST4_IA16):
                bytes_per_pixel = 2
                image_format = QImage.Format_Grayscale16
            case _:
                bytes_per_pixel = 4
                image_format = QImage.Format_RGBA8888

        image = QImage(self.raw, self.width, self.height, bytes_per_pixel * self.width, image_format)

        # Fix grayscale alpha
        if image_format == QImage.Format_Grayscale16:
            image.setAlphaChannel(image)

        self.pixmap = QPixmap.fromImage(image)
