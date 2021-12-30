from PySide6.QtGui import QImage, QPixmap

from blastimation.blast import Blast, blast_guess_resolution, blast_parse_image, decode_blast, decode_blast_lookup


class BlastImage:
    def __init__(self, blast_type: Blast, address: int, encoded: bytes,
                 width: int = 0, height: int = 0):
        self.address: int = address
        self.width: int = width
        self.height: int = height

        self.blast: Blast = blast_type
        self.encoded: bytes = encoded
        self.pixmap: QPixmap = None
        self.qimage: QImage = None

    def decode(self):
        if self.pixmap:
            return

        assert self.encoded
        assert self.blast not in [Blast.BLAST4_IA16, Blast.BLAST5_RGBA32]
        decoded = decode_blast(self.blast, self.encoded)

        if not self.width or not self.height:
            self.guess_resolution(decoded)
        raw = self.parse(decoded)
        self.generate_pixmap(raw)

    def decode_lut(self, lut: bytes):
        assert self.encoded
        assert self.blast in [Blast.BLAST4_IA16, Blast.BLAST5_RGBA32]
        decoded = decode_blast_lookup(self.blast, self.encoded, lut)

        if not self.width or not self.height:
            self.guess_resolution(decoded)
        raw = self.parse(decoded)
        self.generate_pixmap(raw)

    def guess_resolution(self, decoded: bytes):
        self.width, self.height = blast_guess_resolution(self.blast, len(decoded))

    def parse(self, decoded: bytes) -> bytes:
        return blast_parse_image(self.blast, decoded, self.width, self.height, False, True)

    def generate_pixmap(self, raw: bytes):
        match self.blast:
            case (Blast.BLAST6_IA8 | Blast.BLAST3_IA8 | Blast.BLAST4_IA16):
                bytes_per_pixel = 2
                image_format = QImage.Format_Grayscale16
            case _:
                bytes_per_pixel = 4
                image_format = QImage.Format_RGBA8888

        self.qimage = QImage(raw, self.width, self.height, bytes_per_pixel * self.width, image_format)

        # Fix grayscale alpha
        if image_format == QImage.Format_Grayscale16:
            self.qimage.setAlphaChannel(self.qimage)

        self.pixmap = QPixmap.fromImage(self.qimage)
