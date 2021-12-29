import sys

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget, \
    QListView, QAbstractItemView, QComboBox

from blastimation.rom import Rom
from blastimation.blast import Blast, blast_get_lut_size


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
        self.image = list(self.rom.images[Blast.BLAST1_RGBA16].values())[0]
        self.image.decode()

        self.current_lut = {
            128: int("047480", 16),
            256: int("152970", 16)
        }

        self.blast_types = [
            Blast.BLAST1_RGBA16,
            Blast.BLAST2_RGBA32,
            Blast.BLAST3_IA8,
            Blast.BLAST4_IA16,
            Blast.BLAST5_RGBA32,
            Blast.BLAST6_IA8,
        ]
        self.blast_filter: Blast = Blast.BLAST1_RGBA16

        blast_type_names = []
        for t in self.blast_types:
            blast_type_names.append(t.name)

        blast_filter_box = QComboBox()
        blast_filter_box.addItems(blast_type_names)
        blast_filter_box.setCurrentIndex(0)
        blast_filter_box.currentIndexChanged.connect(self.on_blast_filter_changed)

        self.blast_list_models = {}
        for t in self.blast_types:
            self.blast_list_models[t] = QStandardItemModel(0, 1)
            for k in self.rom.images[t].keys():
                self.blast_list_models[t].appendRow(QStandardItem("%06X" % k))

        self.blast_list_view = QListView()
        self.blast_list_view.setObjectName("listView")
        self.blast_list_view.setModel(self.blast_list_models[Blast.BLAST1_RGBA16])
        self.blast_list_view.selectionModel().currentChanged.connect(self.on_list_select)
        self.blast_list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        blast_list_layout = QVBoxLayout()
        blast_list_layout.addWidget(blast_filter_box)
        blast_list_layout.addWidget(self.blast_list_view)

        self.lut_models = {}
        for lut_size in self.current_lut.keys():
            self.lut_models[lut_size] = QStandardItemModel(0, 1)
            for k in self.rom.luts[lut_size].keys():
                self.lut_models[lut_size].appendRow(QStandardItem("%06X" % k))

        self.lut_view = QListView()
        self.lut_view.setObjectName("lutView")
        self.lut_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        lut_auto_button = QPushButton("Select closest", self)
        lut_auto_button.clicked.connect(self.on_auto_lut)

        lut_layout = QVBoxLayout()
        lut_layout.addWidget(self.lut_view)
        lut_layout.addWidget(lut_auto_button)

        lists_layout = QHBoxLayout()
        lists_layout.addLayout(blast_list_layout)
        lists_layout.addLayout(lut_layout)
        main_layout.addLayout(lists_layout)

        self.current_blast = None

    def on_list_select(self, model_index):
        address = int(model_index.data(), 16)
        self.image = self.rom.images[self.blast_filter][address]

        match self.blast_filter:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.blast_filter)
                lut = self.rom.luts[lut_size][self.current_lut[lut_size]]
                self.image.decode_lut(lut)
            case _:
                self.image.decode()

        self.update_image_label()

    def on_lut_select(self, model_index):
        lut_addr = int(model_index.data(), 16)

        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.blast_filter)
                self.current_lut[lut_size] = lut_addr
                lut = self.rom.luts[lut_size][self.current_lut[lut_size]]
                self.image.decode_lut(lut)
                self.update_image_label()

    def on_blast_filter_changed(self, index):
        self.blast_filter = self.blast_types[index]
        self.blast_list_view.setModel(self.blast_list_models[self.blast_filter])
        self.blast_list_view.selectionModel().currentChanged.connect(self.on_list_select)

        index = self.blast_list_models[self.blast_filter].index(0, 0)
        self.blast_list_view.setCurrentIndex(index)

        match self.blast_filter:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.blast_filter)
                self.lut_view.setModel(self.lut_models[lut_size])
                self.lut_view.selectionModel().currentChanged.connect(self.on_lut_select)
            case _:
                self.lut_view.setModel(None)

    def on_auto_lut(self):
        match self.blast_filter:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.blast_filter)

                last_k = 0
                lut_keys = list(self.rom.luts[lut_size].keys())
                lut_keys.sort()

                row = -1
                for k in lut_keys:
                    if k > self.image.address:
                        break
                    last_k = k
                    row += 1
                assert last_k != 0

                self.current_lut[lut_size] = last_k
                print(f"Found auto lut %06X" % last_k)

                index = self.lut_models[lut_size].index(row, 0)
                self.lut_view.setCurrentIndex(index)

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