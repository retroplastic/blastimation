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
                0x1FB810: [Comp.RL, 0x1FBEC8],
            },
            Blast.BLAST4_IA16: {
                0x20CFF8: [Comp.Quad, 0x20DB40, 0x20E758, 0x20F120],  # Lake
            }
        }

        composites = {
            1: {
                "TB": {
                    "Ramdozer": [0x1D8420, 0x1D8970],
                    "Cyclone Suit": [0x1DA338, 0x1DA898],
                },
                "RL": {
                    "B1_RL_1FB810": [0x1FB810, 0x1FBEC8],
                }
            },
            4: {
                "Quad": {
                    "Lake": [0x20CFF8, 0x20DB40, 0x20E758, 0x20F120],
                }
            }
        }

        gen_yaml = ryaml.dumps(composites)
        pprint.pprint(gen_yaml)
