from blastimation.blast import blast_get_format_id
from blastimation.comp import Composite, CompType


class AnimationComp:
    def __init__(self):
        self.name: str = ""
        self.comps: list[Composite] = []
        self.type = CompType.AnimationComp

    def blast(self, images):
        return self.comps[0].blast(images)

    def start(self):
        return self.comps[0].start()

    def width(self, images):
        return self.comps[0].width(images)

    def height(self, images):
        return self.comps[0].height(images)

    def encoded_size(self, images):
        size = 0
        for c in self.comps:
            size += c.encoded_size(images)
        return size

    def decoded_size(self, images):
        size = 0
        for c in self.comps:
            size += c.decoded_size(images)
        return size

    def frames(self):
        return len(self.comps)

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
