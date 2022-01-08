import io
import os

from PySide6.QtCore import QBuffer
from PySide6.QtWidgets import QApplication

from blastimation.comp import CompType
from blastimation.meta import Meta
from blastimation.rom import rom

from PIL import Image

rom.load("blastcorps.us.v11.assets.yaml")

os.makedirs("gifs", exist_ok=True)

meta = Meta()

QApplication()

for addr, comp in meta.comps.items():
    if comp.type in [CompType.Animation, CompType.AnimationComp]:
        print("%06X" % addr, comp, comp.frames())
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

        images = []
        for pixmap in frame_pixmaps:
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            pixmap.save(buffer, "PNG")
            images.append(Image.open(io.BytesIO(buffer.data())))

        images[0].save('gifs/%06X.png' % addr)

        images[0].save('gifs/%06X.gif' % addr,
                       save_all=True, append_images=images[1:],
                       optimize=True,
                       loop=0)
