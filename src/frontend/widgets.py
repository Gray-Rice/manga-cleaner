import os
import PySide6.QtSvg 
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFrame, QSlider, QHBoxLayout,
                             QStyledItemDelegate, QGridLayout, QComboBox, QDialog)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QIcon
from src.utils.config import Config
from src.utils.paths import Paths

#/////////////////////////////////#
#    STUDIO COMPONENT LIBRARY     #
#/////////////////////////////////#

class FileListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icons = {}

    def _get_icon(self, state_name: str) -> QIcon:
        """Caches and returns the SVG icon for the given state"""
        if state_name not in self.icons:
            icon_path = os.path.join(Paths.BUNDLE_DIR, "assets", f"icon_{state_name}.svg")
            if os.path.exists(icon_path):
                self.icons[state_name] = QIcon(icon_path)
            else:
                self.icons[state_name] = QIcon() 
        return self.icons[state_name]

    def paint(self, painter, option, index):
        # 1. Paint standard background, highlight, checkbox, and text
        super().paint(painter, option, index)
        
        # 2. Extract our custom status and lock flags
        state_name = index.data(Qt.UserRole + 1)
        is_locked = index.data(Qt.UserRole + 2)
        
        icon_size = 18
        offset_x = 4  # Starting right-margin
        
        # 3. Draw the Status Icon (Far Right)
        if state_name:
            icon = self._get_icon(state_name)
            if not icon.isNull():
                x = option.rect.right() - icon_size - offset_x
                y = option.rect.top() + (option.rect.height() - icon_size) // 2
                rect = QRect(x, y, icon_size, icon_size)
                icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)
                offset_x += icon_size + 4  # Shift cursor left for the next icon
                
        # 4. Draw the Lock Icon (To the left of the status icon)
        if is_locked:
            lock_icon = self._get_icon("lock")
            if not lock_icon.isNull():
                x = option.rect.right() - icon_size - offset_x
                y = option.rect.top() + (option.rect.height() - icon_size) // 2
                rect = QRect(x, y, icon_size, icon_size)
                lock_icon.paint(painter, rect, Qt.AlignCenter, QIcon.Normal, QIcon.On)

class FileListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background: {Config.COLOR_PANEL}; border: none;")
        self.setItemDelegate(FileListDelegate(self))

    def add_file(self, full_path: str):
        item = QListWidgetItem(os.path.basename(full_path))
        item.setData(Qt.UserRole, full_path)
        item.setData(Qt.UserRole + 1, "unmodified")  
        item.setData(Qt.UserRole + 2, False) # Initial lock state
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Unchecked)
        self.addItem(item)

    def update_item_state(self, full_path: str, state_name: str):
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == full_path:
                item.setData(Qt.UserRole + 1, state_name)
                break

class ToolGroup(QFrame):
    def __init__(self, title, button_configs):
        super().__init__()
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(5, 5, 5, 5)
        main_lay.setSpacing(4)
        
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 9px; font-weight: bold;")
        main_lay.addWidget(lbl)
        
        grid_lay = QGridLayout()
        grid_lay.setSpacing(4)
        
        self.buttons = {}
        checkable = ["MOVE", "BRUSH", "ERASER", "RECT", "LASSO", "POLY", "BUCKET"]
        
        for i, name in enumerate(button_configs):
            btn = QPushButton(name)
            if name in checkable: 
                btn.setCheckable(True)
                btn.setAutoExclusive(True) 
            self.buttons[name] = btn
            
            # Map index to a 2-column grid (row = index // 2, col = index % 2)
            row = i // 2
            col = i % 2
            grid_lay.addWidget(btn, row, col)
            
        main_lay.addLayout(grid_lay)

class HardwareMonitor(QFrame):
    def __init__(self):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        
        self.lbl = QLabel("SYSTEM IDLE")
        self.lbl.setStyleSheet(f"color: {Config.COLOR_ACCENT}; font-weight: bold; font-size: 10px;")
        
        self.bar = QSlider(Qt.Horizontal)
        self.bar.setRange(0, 100)
        self.bar.setFixedWidth(100)
        self.bar.setEnabled(False)
        
        lay.addWidget(self.lbl)
        lay.addWidget(self.bar)

