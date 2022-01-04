import sys
import threading

from PySide6.QtCore import QRect, Qt, QPoint, QSortFilterProxyModel, QSize, QEvent, QTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem, QImage, QPainter, QPixmap, QColor, QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget, \
    QListView, QComboBox, QTabWidget, QTreeView, QToolButton, QStyle, QStackedWidget

from blastimation.anim import Animation
from blastimation.comp import Composite
from blastimation.image import BlastImage
from blastimation.rom import Rom, CompType
from blastimation.blast import Blast, blast_get_lut_size


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blastimation")
        self.resize(960, 1080)

        self.blast_filter_types = [
            None,
            Blast.BLAST1_RGBA16,
            Blast.BLAST2_RGBA32,
            Blast.BLAST3_IA8,
            Blast.BLAST4_IA16,
            Blast.BLAST5_RGBA32,
            Blast.BLAST6_IA8,
        ]

        self.initialized = False

        self.lut_models = {}

        self.rom = None
        self.image = None
        self.animation = None
        self.animation_timer: QTimer = QTimer()
        self.animation_timer.setInterval(100)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_frame: int = 0

        self.single_model = self.make_single_model()
        self.composite_model = self.make_composite_model()
        self.animation_model = self.make_animation_model()

        self.list_toggle_button_states = [
            (self.style().standardIcon(QStyle.SP_FileDialogListView), "Grid view"),
            (self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "List view")
        ]

        # Global widgets
        self.image_label = QLabel()
        self.lut_combo_box = QComboBox()
        self.single_view = QTreeView()
        self.single_view.sortByColumn(0, Qt.AscendingOrder)
        self.lut_auto_button = QPushButton("Guess LUT", self)

        self.single_icon_view = QListView()
        self.single_proxy_model = QSortFilterProxyModel()
        self.single_stack_widget = QStackedWidget()
        self.composite_view = QTreeView()
        self.composite_proxy_model = QSortFilterProxyModel()
        self.list_toggle_button = QToolButton()

        self.animation_view = QTreeView()
        self.animation_proxy_model = QSortFilterProxyModel()

        self.init_widgets()

    def animate(self):
        frame_addr = self.animation.addresses[self.animation_frame]
        self.image = self.rom.images[frame_addr]
        self.update_image_label()

        self.animation_frame += 1
        if self.animation_frame >= self.animation.frames():
            self.animation_frame = 0

    @staticmethod
    def make_single_model():
        m = QStandardItemModel(0, 8)
        m.setHeaderData(0, Qt.Horizontal, "Start")
        m.setHeaderData(1, Qt.Horizontal, "Name")
        m.setHeaderData(2, Qt.Horizontal, "Encoding")
        m.setHeaderData(3, Qt.Horizontal, "Format")
        m.setHeaderData(4, Qt.Horizontal, "Width")
        m.setHeaderData(5, Qt.Horizontal, "Height")
        m.setHeaderData(6, Qt.Horizontal, "Size Enc")
        m.setHeaderData(7, Qt.Horizontal, "Size Dec")
        return m

    @staticmethod
    def make_animation_model():
        m = QStandardItemModel(0, 9)
        m.setHeaderData(0, Qt.Horizontal, "Start")
        m.setHeaderData(1, Qt.Horizontal, "Name")
        m.setHeaderData(2, Qt.Horizontal, "Encoding")
        m.setHeaderData(3, Qt.Horizontal, "Format")
        m.setHeaderData(4, Qt.Horizontal, "Width")
        m.setHeaderData(5, Qt.Horizontal, "Height")
        m.setHeaderData(6, Qt.Horizontal, "Size Enc")
        m.setHeaderData(7, Qt.Horizontal, "Size Dec")
        m.setHeaderData(8, Qt.Horizontal, "Frames")
        return m

    def populate_single_model(self):
        for addr, image in self.rom.images.items():
            match image.blast:
                case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                    lut_size = blast_get_lut_size(image.blast)
                    lut = self.rom.luts[lut_size][image.lut]
                    image.decode_lut(lut)
                case _:
                    image.decode()

            last_row = self.single_model.rowCount()
            self.single_model.insertRow(last_row)
            items = image.model_data()
            for i in range(len(items)):
                self.single_model.setData(self.single_model.index(last_row, i), items[i])

            # Update icon
            icon = QIcon(image.pixmap.scaled(
                QSize(128, 128),
                Qt.KeepAspectRatio,
                Qt.FastTransformation,
            ))
            self.single_model.item(last_row).setIcon(icon)

    @staticmethod
    def make_composite_model():
        m = QStandardItemModel(0, 9)
        m.setHeaderData(0, Qt.Horizontal, "Start")
        m.setHeaderData(1, Qt.Horizontal, "Name")
        m.setHeaderData(2, Qt.Horizontal, "Encoding")
        m.setHeaderData(3, Qt.Horizontal, "Format")
        m.setHeaderData(4, Qt.Horizontal, "Width")
        m.setHeaderData(5, Qt.Horizontal, "Height")
        m.setHeaderData(6, Qt.Horizontal, "Size Enc")
        m.setHeaderData(7, Qt.Horizontal, "Size Dec")
        m.setHeaderData(8, Qt.Horizontal, "Comp")
        return m

    def populate_comp_model(self):
        for addr, comp in self.rom.comps.items():
            last_row = self.composite_model.rowCount()
            self.composite_model.insertRow(last_row)

            items = comp.model_data(self.rom.images)
            for i in range(len(items)):
                self.composite_model.setData(self.composite_model.index(last_row, i), items[i])

    def populate_animation_model(self):
        for addr, animation in self.rom.animations.items():
            last_row = self.animation_model.rowCount()
            self.animation_model.insertRow(last_row)

            items = animation.model_data(self.rom.images)
            for i in range(len(items)):
                self.animation_model.setData(self.animation_model.index(last_row, i), items[i])

    def init_luts(self):
        for lut_size in [128, 256]:
            self.lut_models[lut_size] = QStandardItemModel(0, 1)
            for k in self.rom.luts[lut_size].keys():
                self.lut_models[lut_size].appendRow(QStandardItem("%06X" % k))

    def init_widgets(self):
        self.single_proxy_model.setDynamicSortFilter(True)
        self.single_proxy_model.setSourceModel(self.single_model)
        self.single_proxy_model.setFilterKeyColumn(2)

        self.composite_proxy_model.setDynamicSortFilter(True)
        self.composite_proxy_model.setSourceModel(self.composite_model)
        self.composite_proxy_model.setFilterKeyColumn(2)

        self.animation_proxy_model.setDynamicSortFilter(True)
        self.animation_proxy_model.setSourceModel(self.animation_model)
        self.animation_proxy_model.setFilterKeyColumn(2)

        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)
        screen_geometry: QRect = self.screen().geometry()
        self.image_label.setMinimumSize(
            screen_geometry.width() / 8, screen_geometry.height() / 8
        )

        main_layout = QVBoxLayout(self)

        self.list_toggle_button.setIcon(self.list_toggle_button_states[0][0])
        self.list_toggle_button.setToolTip(self.list_toggle_button_states[0][1])
        self.list_toggle_button.clicked.connect(self.on_toggle_list_mode)

        menu_buttons = QHBoxLayout()

        main_layout.addWidget(self.image_label)
        main_layout.addLayout(menu_buttons)

        blast_type_names = ["All"]
        for t in self.blast_filter_types:
            if t:
                blast_type_names.append(t.name)

        blast_filter_box = QComboBox()
        blast_filter_box.addItems(blast_type_names)
        blast_filter_box.setCurrentIndex(0)
        blast_filter_box.currentIndexChanged.connect(self.on_blast_filter_changed)
        blast_filter_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.single_view.setRootIsDecorated(False)
        self.single_view.setAlternatingRowColors(True)
        self.single_view.setModel(self.single_proxy_model)
        self.single_view.selectionModel().currentChanged.connect(self.on_single_select)
        self.single_view.setSortingEnabled(True)

        self.single_icon_view.setViewMode(QListView.IconMode)
        self.single_icon_view.setMovement(QListView.Static)
        self.single_icon_view.setIconSize(QSize(128, 128))
        self.single_icon_view.setModel(self.single_proxy_model)
        self.single_icon_view.selectionModel().currentChanged.connect(self.on_single_select)

        self.composite_view.setRootIsDecorated(False)
        self.composite_view.setAlternatingRowColors(True)
        self.composite_view.setModel(self.composite_proxy_model)
        self.composite_view.selectionModel().currentChanged.connect(self.on_composite_select)
        self.composite_view.setSortingEnabled(True)

        self.animation_view.setRootIsDecorated(False)
        self.animation_view.setAlternatingRowColors(True)
        self.animation_view.setModel(self.animation_proxy_model)
        self.animation_view.selectionModel().currentChanged.connect(self.on_animation_select)
        self.animation_view.setSortingEnabled(True)

        tab_widget = QTabWidget()
        tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.single_stack_widget.addWidget(self.single_view)
        self.single_stack_widget.addWidget(self.single_icon_view)

        tab_widget.addTab(self.single_stack_widget, "Single")
        tab_widget.addTab(self.composite_view, "Multi")
        tab_widget.addTab(self.animation_view, "Anim")

        self.lut_auto_button.clicked.connect(self.on_auto_lut)
        self.lut_auto_button.hide()
        self.lut_combo_box.currentIndexChanged.connect(self.on_lut_select)
        self.lut_combo_box.hide()

        menu_buttons.addWidget(blast_filter_box)
        menu_buttons.addWidget(self.lut_combo_box)
        menu_buttons.addWidget(self.lut_auto_button)
        menu_buttons.addWidget(self.list_toggle_button)

        main_layout.addWidget(tab_widget)

    def on_toggle_list_mode(self):
        if self.single_stack_widget.currentIndex() == 0:
            # List is active, make grid
            new_index = 1
        else:
            # Grid is active, make list
            new_index = 0
        self.single_stack_widget.setCurrentIndex(new_index)
        self.list_toggle_button.setIcon(self.list_toggle_button_states[new_index][0])
        self.list_toggle_button.setToolTip(self.list_toggle_button_states[new_index][1])

    def on_single_select(self, model_index):
        self.animation = None
        self.animation_timer.stop()

        addr_i = self.single_proxy_model.index(model_index.row(), 0)
        addr_str = self.single_proxy_model.data(addr_i)
        if not addr_str:
            return
        addr = int(addr_str, 16)

        self.image = self.rom.images[addr]
        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.image.blast)
                lut = self.rom.luts[lut_size][self.image.lut]
                self.image.decode_lut(lut)
            case _:
                self.image.decode()

        self.update_image_label()

        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.image.blast)
                self.lut_combo_box.setModel(self.lut_models[lut_size])
                self.lut_combo_box.show()
                self.lut_auto_button.show()
                lut_index = list(self.rom.luts[lut_size].keys()).index(self.image.lut)
                self.lut_combo_box.setCurrentIndex(lut_index)
            case _:
                self.lut_combo_box.hide()
                self.lut_auto_button.hide()

    def on_composite_select(self, model_index):
        self.animation = None
        self.animation_timer.stop()

        addr_i = self.composite_proxy_model.index(model_index.row(), 0)
        address = int(self.composite_proxy_model.data(addr_i), 16)

        c: Composite = self.rom.comps[address]

        images = []
        for addr in c.addresses:
            i = self.rom.images[addr]
            i.decode()
            images.append(i)

        match c.type:
            case CompType.TopBottom:
                width = images[0].width
                height = images[0].height * 2
            case CompType.RightLeft:
                width = images[0].width * 2
                height = images[0].height
            case CompType.Quad:
                width = images[0].width * 2
                height = images[0].height * 2
            case _:
                width = 0
                height = 0

        composite_image = QImage(width, height, QImage.Format_ARGB32)
        composite_image.fill(QColor(0, 0, 0, 0))

        painter = QPainter(composite_image)

        match c.type:
            case CompType.TopBottom:
                painter.drawImage(QPoint(0, 0), images[1].qimage)
                painter.drawImage(QPoint(0, height/2), images[0].qimage)
            case CompType.RightLeft:
                painter.drawImage(QPoint(0, 0), images[1].qimage)
                painter.drawImage(QPoint(width / 2, 0), images[0].qimage)
            case CompType.Quad:
                painter.drawImage(QPoint(0, 0), images[2].qimage)
                painter.drawImage(QPoint(width / 2, 0), images[3].qimage)
                painter.drawImage(QPoint(0, height / 2), images[0].qimage)
                painter.drawImage(QPoint(width / 2, height / 2), images[1].qimage)

        painter.end()

        self.image = BlastImage(c.blast, address, None, width, height)
        self.image.pixmap = QPixmap.fromImage(composite_image)
        self.update_image_label()

    def on_animation_select(self, model_index):
        addr_i = self.animation_proxy_model.index(model_index.row(), 0)
        address = int(self.animation_proxy_model.data(addr_i), 16)

        a: Animation = self.rom.animations[address]
        self.animation = a

        images = []
        for addr in a.addresses:
            i = self.rom.images[addr]
            i.decode()
            images.append(i)

        self.image = images[0]
        self.update_image_label()

        self.animation_frame = 0

        self.animation_timer.start()

    def on_lut_select(self, index):
        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.image.blast)
                self.image.lut = int(self.lut_models[lut_size].item(index).text(), 16)
                lut = self.rom.luts[lut_size][self.image.lut]
                self.image.decode_lut(lut)
                self.update_image_label()

    def on_blast_filter_changed(self, index):
        blast_type = self.blast_filter_types[index]
        if not blast_type:
            self.single_proxy_model.setFilterFixedString("")
            self.composite_proxy_model.setFilterFixedString("")
            return

        self.single_proxy_model.setFilterFixedString(blast_type.name)
        self.composite_proxy_model.setFilterFixedString(blast_type.name)

    def on_auto_lut(self):
        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.image.blast)

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

                self.image.lut = last_k
                print(f"Found auto lut %06X" % last_k)
                self.lut_combo_box.setCurrentIndex(row)

    def resizeEvent(self, event):
        if not self.image:
            return
        scaled_size = self.image.pixmap.size()
        scaled_size.scale(self.image_label.size(), Qt.KeepAspectRatio)
        if scaled_size != self.image_label.pixmap().size():
            self.update_image_label()

    def post_initialize(self):
        self.rom = Rom(sys.argv[1])
        self.init_luts()
        self.image = list(self.rom.images.values())[0]
        self.image.decode()
        self.update_image_label()
        self.populate_single_model()
        self.populate_comp_model()
        self.populate_animation_model()
        self.initialized = True

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange and not self.initialized:
            t = threading.Thread(target=self.post_initialize)
            t.start()

    def update_image_label(self):
        self.image_label.setPixmap(
            self.image.pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.FastTransformation,
            )
        )
