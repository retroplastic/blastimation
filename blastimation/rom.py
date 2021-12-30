import struct
from enum import Enum

import yaml

from blastimation.blast import Blast
from blastimation.image import BlastImage

ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


class CompType(Enum):
    TB = 0  # Top Bottom (Actually Bottom Top, as we flip)
    RL = 1  # Right Left


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
            y = yaml.safe_load(f)

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
        # Vehicles
        self.composites[Blast.BLAST1_RGBA16][0x1D8420] = [CompType.TB, 0x1D8970]
        self.composites[Blast.BLAST1_RGBA16][0x1DA338] = [CompType.TB, 0x1DA898]
        self.composites[Blast.BLAST1_RGBA16][0x1DAE40] = [CompType.TB, 0x1F0498]
        self.composites[Blast.BLAST1_RGBA16][0x0D0288] = [CompType.RL, 0x0D4410]
        self.composites[Blast.BLAST1_RGBA16][0x0F25B8] = [CompType.RL, 0x0F27A8]
        self.composites[Blast.BLAST1_RGBA16][0x1FB810] = [CompType.RL, 0x1FBEC8]
        self.composites[Blast.BLAST1_RGBA16][0x278520] = [CompType.RL, 0x278890]

        self.composites[Blast.BLAST1_RGBA16][0x2AC268] = [CompType.TB, 0x2AC748]
        self.composites[Blast.BLAST1_RGBA16][0x2ACB18] = [CompType.TB, 0x2ACF88]
        self.composites[Blast.BLAST1_RGBA16][0x2AD6F8] = [CompType.TB, 0x2AD370]

        # $ animation
        self.composites[Blast.BLAST1_RGBA16][0x2ADAA0] = [CompType.TB, 0x2ADCF8]
        self.composites[Blast.BLAST1_RGBA16][0x2ADFB0] = [CompType.TB, 0x2AE208]
        self.composites[Blast.BLAST1_RGBA16][0x2AE4A8] = [CompType.TB, 0x2AE828]
        self.composites[Blast.BLAST1_RGBA16][0x2AEC00] = [CompType.TB, 0x2AEF40]
        self.composites[Blast.BLAST1_RGBA16][0x2AF290] = [CompType.TB, 0x2AF520]

        self.composites[Blast.BLAST1_RGBA16][0x08A840] = [CompType.TB, 0x089EE8]

    def print_stats(self):
        print("LUTs:")
        for lut_size, lut_dict in self.luts.items():
            print(f"  {lut_size} ({len(lut_dict)}):")
            for addr in lut_dict.keys():
                print("    ", addr)

        print("Blasts:")
        for blast_id, blast_dict in self.images.items():
            print(f"  {Blast(blast_id)} ({len(blast_dict)})")
