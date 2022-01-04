from blastimation.blast import Blast


class Animation:
    def __init__(self):
        self.name: str = ""
        self.start: int = 0x0
        self.addresses: list[int] = []
        self.blast: Blast = Blast.BLAST0
