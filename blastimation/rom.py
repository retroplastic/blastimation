import struct
import ryaml

from blastimation.blast import Blast, blast_has_lut
from blastimation.image import BlastImage
from blastimation.lut import luts, get_last_lut

ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


class Rom:
    def __init__(self):
        self.images: dict[int:BlastImage] = {}

    def load(self, path: str):
        if path.endswith(".yaml"):
            self.load_yaml(path)
        else:
            self.load_rom(path)

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
                luts[size][address] = data
            elif s["type"] == "blast":
                self.images[address] = BlastImage(s["blast"], address, data, s["width"], s["height"])
                if blast_has_lut(s["blast"]):
                    self.images[address].lut = get_last_lut(s["blast"])

    def load_rom(self, rom_path: str):
        print("Loading directly from ROM...")
        print("WARNING: Resolutions will be broken! You need to load the yaml.")
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
                        luts[size][address] = encoded_bytes
                    continue

                self.images[address] = BlastImage(blast_type, address, encoded_bytes)
                if blast_has_lut(blast_type):
                    self.images[address].lut = get_last_lut(blast_type)


rom = Rom()
