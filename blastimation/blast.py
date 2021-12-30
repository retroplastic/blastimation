import struct
from enum import Enum

from blastimation.tex64 import parse_rgba16, parse_ia8


class Blast(Enum):
    BLAST0 = 0
    BLAST1_RGBA16 = 1
    BLAST2_RGBA32 = 2
    BLAST3_IA8 = 3
    BLAST4_IA16 = 4
    BLAST5_RGBA32 = 5
    BLAST6_IA8 = 6


def blast_parse_image(blast_type: Blast, data: bytes,
                      width: int, height: int,
                      flip_h: bool = False, flip_v: bool = False):
    match blast_type:
        case Blast.BLAST1_RGBA16:
            return parse_rgba16(data, width, height, flip_h, flip_v)
        case (Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
            return parse_ia8(data, width, height, flip_h, flip_v)
        case _:
            return data


def blast_get_lut_size(blast_type: Blast):
    match blast_type:
        case Blast.BLAST4_IA16:
            return 128
        case Blast.BLAST5_RGBA32:
            return 256


def blast_is_grayscale(blast_type: Blast) -> bool:
    match blast_type:
        case (Blast.BLAST3_IA8 | Blast.BLAST6_IA8 | Blast.BLAST4_IA16):
            return True
        case _:
            return False


def blast_get_depth(blast_type: Blast) -> int:
    match blast_type:
        case (Blast.BLAST3_IA8 | Blast.BLAST6_IA8):
            return 8
        case (Blast.BLAST1_RGBA16 | Blast.BLAST4_IA16):
            return 16
        case (Blast.BLAST2_RGBA32 | Blast.BLAST5_RGBA32):
            return 32
        case _:
            return 0


def blast_get_format(blast_type: Blast) -> str:
    match blast_type:
        case (Blast.BLAST1_RGBA16 | Blast.BLAST2_RGBA32 | Blast.BLAST5_RGBA32):
            return "rgba"
        case (Blast.BLAST3_IA8 | Blast.BLAST4_IA16 | Blast.BLAST6_IA8):
            return "ia"
        case _:
            return ""


def blast_get_format_id(blast_type: Blast) -> str:
    return "%s%d" % (blast_get_format(blast_type), blast_get_depth(blast_type))


def blast_get_decoded_extension(blast_type: Blast) -> str:
    match blast_type:
        case Blast.BLAST0:
            return "unblast0"
        case _:
            return "%s%d" % (blast_get_format(blast_type), blast_get_depth(blast_type))


# This cannot be reliably determined by the data and needs to be
# tracked manually in the splat yaml.
def blast_guess_resolution(blast_type: Blast, size: int) -> tuple[int, int]:
    match blast_type:
        case Blast.BLAST1_RGBA16:
            match size:
                case 16:   return 4, 2
                case 512:  return 16, 16
                case 1024: return 16, 32
                case 2048: return 32, 32
                case 4096: return 64, 32
                case 8192: return 64, 64
                case 3200: return 40, 40
                case _:    return 32, int(size / (32 * 2))
        case Blast.BLAST2_RGBA32:
            match size:
                case 256:  return 8, 8
                case 512:  return 8, 16
                case 1024: return 16, 16
                case 2048: return 16, 32
                case 4096: return 32, 32
                case 8192: return 64, 32
                case _:    return 32, int(size / (32 * 4))
        case Blast.BLAST3_IA8:
            match size:
                case 1024: return 32, 32
                case 2048: return 32, 64
                case 4096: return 64, 64
                case _:    return 32, int(size / 32)
        case Blast.BLAST4_IA16:
            match size:
                case 1024: return 16, 32
                case 2048: return 32, 32
                case 4096: return 32, 64
                case 8192: return 64, 64
                case _:    return 32, int(size / (32 * 2))
        case Blast.BLAST5_RGBA32:
            match size:
                case 1024: return 16, 16
                case 2048: return 32, 16
                case 4096: return 32, 32
                case 8192: return 64, 32
                case _:    return 32, int(size / (32 * 4))
        case Blast.BLAST6_IA8:
            return 16, int(size / 16)


def decode_blast_generic(encoded: bytes, decode_single_fun, element_size: int,
                         loop_back_and: int, loop_back_shift: int) -> bytes:
    decoded_bytes = bytearray()

    for unpacked in struct.iter_unpack(">H", encoded):
        current = unpacked[0]

        if current & 0x8000 == 0:
            res = decode_single_fun(current)
            decoded_bytes.extend(res)
        else:
            loop_back_length = current & 0x1F
            loop_back_offset = (current & loop_back_and) >> loop_back_shift

            slice_from = len(decoded_bytes) - loop_back_offset
            slice_to = slice_from + loop_back_length * element_size

            decoded_bytes.extend(decoded_bytes[slice_from:slice_to])

    return decoded_bytes


# Based on 802A5AE0 (061320)
def decode_blast1(encoded: bytes) -> bytes:
    def single(current: int) -> bytes:
        t1 = (current & 0xFFC0) << 1
        current &= 0x3F
        current |= t1
        return struct.pack(">H", current)
    return decode_blast_generic(encoded, single, 2, 0x7FFF, 5)


# 802A5B90 (0613D0)
def decode_blast2(encoded: bytes) -> bytes:
    def single(current: int) -> bytes:
        t1 = current & 0x7800
        t2 = current & 0x0780
        t1 <<= 0x11
        t2 <<= 0xD
        t1 |= t2
        t2 = current & 0x78
        t2 <<= 0x9
        t1 |= t2
        t2 = current & 0x7
        t2 <<= 0x5
        t1 |= t2
        return struct.pack(">I", t1)
    return decode_blast_generic(encoded, single, 4, 0x7FE0, 4)


# 802A5A2C (06126C)
def decode_blast3(encoded: bytes) -> bytes:
    def single(current: int) -> bytes:
        part0 = current >> 8
        part0 <<= 1
        part1 = current & 0xFF
        part1 <<= 1

        return struct.pack(">BB", part0, part1)
    return decode_blast_generic(encoded, single, 2, 0x7FFF, 5)


# 802A5C5C (06149C)
def decode_blast4(encoded: bytes, lut: bytes) -> bytes:
    def single(current: int) -> bytes:
        part0 = current >> 8
        t2 = part0 & 0xFE
        lookup_bytes = lut[t2:t2 + 2]
        t2 = struct.unpack(">H", lookup_bytes)[0]
        part0 &= 1
        t2 <<= 1
        part0 |= t2

        part1 = current & 0xFE
        lookup_bytes = lut[part1:part1 + 2]
        part1 = struct.unpack(">H", lookup_bytes)[0]
        current &= 1
        part1 <<= 1
        part1 |= current
        return struct.pack(">HH", part0, part1)
    return decode_blast_generic(encoded, single, 4, 0x7FE0, 4)


# 802A5D34 (061574)
def decode_blast5(encoded: bytes, lut: bytes) -> bytes:
    def single(current: int) -> bytes:
        t1 = current >> 4
        t1 = t1 << 1

        lookup_bytes = lut[t1:t1 + 2]
        t1 = struct.unpack(">H", lookup_bytes)[0]

        current &= 0xF
        current <<= 4
        t2 = t1 & 0x7C00
        t3 = t1 & 0x03E0
        t2 <<= 0x11
        t3 <<= 0xE
        t2 |= t3
        t3 = t1 & 0x1F
        t3 <<= 0xB
        t2 |= t3
        t2 |= current

        return struct.pack(">I", t2)
    return decode_blast_generic(encoded, single, 4, 0x7FE0, 4)


# 802A5958 (061198)
def decode_blast6(encoded: bytes) -> bytes:
    def single(current: int) -> bytes:
        part0 = current >> 8
        t2 = part0 & 0x38
        part0 &= 0x07
        t2 <<= 2
        part0 <<= 1
        part0 |= t2

        part1 = current & 0xFF
        t2 = part1 & 0x38
        part1 &= 0x07
        t2 <<= 2
        part1 <<= 1
        part1 |= t2

        return struct.pack(">BB", part0, part1)
    return decode_blast_generic(encoded, single, 2, 0x7FFF, 5)


def decode_blast(blast_type: Blast, encoded: bytes) -> bytes:
    match blast_type:
        case Blast.BLAST0:
            return encoded
        case Blast.BLAST1_RGBA16:
            return decode_blast1(encoded)
        case Blast.BLAST2_RGBA32:
            return decode_blast2(encoded)
        case Blast.BLAST3_IA8:
            return decode_blast3(encoded)
        case Blast.BLAST6_IA8:
            return decode_blast6(encoded)


def decode_blast_lookup(blast_type: Blast, encoded: bytes, lut: bytes) -> bytes:
    match blast_type:
        case Blast.BLAST4_IA16:
            return decode_blast4(encoded, lut)
        case Blast.BLAST5_RGBA32:
            return decode_blast5(encoded, lut)
