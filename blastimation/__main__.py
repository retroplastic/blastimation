#!/usr/bin/env python3
import sys

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPixmap, QImage, QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget, \
    QListView, QAbstractItemView, QComboBox

from rom import Rom, blast_get_png_writer
from blast import Blast


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

        # Image state
        self.bytes_per_pixel = 4
        self.image_data = None
        self.width = 0
        self.height = 0
        self.format = QImage.Format_RGBA8888

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
            "08EBE8": [3, 64, 64],
            "33D7D8": [6, 16, 32],
        }

        list_model = QStandardItemModel(0, 1)

        for k in self.images.keys():
            list_model.appendRow(QStandardItem(k))

        list_view = QListView()
        list_view.setObjectName("listView")
        list_view.setModel(list_model)
        list_view.clicked.connect(self.on_list_select)
        list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        main_layout.addWidget(list_view)

    def on_byte_changed(self, index):
        self.bytes_per_pixel = int(self.byte_options[index])
        print("bytes", self.bytes_per_pixel)
        self.regen_pixmap()
        self.update_image_label()

    def on_list_select(self, model_index):
        key = model_index.data()
        image_data = self.images[key]
        self.load_image(key, image_data[0], image_data[1], image_data[2])
        self.update_image_label()

    def load_image(self, address: str, blast_id: int, width: int, height: int):
        blast_type = Blast(blast_id)
        decoded_bytes = self.rom.blasts[blast_id][address]

        writer_class = blast_get_png_writer(blast_type)

        self.image_data = writer_class.parse_image(decoded_bytes, width, height, False, True)
        self.width = width
        self.height = height
        self.format = QImage.Format_RGBA8888

        self.regen_pixmap()

    def regen_pixmap(self):
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
                Qt.SmoothTransformation,
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
