from enum import Enum

from PySide6.QtCore import QPoint
from PySide6.QtGui import QImage, QColor, QPainter, QPixmap

from blastimation.blast import blast_get_format_id
from blastimation.image import BlastImage


class CompType(Enum):
    Single = 0
    TopBottom = 1
    RightLeft = 2
    Quad = 3
    Animation = 4


class Composite:
    def __init__(self):
        self.name: str = ""
        self.addresses: list[int] = []
        self.type: CompType = CompType.Single

    def blast(self, images):
        return images[self.start()].blast

    def start(self):
        return self.addresses[0]

    def width(self, images):
        w = images[self.start()].width
        match self.type:
            case (CompType.RightLeft | CompType.Quad):
                return w * 2
            case _:
                return w

    def height(self, images):
        h = images[self.start()].height
        match self.type:
            case (CompType.TopBottom | CompType.Quad):
                return h * 2
            case _:
                return h

    def encoded_size(self, images):
        size = 0
        for a in self.addresses:
            size += images[a].encoded_size
        return size

    def decoded_size(self, images):
        size = 0
        for a in self.addresses:
            size += images[a].decoded_size
        return size

    def frames(self):
        match self.type:
            case CompType.Animation:
                return len(self.addresses)
            case _:
                return 1

    def model_data(self, images):
        return [
            "0x%06X" % self.start(),
            self.name,
            self.blast(images).name,
            blast_get_format_id(self.blast(images)),
            self.width(images),
            self.height(images),
            self.encoded_size(images),
            self.decoded_size(images),
            self.type.name,
            self.frames()
        ]

    def get_image(self, raw_images: dict[int, BlastImage]) -> BlastImage:
        assert self.type in [CompType.TopBottom, CompType.RightLeft, CompType.Quad]

        images = []
        for addr in self.addresses:
            i = raw_images[addr]
            i.decode()
            images.append(i)

        match self.type:
            case CompType.TopBottom:
                width = images[0].width
                height = images[0].height * 2
            case CompType.RightLeft:
                width = images[0].width * 2
                height = images[0].height
            case CompType.Quad:
                width = images[0].width * 2
                height = images[0].height * 2
            case _:
                width = 0
                height = 0

        composite_image = QImage(width, height, QImage.Format_ARGB32)
        composite_image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(composite_image)

        match self.type:
            case CompType.TopBottom:
                painter.drawImage(QPoint(0, 0), images[1].qimage)
                painter.drawImage(QPoint(0, int(height/2)), images[0].qimage)
            case CompType.RightLeft:
                painter.drawImage(QPoint(0, 0), images[1].qimage)
                painter.drawImage(QPoint(int(width / 2), 0), images[0].qimage)
            case CompType.Quad:
                painter.drawImage(QPoint(0, 0), images[2].qimage)
                painter.drawImage(QPoint(int(width / 2), 0), images[3].qimage)
                painter.drawImage(QPoint(0, int(height / 2)), images[0].qimage)
                painter.drawImage(QPoint(int(width / 2), int(height / 2)), images[1].qimage)

        painter.end()

        image = BlastImage(self.blast(raw_images), self.start(), b"", width, height)
        image.pixmap = QPixmap.fromImage(composite_image)

        return image
