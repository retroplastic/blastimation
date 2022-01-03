from PySide6.QtGui import QImage, QPixmap

from blastimation.blast import Blast, blast_guess_resolution, blast_parse_image, decode_blast, decode_blast_lookup, \
    blast_get_format_id


class BlastImage:
    def __init__(self, blast_type: Blast, address: int, encoded: bytes = b"",
                 width: int = 0, height: int = 0):
        self.address: int = address
        self.width: int = width
        self.height: int = height
        self.lut: int = 0

        self.blast: Blast = blast_type
        self.encoded: bytes = encoded

        if encoded:
            self.encoded_size: int = len(encoded)
        else:
            self.encoded_size: int = 0
        self.decoded_size: int = 0

        self.pixmap: QPixmap = None
        self.qimage: QImage = None

    def model_data(self):
        return [
            "0x%06X" % self.address,
            "?",
            self.blast.name,
            blast_get_format_id(self.blast),
            self.width,
            self.height,
            self.encoded_size,
            self.decoded_size
        ]

    def decode(self):
        if self.pixmap:
            return

        assert self.encoded
        assert self.blast not in [Blast.BLAST4_IA16, Blast.BLAST5_RGBA32]
        decoded = decode_blast(self.blast, self.encoded)

        self.decoded_size = len(decoded)

        if not self.width or not self.height:
            self.guess_resolution(decoded)
        raw = self.parse(decoded)
        self.generate_pixmap(raw)

    def decode_lut(self, lut: bytes):
        assert self.encoded
        assert self.blast in [Blast.BLAST4_IA16, Blast.BLAST5_RGBA32]
        decoded = decode_blast_lookup(self.blast, self.encoded, lut)

        self.decoded_size = len(decoded)

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
