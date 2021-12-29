import sys

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget, \
    QListView, QAbstractItemView, QComboBox

from blastimation.rom import Rom
from blastimation.blast import Blast


class App(QWidget):
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

        self.setWindowTitle("Blastimation")
        self.resize(300, 200)

        self.rom = Rom(sys.argv[1])
        self.image = self.rom.images[1]["00DB08"]
        self.image.decode()

        self.images = {
            "00DB08": [1],
            "26A1C0": [1],
            "27DB30": [2],
            "08EBE8": [3],
            "33D7D8": [6],
            "1F0BD8": [4],
            "1DC880": [5],
            "011570": [5],
            "01A778": [5]
        }

        self.lut_128_key = "047480"
        self.lut_256_key = "152970"

        list_model = QStandardItemModel(0, 1)
        for k in self.images.keys():
            list_model.appendRow(QStandardItem(k))

        blast_list_view = QListView()
        blast_list_view.setObjectName("listView")
        blast_list_view.setModel(list_model)
        blast_list_view.selectionModel().currentChanged.connect(self.on_list_select)
        blast_list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.blast_types = [
            Blast.BLAST1_RGBA16,
            Blast.BLAST2_RGBA32,
            Blast.BLAST3_IA8,
            Blast.BLAST4_IA16,
            Blast.BLAST5_RGBA32,
            Blast.BLAST6_IA8,
        ]

        blast_type_names = []
        for t in self.blast_types:
            blast_type_names.append(t.name)

        blast_filter_box = QComboBox()
        blast_filter_box.addItems(blast_type_names)
        blast_filter_box.setCurrentIndex(0)

        blast_list_layout = QVBoxLayout()
        blast_list_layout.addWidget(blast_filter_box)
        blast_list_layout.addWidget(blast_list_view)

        lut_model = QStandardItemModel(0, 1)
        for k in self.rom.luts[256].keys():
            lut_model.appendRow(QStandardItem(k))

        lut_view = QListView()
        lut_view.setObjectName("lutView")
        lut_view.setModel(lut_model)
        lut_view.selectionModel().currentChanged.connect(self.on_lut_select)
        lut_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        lut_auto_button = QPushButton("Select closest", self)
        # lut_auto_button.clicked.connect(self.close)

        lut_layout = QVBoxLayout()
        lut_layout.addWidget(lut_view)
        lut_layout.addWidget(lut_auto_button)

        lists_layout = QHBoxLayout()
        lists_layout.addLayout(blast_list_layout)
        lists_layout.addLayout(lut_layout)
        main_layout.addLayout(lists_layout)

        self.current_blast = None

    def on_list_select(self, model_index):
        key = model_index.data()
        image_data = self.images[key]

        blast_type = Blast(image_data[0])

        match blast_type:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                self.load_image_lut(key, image_data[0])
            case _:
                self.load_image(key, image_data[0])

        self.update_image_label()

    def on_lut_select(self, model_index):
        self.lut_256_key = model_index.data()
        print("Selected lut", self.lut_256_key)
        match self.image.blast:
            case Blast.BLAST4_IA16:
                lut = self.rom.luts[128][self.lut_128_key]
                self.image.decode_lut(lut)
                self.update_image_label()
            case Blast.BLAST5_RGBA32:
                lut = self.rom.luts[256][self.lut_256_key]
                self.image.decode_lut(lut)
                self.update_image_label()

    def load_image(self, address: str, blast_id: int):
        self.image = self.rom.images[blast_id][address]
        self.image.decode()

    def load_image_lut(self, address: str, blast_id: int):
        self.image = self.rom.images[blast_id][address]

        match Blast(blast_id):
            case Blast.BLAST4_IA16:
                lut = self.rom.luts[128][self.lut_128_key]
            case Blast.BLAST5_RGBA32:
                lut = self.rom.luts[256][self.lut_256_key]
            case _:
                return
        self.image.decode_lut(lut)

    def resizeEvent(self, event):
        scaled_size = self.image.pixmap.size()
        scaled_size.scale(self.image_label.size(), Qt.KeepAspectRatio)
        if scaled_size != self.image_label.pixmap().size():
            self.update_image_label()

    def update_image_label(self):
        self.image_label.setPixmap(
            self.image.pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.FastTransformation,
            )
        )