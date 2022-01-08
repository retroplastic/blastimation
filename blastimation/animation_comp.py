from blastimation.blast import blast_get_format_id
from blastimation.comp import Composite, CompType


class AnimationComp:
    def __init__(self):
        self.name: str = ""
        self.comps: list[Composite] = []
        self.type = CompType.AnimationComp

    def blast(self):
        return self.comps[0].blast()

    def start(self):
        return self.comps[0].start()

    def width(self):
        return self.comps[0].width()

    def height(self):
        return self.comps[0].height()

    def encoded_size(self):
        size = 0
        for c in self.comps:
            size += c.encoded_size()
        return size

    def decoded_size(self):
        size = 0
        for c in self.comps:
            size += c.decoded_size()
        return size

    def frames(self):
        return len(self.comps)

    def lut(self):
        return self.comps[0].lut()

    def set_lut(self, lut: int):
        for c in self.comps:
            c.set_lut(lut)

    def model_data(self):
        return [
            "0x%06X" % self.start(),
            self.name,
            self.blast().name,
            blast_get_format_id(self.blast()),
            self.width(),
            self.height(),
            self.encoded_size(),
            self.decoded_size(),
            self.type.name,
            self.frames()
        ]
