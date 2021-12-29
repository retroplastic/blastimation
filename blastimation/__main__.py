#!/usr/bin/env python3
import sys

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPixmap, QImage, QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget, \
    QListView, QAbstractItemView, QComboBox

from blastimation.rom import Rom
from blastimation.blast import Blast, decode_blast_lookup, blast_get_png_writer


class Blastimation(QWidget):
    def __init__(self):
        super().__init__()

        self.image_label = QLabel(self)

        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)

        screen_geometry: QRect = self.screen().geometry()
        self.image_label.setMinimumSize(
            screen_geometry.width() / 8, screen_geometry.height() / 8
        )

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.image_label)

        buttons_layout = QHBoxLayout()

        byte_box = QComboBox()
        self.byte_options = ["1", "2", "4", "8", "16", "32"]
        byte_box.addItems(self.byte_options)
        byte_box.setCurrentIndex(2)
        byte_box.currentIndexChanged.connect(self.on_byte_changed)
        buttons_layout.addWidget(byte_box)

        self.formats = [
            QImage.Format_A2BGR30_Premultiplied,
            QImage.Format_A2RGB30_Premultiplied,
            QImage.Format_Alpha8,
            QImage.Format_ARGB32,
            QImage.Format_ARGB32_Premultiplied,
            QImage.Format_ARGB4444_Premultiplied,
            QImage.Format_ARGB6666_Premultiplied,
            QImage.Format_ARGB8555_Premultiplied,
            QImage.Format_ARGB8565_Premultiplied,
            QImage.Format_BGR30,
            QImage.Format_BGR888,
            QImage.Format_Grayscale16,
            QImage.Format_Grayscale8,
            QImage.Format_Indexed8,
            QImage.Format_Invalid,
            QImage.Format_Mono,
            QImage.Format_MonoLSB,
            QImage.Format_RGB16,
            QImage.Format_RGB30,
            QImage.Format_RGB32,
            QImage.Format_RGB444,
            QImage.Format_RGB555,
            QImage.Format_RGB666,
            QImage.Format_RGB888,
            QImage.Format_RGBA16FPx4,
            QImage.Format_RGBA16FPx4_Premultiplied,
            QImage.Format_RGBA32FPx4,
            QImage.Format_RGBA32FPx4_Premultiplied,
            QImage.Format_RGBA64,
            QImage.Format_RGBA64_Premultiplied,
            QImage.Format_RGBA8888,
            QImage.Format_RGBA8888_Premultiplied,
            QImage.Format_RGBX16FPx4,
            QImage.Format_RGBX32FPx4,
            QImage.Format_RGBX64,
            QImage.Format_RGBX8888,
        ]

        self.format_names = []
        for f in self.formats:
            self.format_names.append(f.name.decode())

        format_box = QComboBox()
        format_box.addItems(self.format_names)
        format_box.setCurrentIndex(30)
        format_box.currentIndexChanged.connect(self.on_format_changed)
        buttons_layout.addWidget(format_box)

        # Image state
        self.bytes_per_pixel = 4
        self.image_data = None
        self.width = 0
        self.height = 0
        self.format = self.formats[30]

        quit_button = QPushButton("Quit", self)
        quit_button.setShortcut(Qt.CTRL | Qt.Key_Q)
        quit_button.clicked.connect(self.close)
        buttons_layout.addWidget(quit_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.setWindowTitle("Blastimation")
        self.resize(300, 200)

        self.pixmap = None

        self.rom = Rom(sys.argv[1])

        self.load_image("00DB08", 1, 32, 32)
        # self.load_image("26A1C0", 1, 40, 40)
        # self.load_image("27DB30", 2, 32, 32)
        # self.load_image("08EBE8", 3, 64, 64)
        # self.load_image_lut("1F0BD8", 4, 64, 32, "047480")
        # self.load_image_lut("1DC880", 5, 32, 32, "152970")
        # self.load_image("33D7D8", 6, 16, 32)

        self.images = {
            "00DB08": [1, 32, 32],
            "26A1C0": [1, 40, 40],
            "27DB30": [2, 32, 32],
            "08EBE8": [3, 64, 64],
            "33D7D8": [6, 16, 32],
            "1F0BD8": [4, 64, 32],
            "1DC880": [5, 32, 32],
            "011570": [5, 32, 32],
            "01A778": [5, 32, 32]
        }

        self.lut_128_key = "047480"
        self.lut_256_key = "152970"

        list_model = QStandardItemModel(0, 1)
        for k in self.images.keys():
            list_model.appendRow(QStandardItem(k))

        list_view = QListView()
        list_view.setObjectName("listView")
        list_view.setModel(list_model)
        list_view.clicked.connect(self.on_list_select)
        list_view.activated.connect(self.on_list_select)
        list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        list_view.setSelectionMode(QAbstractItemView.SingleSelection)
        list_view.setSelectionBehavior(QAbstractItemView.SelectItems)

        lut_model = QStandardItemModel(0, 1)
        for k in self.rom.luts[256].keys():
            lut_model.appendRow(QStandardItem(k))

        lut_view = QListView()
        lut_view.setObjectName("lutView")
        lut_view.setModel(lut_model)
        lut_view.clicked.connect(self.on_lut_select)
        lut_view.activated.connect(self.on_lut_select)
        lut_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lut_view.setSelectionMode(QAbstractItemView.SingleSelection)
        lut_view.setSelectionBehavior(QAbstractItemView.SelectItems)

        lists_layout = QHBoxLayout()
        lists_layout.addWidget(list_view)
        lists_layout.addWidget(lut_view)
        main_layout.addLayout(lists_layout)

        self.current_blast = None

    def on_format_changed(self, index):
        format_name = self.format_names[index]
        self.format = self.formats[index]
        print("Changing format to", index, format_name)
        self.regen_pixmap()
        self.update_image_label()

    def on_byte_changed(self, index):
        self.bytes_per_pixel = int(self.byte_options[index])
        print("bytes", self.bytes_per_pixel)
        self.regen_pixmap()
        self.update_image_label()

    def on_list_select(self, model_index):
        key = model_index.data()
        image_data = self.images[key]

        blast_type = Blast(image_data[0])

        match blast_type:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                self.load_image_lut(key, image_data[0], image_data[1], image_data[2])
            case _:
                self.load_image(key, image_data[0], image_data[1], image_data[2])

        self.update_image_label()

    def on_lut_select(self, model_index):
        self.lut_256_key = model_index.data()
        print("Selected lut", self.lut_256_key)

        self.regen_pixmap()
        self.update_image_label()

    def load_image(self, address: str, blast_id: int, width: int, height: int):
        blast_type = Blast(blast_id)
        decoded_bytes = self.rom.blasts[blast_id][address]

        writer_class = blast_get_png_writer(blast_type)

        self.image_data = writer_class.parse_image(decoded_bytes, width, height, False, True)
        self.width = width
        self.height = height
        self.current_blast = blast_type

        match blast_type:
            case (Blast.BLAST6_IA8 | Blast.BLAST3_IA8 | Blast.BLAST4_IA16):
                self.bytes_per_pixel = 2
                self.format = QImage.Format_Grayscale16
            case _:
                self.bytes_per_pixel = 4
                self.format = QImage.Format_RGBA8888

        self.regen_pixmap()

    def load_image_lut(self, address: str, blast_id: int, width: int, height: int):
        blast_type = Blast(blast_id)

        match blast_type:
            case Blast.BLAST4_IA16:
                lut = self.rom.luts[128][self.lut_128_key]
            case Blast.BLAST5_RGBA32:
                lut = self.rom.luts[256][self.lut_256_key]
            case _:
                return

        self.encoded_bytes = self.rom.blasts[blast_id][address]

        decoded_bytes = decode_blast_lookup(blast_type, self.encoded_bytes, lut)

        writer_class = blast_get_png_writer(blast_type)

        self.image_data = writer_class.parse_image(decoded_bytes, width, height, False, True)
        self.width = width
        self.height = height
        self.current_blast = blast_type

        match blast_type:
            case (Blast.BLAST6_IA8 | Blast.BLAST3_IA8 | Blast.BLAST4_IA16):
                self.bytes_per_pixel = 2
                self.format = QImage.Format_Grayscale16
            case _:
                self.bytes_per_pixel = 4
                self.format = QImage.Format_RGBA8888

        self.regen_pixmap()

    def regen_pixmap(self):
        match self.current_blast:
            case Blast.BLAST4_IA16:
                lut = self.rom.luts[128][self.lut_128_key]
                decoded_bytes = decode_blast_lookup(self.current_blast, self.encoded_bytes, lut)
                writer_class = blast_get_png_writer(self.current_blast)
                self.image_data = writer_class.parse_image(decoded_bytes, self.width, self.height, False, True)
            case Blast.BLAST5_RGBA32:
                lut = self.rom.luts[256][self.lut_256_key]
                decoded_bytes = decode_blast_lookup(self.current_blast, self.encoded_bytes, lut)
                writer_class = blast_get_png_writer(self.current_blast)
                self.image_data = writer_class.parse_image(decoded_bytes, self.width, self.height, False, True)

        image = QImage(self.image_data, self.width, self.height, self.bytes_per_pixel * self.width, self.format)
        self.pixmap = QPixmap.fromImage(image)

    def resizeEvent(self, event):
        scaled_size = self.pixmap.size()
        scaled_size.scale(self.image_label.size(), Qt.KeepAspectRatio)
        if scaled_size != self.image_label.pixmap().size():
            self.update_image_label()

    def update_image_label(self):
        # img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.image_label.setPixmap(
            self.pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.FastTransformation,
            )
        )


def print_usage():
    print("Usage:")
    print(f"{sys.argv[0]} <rom>")


def main():
    if len(sys.argv) != 2:
        print_usage()
        return

    print(f"Opening {sys.argv[1]}...")

    app = QApplication(sys.argv)
    widget = Blastimation()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
