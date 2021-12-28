import png
from splat_img import iter
from splat_img.color import unpack_color


class N64SegRgba16:
    @staticmethod
    def get_writer(width, height):
        return png.Writer(width, height, greyscale=False, alpha=True)

    @staticmethod
    def parse_image(data, width, height, flip_h=False, flip_v=False):
        img = bytearray()

        for x, y, i in iter.iter_image_indexes(width, height, 2, 1, flip_h, flip_v):
            img += bytes(unpack_color(data[i:]))

        return img