class LabeledSlider(QWidget):
    def __init__(self, label, default, minimum, maximum, callback=None, is_tile=False, suffix="px"):
        super().__init__()
        self.is_tile = is_tile
        self.suffix = suffix
        self.base_label = label
        lay = QVBoxLayout(self)
        
        self.display = QLabel("")
        self.display.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 10px;")
        
        self.slider = QSlider(Qt.Horizontal)
        if is_tile:
            self.slider.setRange(1, 8) 
            self.slider.setValue(default // 512)
        else:
            self.slider.setRange(minimum, maximum)
            self.slider.setValue(default)
            
        self.slider.valueChanged.connect(self.update_text)
        if callback: self.slider.valueChanged.connect(callback)
            
        lay.addWidget(self.display)
        lay.addWidget(self.slider)
        self.update_text(self.slider.value())

    def update_text(self, val):
        if self.is_tile:
            self.display.setText(f"{self.base_label}: {val * 512}px")
        else:
            self.display.setText(f"{self.base_label}: {val}{self.suffix}")


#/////////////////////////////////#
#    EXPORT DIALOG                #
#/////////////////////////////////#

class ExportDialog(QDialog):
    """Modal dialog for selecting export format and quality/compression settings."""
    
    def __init__(self, parent=None, default_format="jpg", default_jpg_quality=95, default_png_compression=6):
        super().__init__(parent)
        self.setWindowTitle("Export Image")
        self.setFixedWidth(360)
        self.setStyleSheet(f"background: {Config.COLOR_PANEL}; color: {Config.COLOR_TEXT};")
        
        self.selected_format = default_format
        self.selected_quality = default_jpg_quality if default_format == "jpg" else default_png_compression
        self.result = None
        
        self._setup_ui()
        self._update_quality_controls()
        
    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        
        # Format selector
        fmt_lay = QHBoxLayout()
        fmt_lbl = QLabel("FORMAT")
        fmt_lbl.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 10px; font-weight: bold;")
        fmt_lay.addWidget(fmt_lbl)
        fmt_lay.addStretch()
        
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["JPG", "PNG"])
        self.fmt_combo.setCurrentText(self.selected_format.upper())
        self.fmt_combo.currentTextChanged.connect(self._on_format_changed)
        self.fmt_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Config.COLOR_BG};
                border: 1px solid #2a2a32;
                border-radius: 4px;
                padding: 6px 10px;
                color: {Config.COLOR_TEXT};
                font-size: 12px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {Config.COLOR_ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {Config.COLOR_PANEL};
                border: 1px solid #2a2a32;
                selection-background-color: {Config.COLOR_ACCENT};
                color: {Config.COLOR_TEXT};
            }}
        """)
        fmt_lay.addWidget(self.fmt_combo)
        lay.addLayout(fmt_lay)
        
        # Quality/Compression controls container
        self.quality_container = QWidget()
        self.quality_lay = QVBoxLayout(self.quality_container)
        self.quality_lay.setContentsMargins(0, 0, 0, 0)
        self.quality_lay.setSpacing(8)
        lay.addWidget(self.quality_container)
        
        # Buttons
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {Config.COLOR_BG};
                border: 1px solid #2a2a32;
                border-radius: 4px;
                padding: 8px 20px;
                color: {Config.COLOR_TEXT};
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: #25252e;
                color: #ffffff;
            }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(self.btn_cancel)
        
        self.btn_export = QPushButton("EXPORT")
        self.btn_export.setObjectName("PrimaryBtn")
        self.btn_export.setStyleSheet(f"""
            #PrimaryBtn {{
                background-color: {Config.COLOR_ACCENT};
                color: #000000;
                border: none;
                font-size: 12px;
                padding: 8px 24px;
                border-radius: 4px;
            }}
            #PrimaryBtn:hover {{
                background-color: #33e0ff;
            }}
        """)
        self.btn_export.clicked.connect(self.accept)
        btn_lay.addWidget(self.btn_export)
        
        lay.addLayout(btn_lay)
        
    def _on_format_changed(self, text):
        self.selected_format = text.lower()
        self._update_quality_controls()
        
    def _update_quality_controls(self):
        # Clear existing controls
        while self.quality_lay.count():
            item = self.quality_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.selected_format == "jpg":
            # JPG Quality slider (1-100)
            lbl = QLabel("QUALITY")
            lbl.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 10px; font-weight: bold;")
            self.quality_lay.addWidget(lbl)
            
            self.quality_slider = QSlider(Qt.Horizontal)
            self.quality_slider.setRange(1, 100)
            self.quality_slider.setValue(self.selected_quality)
            self.quality_slider.valueChanged.connect(self._on_quality_changed)
            self.quality_slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    border: 1px solid #2a2a32;
                    height: 4px;
                    background: {Config.COLOR_BG};
                    margin: 2px 0;
                }}
                QSlider::handle:horizontal {{
                    background: {Config.COLOR_ACCENT};
                    border: 1px solid {Config.COLOR_ACCENT};
                    width: 14px;
                    height: 14px;
                    margin: -6px 0;
                    border-radius: 7px;
                }}
            """)
            self.quality_lay.addWidget(self.quality_slider)
            
            self.quality_value_lbl = QLabel(f"Quality: {self.selected_quality}% (Higher = better quality, larger file)")
            self.quality_value_lbl.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 10px;")
            self.quality_lay.addWidget(self.quality_value_lbl)
            
        else:  # PNG
            # PNG Compression slider (0-9)
            lbl = QLabel("COMPRESSION")
            lbl.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 10px; font-weight: bold;")
            self.quality_lay.addWidget(lbl)
            
            self.quality_slider = QSlider(Qt.Horizontal)
            self.quality_slider.setRange(0, 9)
            self.quality_slider.setValue(self.selected_quality)
            self.quality_slider.valueChanged.connect(self._on_quality_changed)
            self.quality_slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    border: 1px solid #2a2a32;
                    height: 4px;
                    background: {Config.COLOR_BG};
                    margin: 2px 0;
                }}
                QSlider::handle:horizontal {{
                    background: {Config.COLOR_ACCENT};
                    border: 1px solid {Config.COLOR_ACCENT};
                    width: 14px;
                    height: 14px;
                    margin: -6px 0;
                    border-radius: 7px;
                }}
            """)
            self.quality_lay.addWidget(self.quality_slider)
            
            self.quality_value_lbl = QLabel(f"Compression: {self.selected_quality} (Higher = smaller file, slower save)")
            self.quality_value_lbl.setStyleSheet(f"color: {Config.COLOR_TEXT_DIM}; font-size: 10px;")
            self.quality_lay.addWidget(self.quality_value_lbl)
            
    def _on_quality_changed(self, value):
        self.selected_quality = value
        if self.selected_format == "jpg":
            self.quality_value_lbl.setText(f"Quality: {value}% (Higher = better quality, larger file)")
        else:
            self.quality_value_lbl.setText(f"Compression: {value} (Higher = smaller file, slower save)")
            
    def accept(self):
        self.result = (self.selected_format, self.selected_quality)
        super().accept()
        
    def reject(self):
        self.result = None
        super().reject()
