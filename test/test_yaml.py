import pprint
import unittest
import ryaml

from blastimation.blast import Blast
from blastimation.rom import Comp


class Test(unittest.TestCase):
    def test_load(self):
        with open("blastcorps.us.v11.assets.yaml", "r") as f:
            y = ryaml.load(f)

    def test_dump(self):
        composites = {
            Blast.BLAST1_RGBA16: {
                # Vehicles
                0x1D8420: [Comp.TB, 0x1D8970],  # Ramdozer
                0x1DA338: [Comp.TB, 0x1DA898],  # Cyclone Suit
            }
        }

        gen_yaml = ryaml.dumps(composites)
        pprint.pprint(gen_yaml)
