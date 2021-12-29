import struct

from blastimation.blast import Blast, decode_blast


ROM_OFFSET = 0x4CE0
END_OFFSET = 0xCCE0


class Rom:
    def __init__(self, path: str):
        self.luts = {
            128: {},
            256: {}
        }

        self.blasts = {
            1: {},
            2: {},
            3: {},
            4: {},
            5: {},
            6: {}
        }

        with open(path, "rb") as f:
            self.read(f.read())

    def read(self, rom_bytes: bytes):
        for i in range(ROM_OFFSET, END_OFFSET, 8):
            start = struct.unpack(">I", rom_bytes[i:i + 4])[0]
            size = struct.unpack(">H", rom_bytes[i + 4:i + 6])[0]
            blast_type = Blast(struct.unpack(">H", rom_bytes[i + 6:i + 8])[0])
            assert len(rom_bytes) >= start

            if size > 0:
                address = "%06X" % (start + ROM_OFFSET)
                encoded_bytes = rom_bytes[start + ROM_OFFSET: start + ROM_OFFSET + size]

                assert len(encoded_bytes) == size

                match blast_type:
                    case Blast.BLAST0:
                        if size == 128 or size == 256:
                            self.luts[size][address] = encoded_bytes
                    case (Blast.BLAST1_RGBA16 | Blast.BLAST2_RGBA32 | Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
                        self.blasts[blast_type.value][address] = decode_blast(blast_type, encoded_bytes)
                    case _:
                        self.blasts[blast_type.value][address] = encoded_bytes

    def print_stats(self):
        print("LUTs:")
        for lut_size, lut_dict in self.luts.items():
            print(f"  {lut_size} ({len(lut_dict)}):")
            for addr in lut_dict.keys():
                print("    ", addr)

        print("Blasts:")
        for blast_id, blast_dict in self.blasts.items():
            print(f"  {Blast(blast_id)} ({len(blast_dict)})")
