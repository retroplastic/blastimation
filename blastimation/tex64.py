# Based on splat

from math import ceil


# RRRRRGGG GGBBBBBA
def unpack_color(data):
    s = int.from_bytes(data, byteorder="big")

    r = (s >> 11) & 0x1F
    g = (s >>  6) & 0x1F
    b = (s >>  1) & 0x1F
    a = (s &   1) * 0xFF

    r = ceil(0xFF * (r / 31))
    g = ceil(0xFF * (g / 31))
    b = ceil(0xFF * (b / 31))

    return r, g, b, a


def iter_image_indexes(width, height,
                       bytes_per_x: float = 1.0, bytes_per_y: float = 1.0,
                       flip_h: bool = False, flip_v: bool = False):
    w = int(width * bytes_per_x)
    h = int(height * bytes_per_y)

    xrange = range(w - ceil(bytes_per_x), -1, -ceil(bytes_per_x)) if flip_h else range(0, w, ceil(bytes_per_x))
    yrange = range(h - ceil(bytes_per_y), -1, -ceil(bytes_per_y)) if flip_v else range(0, h, ceil(bytes_per_y))

    for y in yrange:
        for x in xrange:
            yield x, y, (y * w) + x


def parse_rgba16(data, width, height, flip_h=False, flip_v=False):
    img = bytearray()

    for x, y, i in iter_image_indexes(width, height, 2, 1, flip_h, flip_v):
        img += bytes(unpack_color(data[i:i + 2]))

    return img


def parse_rgba32(data, width, height, flip_h=False, flip_v=False):
    if not flip_h and not flip_v:
        return data

    img = bytearray()
    for x, y, i in iter_image_indexes(width, height, 4, 1, flip_h, flip_v):
        img += data[i:i+4]

    return img


def parse_ia8(data, width, height, flip_h=False, flip_v=False):
    img = bytearray()

    for x, y, i in iter_image_indexes(width, height, flip_h=flip_h, flip_v=flip_v):
        b = data[i]

        i = (b >> 4) & 0xF
        a = b & 0xF

        i = ceil(0xFF * (i / 15))
        a = ceil(0xFF * (a / 15))

        img += bytes((i, a))

    return img
