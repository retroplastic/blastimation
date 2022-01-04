import pprint
import unittest

import ryaml

from blastimation.blast import Blast
from blastimation.rom import Rom


class Test(unittest.TestCase):
    def test_split_blast5(self):
        rom = Rom("blastcorps.us.v11.assets.yaml")

        blast5_addrs = []

        for image in rom.images.values():
            if image.blast == Blast.BLAST5_RGBA32:
                blast5_addrs.append(image.address)

        with open("meta.yaml", "r") as f:
            meta_yaml = ryaml.load(f)

        single_image_animation_elements = []

        for blast_type_str, animation_list in meta_yaml["animations"].items():
            blast_type = getattr(Blast, blast_type_str)
            if blast_type == Blast.BLAST5_RGBA32:
                for animation in animation_list:
                    single_image_animation_elements.extend(animation)

        blast5_addrs.remove(0x1D83B8)  # Empty, messed up order

        # Remove single element animations
        for e in single_image_animation_elements:
            blast5_addrs.remove(e)

        stuff_from_another_castle = [
            0x224CE8, 0x224DC0, 0x224EB0, 0x224FB8,
            0x225010, 0x2250B0, 0x225170, 0x225240,
            0x225290, 0x225310, 0x2253C0, 0x225450,
            0x2254A0, 0x225500, 0x225580
        ]

        for e in stuff_from_another_castle:
            blast5_addrs.remove(e)

        chunk_size = 4
        chunked_list = [blast5_addrs[i:i + chunk_size] for i in range(0, len(blast5_addrs), chunk_size)]

        for e in chunked_list:
            if len(e) == 4:
                print("      - [0x%06X, 0x%06X, 0x%06X, 0x%06X]" % tuple(e))
            else:
                print("remainder", e)

        print("len", len(blast5_addrs), len(blast5_addrs) / 4)
