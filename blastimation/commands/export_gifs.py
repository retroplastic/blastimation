import io
import os
import shutil
import subprocess

from PySide6.QtCore import QBuffer
from PySide6.QtWidgets import QApplication

from blastimation.comp import CompType
from blastimation.gif_converter import TransparentAnimatedGifConverter
from blastimation.meta import Meta
from blastimation.rom import rom

from PIL import Image

rom.load("blastcorps.us.v11.assets.yaml")

os.makedirs("export/gif", exist_ok=True)
os.makedirs("export/png", exist_ok=True)

do_webp = False
img2webp_path = shutil.which("img2webp")
if img2webp_path:
    do_webp = True
    os.makedirs("export/webp", exist_ok=True)
else:
    print("If you want to export animated WebP, install img2webp (from libwebp).")

do_apng = False
apngasm_path = shutil.which("apngasm")
if img2webp_path:
    do_apng = True
    os.makedirs("export/apng", exist_ok=True)
else:
    print("If you want to export animated WebP, install apngasm.")

meta = Meta()

QApplication()

for addr, comp in meta.comps.items():
    if comp.type in [CompType.Animation, CompType.AnimationComp]:
        print("%06X" % addr, comp.frames())
        frame_pixmaps = []
        for i in range(comp.frames()):
            match comp.type:
                case CompType.Animation:
                    frame_addr = comp.addresses[i]
                    image = rom.images[frame_addr]
                    image.decode()
                    frame_pixmaps.append(image.pixmap)
                case CompType.AnimationComp:
                    image = comp.comps[i].get_image()
                    frame_pixmaps.append(image.pixmap)

        i = 0
        pngs = []
        for pixmap in frame_pixmaps:
            png_path = 'export/png/%06X.%02d.png' % (addr, i)
            pixmap.save(png_path)
            pngs.append(png_path)
            i += 1

        if do_webp:
            command = ["img2webp"]
            command.extend(pngs)
            command.extend(["-o", "export/webp/%06X.webp" % addr])
            subprocess.run(command)

        if do_apng:
            command = ["apngasm", "export/apng/%06X.png" % addr]
            command.extend(pngs)
            subprocess.run(command)

        images = []
        for pixmap in frame_pixmaps:
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            pixmap.save(buffer, "PNG")

            im = Image.open(io.BytesIO(buffer.data()))
            im2 = im.convert(mode='RGBA')
            converter = TransparentAnimatedGifConverter(img_rgba=im2)
            thumbnail_p = converter.process()
            images.append(thumbnail_p)

        images[0].save('export/gif/%06X.gif' % addr,
                       save_all=True, append_images=images[1:],
                       optimize=False,
                       disposal=2,
                       loop=0,
                       transparency=0)
