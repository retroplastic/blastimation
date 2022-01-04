import unittest

from blastimation.blast import Blast
from blastimation.rom import Rom


class Test(unittest.TestCase):
    def test_split_blast5(self):
        rom = Rom("blastcorps.us.v11.assets.yaml")

        blast5_addrs = []

        for image in rom.images.values():
            if image.blast == Blast.BLAST5_RGBA32:
                blast5_addrs.append(image.address)

        #for a in blast5_addrs:
        #    print(a)

        print("len", len(blast5_addrs), len(blast5_addrs) / 4)

        chunk_size = 4
        chunked_list = [blast5_addrs[i:i + chunk_size] for i in range(0, len(blast5_addrs), chunk_size)]

        for e in chunked_list:
            print("      - [0x%06X, 0x%06X, 0x%06X, 0x%06X]" % tuple(e))
