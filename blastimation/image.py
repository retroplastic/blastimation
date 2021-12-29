from blastimation.blast import Blast


class BlastImage:
    def __init__(self):
        self.addr = ""

        self.width = 0
        self.height = 0

        self.blast = Blast.BLAST0
        self.encoded = None
        self.decoded = None
