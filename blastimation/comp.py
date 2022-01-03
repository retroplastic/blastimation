from enum import Enum

from blastimation.blast import Blast, blast_get_format_id


class CompType(Enum):
    TopBottom = 0  # Top Bottom (Actually Bottom Top, as we flip)
    RightLeft = 1  # Right Left
    Quad = 2


class Composite:
    def __init__(self):
        self.name: str = ""
        self.start: int = 0x0
        self.addresses: list[int] = []
        self.blast: Blast = Blast.BLAST0
        self.type: CompType = CompType.TopBottom

    def width(self, images):
        single_width = images[self.addresses[-1]].width
        match self.type:
            case CompType.TopBottom:
                return single_width
            case (CompType.RightLeft | CompType.Quad):
                return single_width * 2

    def height(self, images):
        single_height = images[self.addresses[-1]].height
        match self.type:
            case CompType.RightLeft:
                return single_height
            case (CompType.TopBottom | CompType.Quad):
                return single_height * 2

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

    def model_data(self, images):
        return [
            "0x%06X" % self.addresses[0],
            self.name,
            self.blast.name,
            blast_get_format_id(self.blast),
            self.width(images),
            self.height(images),
            self.encoded_size(images),
            self.decoded_size(images),
            self.type.name,
        ]