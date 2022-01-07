import struct
import ryaml

from blastimation.animation_comp import AnimationComp
from blastimation.blast import Blast, blast_get_lut_size
from blastimation.comp import CompType, Composite
from blastimation.image import BlastImage

ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


class Rom:
    def __init__(self, path: str):
        self.luts = {
            128: {},
            256: {}
        }

        self.lut_overrides: dict[int, list[int]] = {}
        self.in_comp: list[int] = []

        self.images: dict[int:BlastImage] = {}
        self.comps: dict[int:Composite] = {}

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
                self.images[address] = BlastImage(s["blast"], address, data, s["width"], s["height"])
                self.images[address].lut = self.determine_lut(s["blast"])

    def determine_lut(self, blast: Blast) -> int:
        # Check for lut type
        match blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                pass
            case _:
                return 0

        # Return last
        lut_size = blast_get_lut_size(blast)
        lut_keys = list(self.luts[lut_size].keys())
        lut_keys.sort()
        return lut_keys[-1]

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
                        self.luts[size][address] = encoded_bytes
                    continue

                self.images[address] = BlastImage(blast_type, address, encoded_bytes)
                self.images[address].lut = self.determine_lut(blast_type)

    def init_composite_images(self):
        with open("meta.yaml", "r") as f:
            composites_yaml = ryaml.load(f)

        for comp_type_str, comp_list in composites_yaml["composites"].items():
            comp_type = getattr(CompType, comp_type_str)
            for addresses in comp_list:
                c = Composite()
                c.type = comp_type
                if isinstance(addresses[-1], str):
                    c.name = addresses[-1]
                    c.addresses = addresses[:-1]
                else:
                    c.addresses = addresses
                    c.name = ""

                self.in_comp.extend(c.addresses)
                self.comps[c.start()] = c

                # Fix LUTs
                if c.start() in [0x0999E0]:
                    first_lut = self.images[c.start()].lut
                    for addr in c.addresses:
                        self.images[addr].lut = first_lut

        for comp_type_str, animations_dict in composites_yaml["composite_animations"].items():
            comp_type = getattr(CompType, comp_type_str)
            for animation_name, comps_list in animations_dict.items():
                animation_comp = AnimationComp()
                animation_comp.name = animation_name
                i = 0
                for addresses in comps_list:
                    c = Composite()
                    c.name = f"{animation_name}.{i}"
                    i += 1
                    c.addresses = addresses
                    c.type = comp_type

                    self.in_comp.extend(c.addresses)
                    animation_comp.comps.append(c)
                self.comps[animation_comp.start()] = animation_comp

                # Fix LUTs
                if animation_comp.start() in [0x1D0DF8, 0x281C90]:
                    first_lut = self.images[animation_comp.start()].lut
                    for comp in animation_comp.comps:
                        for addr in comp.addresses:
                            self.images[addr].lut = first_lut
