from enum import Enum

from blastimation.blast import Blast


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

    def name(self):
        # if self.name:
        #    return self.name

        return "0x%06X" % self.start

    def width(self, images):
        return 0

    def height(self, images):
        return 0

    def encoded_size(self, images):
        return 0

    def decoded_size(self, images):
        return 0
