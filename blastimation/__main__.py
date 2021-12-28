#!/usr/bin/env python3
import sys

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

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

    def load_image(self, address: str, blast_id: int, width: int, height: int):
        blast_type = Blast(blast_id)
        decoded_bytes = self.rom.blasts[blast_id][address]

        writer_class = blast_get_png_writer(blast_type)

        image_data = writer_class.parse_image(decoded_bytes, width, height, False, True)

        image = QImage(image_data, width, height, 4 * width, QImage.Format_RGBA8888)
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
