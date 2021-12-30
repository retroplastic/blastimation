import struct
from enum import Enum

import ryaml

from blastimation.blast import Blast
from blastimation.image import BlastImage

ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


class Comp(Enum):
    TopBottom = 0  # Top Bottom (Actually Bottom Top, as we flip)
    RightLeft = 1  # Right Left
    Quad = 2


class Rom:
    def __init__(self, path: str):
        self.luts = {
            128: {},
            256: {}
        }

        self.images = {
            Blast.BLAST1_RGBA16: {},
            Blast.BLAST2_RGBA32: {},
            Blast.BLAST3_IA8: {},
            Blast.BLAST4_IA16: {},
            Blast.BLAST5_RGBA32: {},
            Blast.BLAST6_IA8: {}
        }

        self.composites = {
            Blast.BLAST1_RGBA16: {},
            Blast.BLAST2_RGBA32: {},
            Blast.BLAST3_IA8: {},
            Blast.BLAST4_IA16: {},
            Blast.BLAST5_RGBA32: {},
            Blast.BLAST6_IA8: {}
        }

        if path.endswith(".yaml"):
            self.load_yaml(path)
        else:
            self.load_rom(path)

        self.init_composite_images()

    def load_yaml(self, yaml_path: str):
        with open(yaml_path, "r") as f:
            y = ryaml.load(f)

        rom_path = y['options']['target_path']
        with open(rom_path, "rb") as f:
            rom_bytes = f.read()

        segments = []
        for segment in y["segments"]:
            if len(segments) > 0:
                if "end" not in segments[-1]:
                    if isinstance(segment, list):
                        segments[-1]["end"] = segment[0]
                    elif isinstance(segment, dict):
                        segments[-1]["end"] = segment["start"]

            if isinstance(segment, dict) or len(segment) == 1:
                continue

            if segment[1] == "blast" and segment[3] != 0:
                segment_dict = {
                    "start": segment[0],
                    "blast": Blast(segment[3]),
                    "width": segment[4],
                    "height": segment[5],
                    "type": "blast"
                }
                segments.append(segment_dict)
            elif segment[1] == "bin" and len(segment) == 3 and ".lut" in segment[2]:
                segment_dict = {
                    "start": segment[0],
                    "type": "lut"
                }
                segments.append(segment_dict)

        for s in segments:
            address: int = s["start"]
            data: bytes = rom_bytes[address:s["end"]]
            if s["type"] == "lut":
                size = (s["end"] - s["start"])
                self.luts[size][address] = data
            elif s["type"] == "blast":
                blast_type: Blast = s["blast"]
                self.images[blast_type][address] = BlastImage(blast_type, address, data,
                                                              s["width"], s["height"])

    def load_rom(self, rom_path: str):
        with open(rom_path, "rb") as f:
            rom_bytes = f.read()

        for i in range(ROM_OFFSET, END_OFFSET, 8):
            start = struct.unpack(">I", rom_bytes[i:i + 4])[0]
            size = struct.unpack(">H", rom_bytes[i + 4:i + 6])[0]
            blast_type = Blast(struct.unpack(">H", rom_bytes[i + 6:i + 8])[0])
            assert len(rom_bytes) >= start

            if size > 0:
                address: int = start + ROM_OFFSET
                encoded_bytes = rom_bytes[start + ROM_OFFSET: start + ROM_OFFSET + size]

                assert len(encoded_bytes) == size

                if blast_type == Blast.BLAST0:
                    if size in [128, 256]:
                        self.luts[size][address] = encoded_bytes
                    continue

                self.images[blast_type][address] = BlastImage(blast_type, address, encoded_bytes)

    def init_composite_images(self):
        self.composites.update({
            Blast.BLAST1_RGBA16: {
                # Vehicles
                0x1D8420: [Comp.TopBottom, 0x1D8970],  # Ramdozer
                0x1DA338: [Comp.TopBottom, 0x1DA898],  # Cyclone Suit
                0x1DAE40: [Comp.TopBottom, 0x1F0498],  # Backlash
                0x0D0288: [Comp.RightLeft, 0x0D4410],
                0x0F25B8: [Comp.RightLeft, 0x0F27A8],
                0x1FB810: [Comp.RightLeft, 0x1FBEC8],
                0x112928: [Comp.RightLeft, 0x112060],
                0x278520: [Comp.TopBottom, 0x278890],  # Muscle Car

                0x15F370: [Comp.TopBottom, 0x15F4C0],
                0x15F8C0: [Comp.TopBottom, 0x15FDC0],  # Sideswipe

                0x275528: [Comp.TopBottom, 0x275AA8],  # Blast truck
                0x273858: [Comp.TopBottom, 0x273C38],  # Van
                0x2741A0: [Comp.TopBottom, 0x274350],  # Ballista
                0x276FE0: [Comp.TopBottom, 0x277308],  # J-Bomb
                0x277798: [Comp.TopBottom, 0x278000],  # Thunderfist
                0x2746B8: [Comp.TopBottom, 0x274B20],  # Skyfall
                0x2760C0: [Comp.TopBottom, 0x2764A8],  # American Dream
                0x274E70: [Comp.TopBottom, 0x2751C8],  # Police car

                # stones
                0x2BC5E8: [Comp.TopBottom, 0x2BEE28],
                # 0x2BCFE0: [Comp.TB, 0x2BE2B8],
                0x2BCFE0: [Comp.TopBottom, 0x2BD7E0],

                0x08D4C8: [Comp.TopBottom, 0x08DA10],

                0x2AC268: [Comp.TopBottom, 0x2AC748],
                0x2ACB18: [Comp.TopBottom, 0x2ACF88],
                0x2AD370: [Comp.TopBottom, 0x2AD6F8],

                # $ animation
                0x2ADAA0: [Comp.TopBottom, 0x2ADCF8],
                0x2ADFB0: [Comp.TopBottom, 0x2AE208],
                0x2AE4A8: [Comp.TopBottom, 0x2AE828],
                0x2AEC00: [Comp.TopBottom, 0x2AEF40],
                0x2AF290: [Comp.TopBottom, 0x2AF520],

                0x089EE8: [Comp.TopBottom, 0x08A840],

                0x2CE088: [Comp.RightLeft, 0x2CE7B0],
                0x13A210: [Comp.RightLeft, 0x13AAB8],

                0x15A2A0: [Comp.TopBottom, 0x15A728],

                0x32E570: [Comp.TopBottom, 0x32E718],  # Question mark

                0x20CFF8: [Comp.Quad, 0x20DB40, 0x20E758, 0x20F120],  # Lake

                0x180890: [Comp.RightLeft, 0x182330],

                0x32EEF0: [Comp.TopBottom, 0x32F4F8]  # Lighthouse
            }
        })

    def print_stats(self):
        print("LUTs:")
        for lut_size, lut_dict in self.luts.items():
            print(f"  {lut_size} ({len(lut_dict)}):")
            for addr in lut_dict.keys():
                print("    ", addr)

        print("Blasts:")
        for blast_id, blast_dict in self.images.items():
            print(f"  {Blast(blast_id)} ({len(blast_dict)})")
