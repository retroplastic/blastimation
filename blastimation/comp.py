from enum import Enum

from blastimation.blast import Blast, blast_get_format_id


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
        self.blast: Blast = Blast.BLAST0
        self.type: CompType = CompType.Single

    def start(self):
        return self.addresses[0]

    def width(self, images):
        w = images[self.addresses[0]].width
        match self.type:
            case (CompType.RightLeft | CompType.Quad):
                return w * 2
            case _:
                return w

    def height(self, images):
        h = images[self.addresses[0]].height
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
            self.blast.name,
            blast_get_format_id(self.blast),
            self.width(images),
            self.height(images),
            self.encoded_size(images),
            self.decoded_size(images),
            self.type.name,
            self.frames()
        ]
