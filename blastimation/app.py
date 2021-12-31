import sys

from PySide6.QtCore import QRect, Qt, QPoint, QSortFilterProxyModel, QSize, QEvent
from PySide6.QtGui import QStandardItemModel, QStandardItem, QImage, QPainter, QPixmap, QColor, QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget, \
    QListView, QAbstractItemView, QComboBox, QTabWidget, QTreeView, QToolButton, QStyle, QSpacerItem, QStackedLayout, \
    QStackedWidget

from blastimation.comp import Composite
from blastimation.image import BlastImage
from blastimation.rom import Rom, CompType
from blastimation.blast import Blast, blast_get_lut_size, blast_get_format_id


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blastimation")
        self.resize(960, 1080)

        self.current_lut = {
            128: 0x047480,
            256: 0x152970
        }

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

        self.single_model = self.make_single_model()
        self.composite_model = self.make_composite_model()

        self.list_toggle_button_states = [
            (self.style().standardIcon(QStyle.SP_FileDialogListView), "Grid view"),
            (self.style().standardIcon(QStyle.SP_FileDialogDetailedView), "List view")
        ]

        # Global widgets
        self.image_label = QLabel()
        self.lut_view = QListView()
        self.lut_widget = QWidget()
        self.single_view = QTreeView()
        self.single_icon_view = QListView()
        self.single_proxy_model = QSortFilterProxyModel()
        self.single_stack_widget = QStackedWidget()
        self.composite_view = QTreeView()
        self.composite_proxy_model = QSortFilterProxyModel()
        self.list_toggle_button = QToolButton()

        self.init_widgets()

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

    def populate_single_model(self):
        for addr, image in self.rom.images.items():
            match image.blast:
                case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                    lut_size = blast_get_lut_size(image.blast)
                    lut = self.rom.luts[lut_size][self.current_lut[lut_size]]
                    image.decode_lut(lut)
                case _:
                    image.decode()

            self.single_model.insertRow(0)
            items = image.model_data()
            for i in range(len(items)):
                self.single_model.setData(self.single_model.index(0, i), items[i])

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
            self.composite_model.insertRow(0)

            items = comp.model_data(self.rom.images)
            for i in range(len(items)):
                self.composite_model.setData(self.composite_model.index(0, i), items[i])

    def init_luts(self):
        for lut_size in self.current_lut.keys():
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
        menu_buttons.addStretch()
        menu_buttons.addWidget(self.list_toggle_button)

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

        self.single_view.setRootIsDecorated(False)
        self.single_view.setAlternatingRowColors(True)
        self.single_view.setModel(self.single_proxy_model)
        self.single_view.selectionModel().currentChanged.connect(self.on_single_select)
        self.single_view.setSortingEnabled(True)

        self.single_icon_view.setViewMode(QListView.IconMode)
        self.single_icon_view.setMovement(QListView.Static)
        self.single_icon_view.setIconSize(QSize(100, 100))
        self.single_icon_view.setModel(self.single_proxy_model)

        self.composite_view.setRootIsDecorated(False)
        self.composite_view.setAlternatingRowColors(True)
        self.composite_view.setModel(self.composite_proxy_model)
        self.composite_view.selectionModel().currentChanged.connect(self.on_composite_select)
        self.composite_view.setSortingEnabled(True)

        blast_list_layout = QVBoxLayout()
        blast_list_layout.addWidget(blast_filter_box)

        tab_widget = QTabWidget()
        tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.single_stack_widget.addWidget(self.single_view)
        self.single_stack_widget.addWidget(self.single_icon_view)

        tab_widget.addTab(self.single_stack_widget, "Single")
        tab_widget.addTab(self.composite_view, "Multi")
        blast_list_layout.addWidget(tab_widget)

        self.lut_view.setObjectName("lutView")
        self.lut_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        lut_auto_button = QPushButton("Select closest", self)
        lut_auto_button.clicked.connect(self.on_auto_lut)

        self.lut_widget.hide()
        lut_layout = QVBoxLayout(self.lut_widget)
        lut_layout.addWidget(self.lut_view)
        lut_layout.addWidget(lut_auto_button)

        lists_layout = QHBoxLayout()
        lists_layout.addLayout(blast_list_layout)
        lists_layout.addWidget(self.lut_widget)

        main_layout.addLayout(lists_layout)

    def on_toggle_list_mode(self):
        if self.single_stack_widget.currentIndex() == 0:
            # List is active, make grid
            self.single_stack_widget.setCurrentIndex(1)
            self.list_toggle_button.setIcon(self.list_toggle_button_states[1][0])
            self.list_toggle_button.setToolTip(self.list_toggle_button_states[1][1])

        else:
            # Grid is active, make list
            self.single_stack_widget.setCurrentIndex(0)
            self.list_toggle_button.setIcon(self.list_toggle_button_states[0][0])
            self.list_toggle_button.setToolTip(self.list_toggle_button_states[0][1])

    def on_single_select(self, model_index):
        addr_i = self.single_proxy_model.index(model_index.row(), 0)
        addr = int(self.single_proxy_model.data(addr_i), 16)

        self.image = self.rom.images[addr]
        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.image.blast)
                lut = self.rom.luts[lut_size][self.current_lut[lut_size]]
                self.image.decode_lut(lut)
            case _:
                self.image.decode()

        self.update_image_label()

    def on_composite_select(self, model_index):
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

    def on_lut_select(self, model_index):
        lut_addr = int(model_index.data(), 16)

        match self.image.blast:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(self.image.blast)
                self.current_lut[lut_size] = lut_addr
                lut = self.rom.luts[lut_size][self.current_lut[lut_size]]
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

        match blast_type:
            case (Blast.BLAST4_IA16 | Blast.BLAST5_RGBA32):
                lut_size = blast_get_lut_size(blast_type)
                self.lut_view.setModel(self.lut_models[lut_size])
                self.lut_view.selectionModel().currentChanged.connect(self.on_lut_select)
                self.lut_widget.show()
            case _:
                self.lut_widget.hide()
                self.lut_view.setModel(None)

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

                self.current_lut[lut_size] = last_k
                print(f"Found auto lut %06X" % last_k)

                index = self.lut_models[lut_size].index(row, 0)
                self.lut_view.setCurrentIndex(index)

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
        self.initialized = True

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange and not self.initialized:
            self.post_initialize()

    def update_image_label(self):
        self.image_label.setPixmap(
            self.image.pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.FastTransformation,
            )
        )
