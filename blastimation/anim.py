from blastimation.blast import Blast, blast_get_format_id


class Animation:
    def __init__(self):
        self.name: str = ""
        self.start: int = 0x0
        self.addresses: list[int] = []
        self.blast: Blast = Blast.BLAST0

    def width(self, images):
        return images[self.addresses[0]].width

    def height(self, images):
        return images[self.addresses[0]].height

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
        return len(self.addresses)

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
            self.frames(),
        ]
