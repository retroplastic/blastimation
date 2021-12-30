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

        composites = {
            1: {
                "TB": [
                    [0x1D8420, 0x1D8970, "Ramdozer"],
                    [0x1DA338, 0x1DA898, "Cyclone Suit"],
                ],
                "RL": [
                    [0x1FB810, 0x1FBEC8, "B1_RL_1FB810"],
                ]
            },
            4: {
                "Quad": [
                    [0x20CFF8, 0x20DB40, 0x20E758, 0x20F120, "Lake"],
                ]
            }
        }

        gen_yaml = ryaml.dumps(composites)
        pprint.pprint(gen_yaml)

        lines = []

        for blast_id, comp_dict in composites.items():
            lines.append(f"{blast_id}:\n")
            for comp_name, comp_list in comp_dict.items():
                lines.append(f"  {comp_name}:\n")
                for comp in comp_list:
                    comp_strs = []
                    for c in comp:
                        if isinstance(c, int):
                            c_str = "0x%06X" % c
                        elif isinstance(c, str):
                            c_str = c
                        else:
                            raise Exception("Unexpected element.")
                        comp_strs.append(c_str)
                    comp_str = ", ".join(comp_strs)
                    lines.append(f"    - [{comp_str}]\n")

        with open("test.yaml", "w") as f:
            f.writelines(lines)

        with open("test.yaml", "r") as f:
            reloaded = ryaml.load(f)

        pprint.pprint(reloaded)
