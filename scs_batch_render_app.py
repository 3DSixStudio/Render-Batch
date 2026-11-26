# -*- coding: utf-8 -*-
"""
SCS Batch Render - Desktop app (PySide6)
Batch renders Scs_N / Icon_N collections by running Blender in background mode.
Created by Hari  |  https://github.com/3DSixStudio/Render-Batch
"""

import os
import re
import sys
import json
import time
import tempfile
import subprocess

from PySide6.QtCore import (Qt, QThread, Signal, QProcess, QProcessEnvironment, QTimer, QUrl,
                            QRectF, QSize, QByteArray)
from PySide6.QtGui import (QPixmap, QDesktopServices, QColor, QBrush, QIcon, QPainter, QPen,
                           QConicalGradient, QFont, QImage)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QCheckBox, QRadioButton, QButtonGroup,
    QSpinBox, QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QProgressBar, QMessageBox,
    QHeaderView, QSizePolicy, QFrame, QGraphicsDropShadowEffect, QScrollArea, QStackedWidget,
)

import blender_finder
import updater

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_SCRIPT = os.path.join(APP_DIR, "scs_render_core.py")
APP_NAME = "SCS Batch Render"
APP_AUTHOR = "Hari"
DEFAULT_RES = {"Scs": (2796, 2048), "Icon": (2048, 2048)}


def read_version():
    try:
        with open(os.path.join(APP_DIR, "version.txt"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return "?"


APP_VERSION = read_version()

SETTINGS_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "SCS_Batch_Render")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
BG = "#f4f5fa"
CARD = "#ffffff"
TEXT = "#1f2333"
SUB = "#8b90a5"
BORDER = "#eceef5"
PURPLE = "#7c5cff"
ORANGE = "#ff9f43"
BLUE = "#4c8dff"
GREEN = "#22c08a"
RED = "#ff5b6e"
PINK = "#ff6fa5"

C_RENDERING = QColor(ORANGE)
C_DONE = QColor(GREEN)
C_ERROR = QColor(RED)
C_DIM = QColor("#b4b8c8")
C_ON = QColor(TEXT)
C_PART = QColor(PURPLE)
C_NORMAL = QColor(TEXT)

STYLE = """
* { font-family:'Segoe UI', 'Inter', sans-serif; font-size:10pt; color:#1f2333; }
QMainWindow, QWidget#root, QDialog { background:#f4f5fa; }
QToolTip { background:#1f2333; color:#ffffff; border:none; padding:4px 8px; }

/* sidebar */
QFrame#sidebar { background:#ffffff; border-right:1px solid #eceef5; }
QLabel#brand { font-size:12.5pt; font-weight:800; color:#1f2333; }
QLabel#brandSub { color:#8b90a5; font-size:8.5pt; }
QLabel#section { color:#8b90a5; font-size:8.5pt; font-weight:bold; letter-spacing:1px; }
QPushButton#nav { background:transparent; border:none; border-radius:10px; text-align:left;
    padding:9px 12px; color:#6b7086; font-weight:600; }
QPushButton#nav:hover { background:#f6f4ff; color:#1f2333; }
QPushButton#nav:checked { background:#f1edff; color:#7c5cff; }
QFrame#recentRow { background:transparent; border-radius:8px; }
QFrame#recentRow:hover { background:#f6f7fb; }
QLabel#recentName { font-weight:600; font-size:9pt; }
QLabel#recentSub { color:#8b90a5; font-size:8pt; }
QFrame#profile { background:#f7f8fc; border-radius:12px; }
QLabel#avatarBig { background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c5cff, stop:1 #ff9f43);
    color:#ffffff; font-weight:800; font-size:12pt; border-radius:18px; }

/* top bar */
QLineEdit#search { background:#ffffff; border:1px solid #eceef5; border-radius:10px; padding:8px 10px; }
QLineEdit#search:focus { border-color:#7c5cff; }
QPushButton#iconBtn { background:#ffffff; border:1px solid #eceef5; border-radius:10px; padding:6px; }
QPushButton#iconBtn:hover { border-color:#7c5cff; }
QPushButton#avatar { background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #7c5cff, stop:1 #ff9f43);
    color:#ffffff; font-weight:800; border:none; border-radius:17px; }
QLabel#dot { background:#ff5b6e; border-radius:4px; }

/* headings */
QLabel#h1 { font-size:16pt; font-weight:800; }
QLabel#h2 { font-size:11.5pt; font-weight:800; }
QLabel#sub { color:#8b90a5; }
QLabel#chip { background:#ffffff; border:1px solid #eceef5; border-radius:9px; padding:5px 12px; color:#6b7086; }

/* cards */
QFrame#card { background:#ffffff; border-radius:16px; }
QFrame#stat { border-radius:14px; }
QLabel#statValue { font-size:20pt; font-weight:800; }
QLabel#statTitle { font-size:9pt; font-weight:700; }
QLabel#statSub { font-size:8pt; color:#8b90a5; }
QLabel#nowTitle { font-size:13pt; font-weight:800; }
QLabel#thumb { background:#f4f5fa; border:1px dashed #dfe2ec; border-radius:12px; color:#b4b8c8; }
QLabel#fieldLabel { color:#6b7086; font-weight:600; }

/* inputs */
QLineEdit, QComboBox, QSpinBox { background:#f7f8fc; border:1px solid #eceef5; border-radius:8px;
    padding:6px 8px; selection-background-color:#7c5cff; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color:#7c5cff; background:#ffffff; }
QComboBox::drop-down { border:none; width:22px; }
QComboBox QAbstractItemView { background:#ffffff; border:1px solid #eceef5; selection-background-color:#f1edff;
    selection-color:#1f2333; outline:none; }
QSpinBox::up-button, QSpinBox::down-button { width:16px; border:none; background:transparent; }

/* buttons */
QPushButton { background:#ffffff; border:1px solid #e3e5ee; border-radius:8px; padding:6px 14px; font-weight:600; }
QPushButton:hover { border-color:#7c5cff; color:#7c5cff; }
QPushButton:pressed { background:#f1edff; }
QPushButton:disabled { color:#b4b8c8; border-color:#eceef5; background:#fafbfd; }
QPushButton#primary { background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #9b7bff);
    color:#ffffff; border:none; padding:10px 22px; font-size:10.5pt; font-weight:800; border-radius:10px; }
QPushButton#primary:hover { background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #6a48ff, stop:1 #8a66ff); color:#ffffff; }
QPushButton#primary:disabled { background:#d9d2ff; color:#ffffff; }
QPushButton#danger { background:#fff0f2; color:#ff5b6e; border:1px solid #ffd0d6; padding:10px 22px;
    font-size:10.5pt; font-weight:800; border-radius:10px; }
QPushButton#danger:hover { background:#ff5b6e; color:#ffffff; }
QPushButton#danger:disabled { background:#fafbfd; color:#d0d3de; border-color:#eceef5; }
QPushButton#link { background:transparent; border:none; color:#8b90a5; padding:2px 4px; font-weight:600; }
QPushButton#link:hover { color:#7c5cff; }
QLabel#cfg { background:#f7f8fc; border:1px solid #eceef5; border-radius:8px; padding:7px 10px; color:#6b7086; }
QLabel#cfg:hover { border-color:#7c5cff; color:#7c5cff; }
QPushButton#pill { background:#f7f8fc; border:1px solid #eceef5; border-radius:14px; padding:4px 12px; font-size:9pt; }
QPushButton#pill:hover { background:#f1edff; color:#7c5cff; border-color:#d9d0ff; }

/* tree / log */
QTreeWidget { background:#ffffff; border:none; alternate-background-color:#fafbfe; outline:none; }
QTreeWidget::item { padding:4px 2px; border:none; }
QTreeWidget::item:selected { background:#f1edff; color:#1f2333; }
QHeaderView::section { background:#ffffff; border:none; border-bottom:1px solid #eceef5; padding:6px 4px;
    color:#8b90a5; font-weight:700; font-size:9pt; }
QPlainTextEdit#log { background:#fafbfe; border:1px solid #eceef5; border-radius:10px;
    font-family:Consolas,'Cascadia Mono','Courier New'; font-size:9pt; color:#3d4255; }

QProgressBar { background:#eef0f6; border:none; border-radius:4px; height:8px; text-align:center;
    font-size:8pt; color:transparent; }
QProgressBar::chunk { border-radius:4px; background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7c5cff, stop:1 #ff9f43); }

QScrollBar:vertical { background:transparent; width:10px; margin:2px; }
QScrollBar::handle:vertical { background:#dfe2ec; border-radius:4px; min-height:30px; }
QScrollBar::handle:vertical:hover { background:#c9ccd6; }
QScrollBar:horizontal { background:transparent; height:10px; margin:2px; }
QScrollBar::handle:horizontal { background:#dfe2ec; border-radius:4px; min-width:30px; }
QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; }

/* check boxes / radios */
QCheckBox, QRadioButton { spacing:8px; font-weight:600; }
QCheckBox::indicator, QTreeView::indicator { width:16px; height:16px; border:2px solid #c9ccd6;
    border-radius:5px; background:#ffffff; }
QCheckBox::indicator:hover, QTreeView::indicator:hover { border-color:#7c5cff; }
QCheckBox::indicator:checked, QTreeView::indicator:checked { border-color:#7c5cff; background:#7c5cff;
    image:url(@UI@/check.svg); }
QCheckBox::indicator:indeterminate, QTreeView::indicator:indeterminate { border-color:#7c5cff;
    background:#a995ff; image:url(@UI@/partial.svg); }
QRadioButton#mode { background:#f7f8fc; border:1px solid #eceef5; border-radius:9px; padding:6px 12px; }
QRadioButton#mode:checked { background:#f1edff; border-color:#7c5cff; color:#7c5cff; }
QRadioButton#mode::indicator { width:0px; height:0px; border:none; background:transparent; image:none; }

/* dialog */
QFrame#dlgCard { background:#ffffff; border-radius:14px; }
QLabel#author { font-size:15pt; font-weight:800; color:#7c5cff; }
"""

# Simple line icons (24x24, stroke = COLOR)
ICON_SVG = {
    "dashboard": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/>'
                 '<rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "scan": '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/>'
            '<path d="M8 12h8"/>',
    "log": '<path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/>'
           '<circle cx="4" cy="18" r="1"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1'
                'a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3'
                'l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0'
                ' 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3'
                'a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0'
                '-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/>'
             '<path d="M21 15l-5-5L5 21"/>',
    "play": '<path d="M7 4l13 8-13 8z"/>',
    "stop": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    "update": '<path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>',
}


def make_icon(name, color=SUB, size=20):
    body = ICON_SVG.get(name, "")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>')
    pm = QPixmap()
    pm.loadFromData(QByteArray(svg.encode("utf-8")), "SVG")
    if not pm.isNull() and pm.width() != size * 2:
        pm = pm.scaled(size * 2, size * 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return QIcon(pm)


def build_style():
    ui_dir = os.path.join(APP_DIR, "ui").replace("\\", "/")
    return STYLE.replace("@UI@", ui_dir)


def human_time(sec):
    sec = int(max(0, sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data):
    try:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def kill_tree(pid):
    if not pid:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                       capture_output=True, creationflags=0x08000000)
    else:
        try:
            os.kill(pid, 9)
        except Exception:
            pass


def shadow(widget, blur=28, alpha=22, dy=6):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    eff.setColor(QColor(40, 45, 80, alpha))
    widget.setGraphicsEffect(eff)


# ---------------------------------------------------------------------------
# Custom widgets
# ---------------------------------------------------------------------------
class Card(QFrame):
    """White rounded panel with optional title row."""

    def __init__(self, title=None, subtitle=None):
        super().__init__()
        self.setObjectName("card")
        shadow(self)
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(18, 16, 18, 16)
        self.lay.setSpacing(10)
        self.head = QHBoxLayout()
        self.head.setSpacing(8)
        if title:
            col = QVBoxLayout()
            col.setSpacing(0)
            t = QLabel(title)
            t.setObjectName("h2")
            col.addWidget(t)
            if subtitle:
                self.subtitle = QLabel(subtitle)
                self.subtitle.setObjectName("sub")
                col.addWidget(self.subtitle)
            self.head.addLayout(col)
            self.head.addStretch(1)
            self.lay.addLayout(self.head)


class StatCard(QFrame):
    def __init__(self, title, bg, accent):
        super().__init__()
        self.setObjectName("stat")
        self.setStyleSheet(f"QFrame#stat {{ background:{bg}; }}")
        self.setMinimumHeight(104)
        v = QVBoxLayout(self)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(2)
        v.addStretch(1)
        self.value = QLabel("0")
        self.value.setObjectName("statValue")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setStyleSheet(f"color:{TEXT};")
        v.addWidget(self.value)
        t = QLabel(title)
        t.setObjectName("statTitle")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f"color:{accent};")
        v.addWidget(t)
        self.sub = QLabel("")
        self.sub.setObjectName("statSub")
        self.sub.setAlignment(Qt.AlignCenter)
        v.addWidget(self.sub)
        v.addStretch(1)

    def set(self, value, sub=None):
        self.value.setText(str(value))
        if sub is not None:
            self.sub.setText(sub)


class Ring(QWidget):
    """Circular progress (gradient arc) with centre text."""

    def __init__(self, size=150, width=12, colors=(PURPLE, ORANGE), font_px=None):
        super().__init__()
        self.setFixedSize(size, size)
        self.width_ = width
        self.colors = colors
        self.frac = 0.0
        self.text = "0"
        self.caption = ""
        self.font_px = font_px or int(size * 0.2)

    def set_value(self, frac, text=None, caption=None):
        self.frac = max(0.0, min(1.0, frac))
        if text is not None:
            self.text = text
        if caption is not None:
            self.caption = caption
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width_
        r = QRectF(w / 2 + 2, w / 2 + 2, self.width() - w - 4, self.height() - w - 4)
        pen = QPen(QColor("#eef0f6"), w)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawArc(r, 0, 360 * 16)
        if self.frac > 0:
            g = QConicalGradient(r.center(), 90)
            g.setColorAt(0.0, QColor(self.colors[0]))
            g.setColorAt(1.0, QColor(self.colors[-1]))
            pen = QPen(QBrush(g), w)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawArc(r, 90 * 16, -int(self.frac * 360 * 16))
        p.setPen(QColor(TEXT))
        f = QFont(self.font())
        f.setPixelSize(self.font_px)
        f.setBold(True)
        p.setFont(f)
        tr = QRectF(r)
        if self.caption:
            tr.setHeight(r.height() * 0.62)
            p.drawText(tr, Qt.AlignHCenter | Qt.AlignBottom, self.text)
            f2 = QFont(self.font())
            f2.setPixelSize(max(9, int(self.font_px * 0.45)))
            p.setFont(f2)
            p.setPen(QColor(SUB))
            cr = QRectF(r.left(), r.top() + r.height() * 0.62, r.width(), r.height() * 0.3)
            p.drawText(cr, Qt.AlignHCenter | Qt.AlignTop, self.caption)
        else:
            p.drawText(tr, Qt.AlignCenter, self.text)
        p.end()


class Donut(QWidget):
    """Small ring + label + value (like 'Leads Summary')."""

    def __init__(self, title, color):
        super().__init__()
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        self.ring = Ring(40, 6, (color, color), font_px=11)
        h.addWidget(self.ring)
        v = QVBoxLayout()
        v.setSpacing(0)
        t = QLabel(title)
        t.setObjectName("sub")
        t.setStyleSheet("font-size:8.5pt;")
        v.addWidget(t)
        self.val = QLabel("0")
        self.val.setStyleSheet("font-size:12pt; font-weight:800;")
        v.addWidget(self.val)
        h.addLayout(v)

    def set(self, count, total):
        self.val.setText(str(count))
        self.ring.set_value(count / total if total else 0, "")


# ---------------------------------------------------------------------------
# Background threads
# ---------------------------------------------------------------------------
class FindBlenderThread(QThread):
    found = Signal(list)

    def run(self):
        try:
            self.found.emit(blender_finder.find_blenders())
        except Exception:
            self.found.emit([])


class UpdateCheckThread(QThread):
    result = Signal(dict, str)

    def run(self):
        try:
            self.result.emit(updater.check_remote(), "")
        except Exception as e:
            self.result.emit({}, str(e))


class UpdateInstallThread(QThread):
    log = Signal(str)
    done = Signal(bool, str)

    def __init__(self, remote):
        super().__init__()
        self.remote = remote

    def run(self):
        try:
            updater.download_and_install(self.remote, log=self.log.emit)
            self.done.emit(True, "")
        except Exception as e:
            self.done.emit(False, str(e))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    RE_SAMPLE = re.compile(r"Sample (\d+)/(\d+)")
    RE_REMAIN = re.compile(r"Remaining:\s*([\d:.]+)")

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1460, 940)
        self.setMinimumSize(1180, 760)
        self.setAcceptDrops(True)

        self.settings = load_settings()
        self.proc = None
        self.proc_mode = None
        self.proc_buffer = ""
        self.scan_json_path = None
        self.select_json_path = None
        self.scan_data = None
        self.key_to_item = {}
        self.stop_requested = False
        self.render_start = 0.0
        self.item_start = 0.0
        self.done_count = 0
        self.error_count = 0
        self.done_secs = []
        self.total = 0
        self.threads = []
        self.finish_info = None
        self.item_remaining = ""
        self.last_paths = {}
        self.last_image = None
        self.recent = []

        self._build_ui()
        self._load_into_ui()

        self.tick = QTimer(self)
        self.tick.timeout.connect(self._on_tick)
        self.tick.start(1000)

        self.find_blenders()
        if self.settings.get("auto_check_update", True):
            QTimer.singleShot(1500, lambda: self.check_update(silent=True))

    # ================================================================== UI
    def _btn(self, text, slot=None, obj_name=None, tip=None, icon=None, icon_color=None):
        b = QPushButton(text)
        if obj_name:
            b.setObjectName(obj_name)
        if slot:
            b.clicked.connect(slot)
        if tip:
            b.setToolTip(tip)
        if icon:
            b.setIcon(make_icon(icon, icon_color or SUB))
            b.setIconSize(QSize(16, 16))
        b.setCursor(Qt.PointingHandCursor)
        return b

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_sidebar())

        content = QWidget()
        cv = QVBoxLayout(content)
        cv.setContentsMargins(26, 20, 26, 20)
        cv.setSpacing(16)

        # heading + main actions (the only Start / Stop buttons)
        hrow = QHBoxLayout()
        hrow.setSpacing(10)
        col = QVBoxLayout()
        col.setSpacing(0)
        h = QLabel("Render Overview")
        h.setObjectName("h1")
        col.addWidget(h)
        self.lbl_status = QLabel("Ready.")
        self.lbl_status.setObjectName("sub")
        col.addWidget(self.lbl_status)
        hrow.addLayout(col)
        hrow.addStretch(1)
        self.btn_stop = self._btn("  Stop Now", self.stop_now, "danger", icon="stop", icon_color=RED)
        self.btn_stop.setEnabled(False)
        self.btn_render = self._btn("  Start Render", self.start_render, "primary", icon="play", icon_color="#ffffff")
        self.btn_render.setMinimumWidth(170)
        hrow.addWidget(self.btn_stop)
        hrow.addWidget(self.btn_render)
        cv.addLayout(hrow)

        # stat cards (the only place for counts / overall progress / time)
        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.st_total = StatCard("Images In Scene", "#eaf3ff", BLUE)
        self.st_selected = StatCard("Will Render", "#fff3e6", ORANGE)
        self.st_done = StatCard("Rendered", "#f1edff", PURPLE)
        self.st_time = StatCard("Elapsed Time", "#ffeef2", PINK)
        for c in (self.st_total, self.st_selected, self.st_done, self.st_time):
            stats.addWidget(c)
        self.st_total.set("0", "Scan a scene to count")
        self.st_selected.set("0", "Mode: render all")
        self.st_done.set("0 / 0", "No errors")
        self.st_time.set("00:00", "ETA --:--")
        cv.addLayout(stats)

        mid = QHBoxLayout()
        mid.setSpacing(14)
        mid.addWidget(self._build_project_card(), 5)
        mid.addWidget(self._build_now_card(), 6)
        cv.addLayout(mid)

        bot = QHBoxLayout()
        bot.setSpacing(14)
        bot.addWidget(self._build_items_card(), 11)
        bot.addWidget(self._build_log_card(), 9)
        cv.addLayout(bot, 1)

        self.stack = QStackedWidget()
        self.stack.addWidget(content)                        # 0 dashboard
        self.stack.addWidget(self._build_settings_page())    # 1 settings
        self.stack.addWidget(self._build_info_page())        # 2 info
        outer.addWidget(self.stack, 1)

    # ------------------------------------------------------------------ sidebar (navigation only)
    def _build_sidebar(self):
        sb = QFrame()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(220)
        v = QVBoxLayout(sb)
        v.setContentsMargins(16, 20, 16, 16)
        v.setSpacing(4)

        brand = QHBoxLayout()
        logo = QLabel()
        ico = os.path.join(APP_DIR, "ui", "icon.png")
        if os.path.isfile(ico):
            logo.setPixmap(QPixmap(ico).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        brand.addWidget(logo)
        bc = QVBoxLayout()
        bc.setSpacing(0)
        b1 = QLabel("SCS RENDER")
        b1.setObjectName("brand")
        bc.addWidget(b1)
        b2 = QLabel("Batch render tool")
        b2.setObjectName("brandSub")
        bc.addWidget(b2)
        brand.addLayout(bc)
        brand.addStretch(1)
        v.addLayout(brand)
        v.addSpacing(22)

        sec = QLabel("MENU")
        sec.setObjectName("section")
        v.addWidget(sec)
        v.addSpacing(4)

        self.nav_buttons = {}

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        def nav(key, text, icon):
            b = self._btn("  " + text, lambda: self.show_page(key), "nav", icon=icon)
            b.setIconSize(QSize(18, 18))
            b.setCheckable(True)
            b.setProperty("icon_name", icon)
            self.nav_group.addButton(b)
            self.nav_buttons[key] = b
            v.addWidget(b)
            return b

        nav("dash", "Dashboard", "dashboard")
        nav("settings", "Settings", "settings")
        self.nav_info = nav("info", "Info && Update", "info")
        self.nav_buttons["dash"].setChecked(True)
        self._refresh_nav_icons()
        v.addStretch(1)

        prof = QFrame()
        prof.setObjectName("profile")
        ph = QHBoxLayout(prof)
        ph.setContentsMargins(10, 10, 10, 10)
        av = QLabel(APP_AUTHOR[:1].upper())
        av.setObjectName("avatarBig")
        av.setFixedSize(36, 36)
        av.setAlignment(Qt.AlignCenter)
        ph.addWidget(av)
        pc = QVBoxLayout()
        pc.setSpacing(0)
        n = QLabel(APP_AUTHOR)
        n.setStyleSheet("font-weight:800;")
        pc.addWidget(n)
        r = QLabel("App Creator")
        r.setObjectName("recentSub")
        pc.addWidget(r)
        ph.addLayout(pc)
        ph.addStretch(1)
        v.addWidget(prof)
        return sb

    @staticmethod
    def _elide(text, n):
        return text if len(text) <= n else text[: n - 1] + "…"

    # ------------------------------------------------------------------ project card
    def _build_project_card(self):
        card = Card("Project", "What to render and where to save it")
        g = QGridLayout()
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(10)
        g.setColumnStretch(1, 1)

        lb = QLabel("Blend file")
        lb.setObjectName("fieldLabel")
        g.addWidget(lb, 0, 0)
        self.ed_blend = QLineEdit()
        self.ed_blend.setPlaceholderText("Drop your prepared .blend here or click Browse")
        g.addWidget(self.ed_blend, 0, 1)
        g.addWidget(self._btn("Browse", self.browse_blend), 0, 2)
        self.btn_scan = self._btn("Scan", self.start_scan, tip="Read the .blend and list Scs_N / Icon_N",
                                  icon="scan")
        g.addWidget(self.btn_scan, 0, 3)

        lo = QLabel("Output folder")
        lo.setObjectName("fieldLabel")
        g.addWidget(lo, 1, 0)
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Folder for the PNG images")
        g.addWidget(self.ed_out, 1, 1)
        g.addWidget(self._btn("Browse", self.browse_out), 1, 2)
        g.addWidget(self._btn("Open", self.open_out, icon="folder"), 1, 3)
        card.lay.addLayout(g)

        card.lay.addSpacing(4)
        cl = QLabel("Render settings  (change them on the Settings page)")
        cl.setObjectName("fieldLabel")
        card.lay.addWidget(cl)
        self.btn_cfg = QLabel("")
        self.btn_cfg.setObjectName("cfg")
        self.btn_cfg.setWordWrap(True)
        card.lay.addWidget(self.btn_cfg)
        card.lay.addStretch(1)
        return card

    # ------------------------------------------------------------------ now rendering card
    def _build_now_card(self):
        card = Card("Now Rendering", "Current image and last finished image")
        h = QHBoxLayout()
        h.setSpacing(18)

        self.ring = Ring(132, 12)
        self.ring.set_value(0, "0%", "this image")
        h.addWidget(self.ring, 0, Qt.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(6)
        self.lbl_now = QLabel("Idle")
        self.lbl_now.setObjectName("nowTitle")
        self.lbl_now.setWordWrap(True)
        info.addWidget(self.lbl_now)
        self.lbl_now_info = QLabel("Press Start Render to begin.")
        self.lbl_now_info.setObjectName("sub")
        self.lbl_now_info.setWordWrap(True)
        info.addWidget(self.lbl_now_info)
        self.lbl_time = QLabel("")
        self.lbl_time.setObjectName("sub")
        self.lbl_time.setWordWrap(True)
        info.addWidget(self.lbl_time)
        info.addStretch(1)
        h.addLayout(info, 1)

        tv = QVBoxLayout()
        tv.setSpacing(4)
        self.img = QLabel("No image yet")
        self.img.setObjectName("thumb")
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setFixedSize(200, 150)
        self.img.setCursor(Qt.PointingHandCursor)
        self.img.setToolTip("Click to open the image")
        self.img.mousePressEvent = lambda e: self.open_last_image()
        tv.addWidget(self.img)
        self.lbl_img = QLabel("Last finished image")
        self.lbl_img.setObjectName("sub")
        self.lbl_img.setAlignment(Qt.AlignCenter)
        self.lbl_img.setFixedWidth(200)
        tv.addWidget(self.lbl_img)
        h.addLayout(tv)

        card.lay.addLayout(h)
        return card

    # ------------------------------------------------------------------ scene items card
    def _build_items_card(self):
        card = Card("Scene Items", "Tick the images to render")
        self.ed_search = QLineEdit()
        self.ed_search.setObjectName("search")
        self.ed_search.setPlaceholderText("Search...")
        self.ed_search.addAction(make_icon("search", SUB), QLineEdit.LeadingPosition)
        self.ed_search.setClearButtonEnabled(True)
        self.ed_search.setFixedWidth(200)
        self.ed_search.textChanged.connect(self.apply_filter)
        card.head.addWidget(self.ed_search)
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["Show: all", "Show: Scs", "Show: Icon", "Show: Custom",
                                  "Show: maps", "Show: objects"])
        self.cmb_filter.setFixedWidth(140)
        self.cmb_filter.currentIndexChanged.connect(self.apply_filter)
        card.head.addWidget(self.cmb_filter)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.rb_all = QRadioButton("Render all")
        self.rb_checked = QRadioButton("Checked only")
        for rb in (self.rb_all, self.rb_checked):
            rb.setObjectName("mode")
            rb.setCursor(Qt.PointingHandCursor)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_all)
        self.mode_group.addButton(self.rb_checked)
        self.rb_all.setChecked(True)
        self.rb_all.toggled.connect(lambda *_: self._update_stats())
        row.addWidget(self.rb_all)
        row.addWidget(self.rb_checked)
        row.addStretch(1)
        tick = QLabel("Tick:")
        tick.setObjectName("sub")
        row.addWidget(tick)
        for text, slot in (("All", lambda: self.set_all_checked(True)),
                           ("None", lambda: self.set_all_checked(False)),
                           ("Scs", lambda: self.check_prefix("Scs")),
                           ("Icon", lambda: self.check_prefix("Icon"))):
            row.addWidget(self._btn(text, slot, "pill"))
        card.lay.addLayout(row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Status"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.itemChanged.connect(self._on_tree_changed)
        self.tree.itemDoubleClicked.connect(self._on_tree_double)
        card.lay.addWidget(self.tree, 1)

        self.lbl_scene = QLabel("No scene scanned yet. Choose a .blend file in Project.")
        self.lbl_scene.setObjectName("sub")
        self.lbl_scene.setWordWrap(True)
        card.lay.addWidget(self.lbl_scene)
        return card

    # ------------------------------------------------------------------ log card
    def _build_log_card(self):
        card = Card("Render Log", "Blender output")
        card.head.addWidget(self._btn("Save", self.save_log, "pill"))
        card.head.addWidget(self._btn("Clear", lambda: self.log.clear(), "pill"))
        self.log = QPlainTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(30000)
        card.lay.addWidget(self.log, 1)
        self.chk_verbose = QCheckBox("Show Blender sample lines")
        card.lay.addWidget(self.chk_verbose)
        return card

    # ================================================================== dialogs
    def _size_spin(self, val):
        sp = QSpinBox()
        sp.setRange(16, 16384)
        sp.setSingleStep(2)
        sp.setValue(val)
        sp.setSuffix(" px")
        sp.setMinimumWidth(120)
        sp.valueChanged.connect(self._on_size_changed)
        return sp

    def _page(self, title, subtitle):
        """A page in the main area (same header style as the Dashboard)."""
        page = QWidget()
        pv = QVBoxLayout(page)
        pv.setContentsMargins(26, 20, 26, 20)
        pv.setSpacing(16)
        col = QVBoxLayout()
        col.setSpacing(0)
        h = QLabel(title)
        h.setObjectName("h1")
        col.addWidget(h)
        sub = QLabel(subtitle)
        sub.setObjectName("sub")
        col.addWidget(sub)
        pv.addLayout(col)
        body = QWidget()
        body.setMaximumWidth(900)
        outer = QVBoxLayout(body)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)
        pv.addWidget(body, 0, Qt.AlignLeft)
        pv.addStretch(1)
        body.setMinimumWidth(760)
        return page, outer

    def _dlg_card(self, title):
        f = QFrame()
        f.setObjectName("dlgCard")
        shadow(f, 20, 16, 4)
        v = QVBoxLayout(f)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)
        t = QLabel(title)
        t.setObjectName("h2")
        v.addWidget(t)
        return f, v

    def _build_settings_page(self):
        page, outer = self._page("Settings", "Blender, render options and image size. Changes are saved automatically.")

        f, v = self._dlg_card("Blender executable")
        row = QHBoxLayout()
        self.cmb_blender = QComboBox()
        self.cmb_blender.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_blender.setToolTip("Blender installs found automatically (registry, Program Files, Steam, PATH...)")
        self.cmb_blender.currentIndexChanged.connect(lambda *_: self._refresh_cfg_label())
        row.addWidget(self.cmb_blender, 1)
        self.btn_find = self._btn("Detect again", self.find_blenders, icon="scan")
        row.addWidget(self.btn_find)
        row.addWidget(self._btn("Browse...", self.browse_blender))
        v.addLayout(row)
        hint = QLabel("Blender is detected automatically and the newest version is listed first. "
                      "Use Browse... if your version is not in the list.")
        hint.setObjectName("sub")
        hint.setWordWrap(True)
        v.addWidget(hint)
        outer.addWidget(f)

        f, v = self._dlg_card("Render options")
        ro = QGridLayout()
        ro.setHorizontalSpacing(10)
        ro.setVerticalSpacing(8)
        self.chk_gpu = QCheckBox("Force GPU rendering (Cycles: OptiX / CUDA / HIP / Metal / oneAPI)")
        self.chk_gpu.toggled.connect(lambda *_: self._refresh_cfg_label())
        ro.addWidget(self.chk_gpu, 0, 0, 1, 3)
        sf = QLabel("Start frame")
        sf.setObjectName("fieldLabel")
        ro.addWidget(sf, 1, 0)
        self.sp_frame = QSpinBox()
        self.sp_frame.setRange(-100000, 100000)
        self.sp_frame.setValue(2)
        self.sp_frame.setMinimumWidth(120)
        self.sp_frame.valueChanged.connect(self._on_size_changed)
        ro.addWidget(self.sp_frame, 1, 1)
        fh = QLabel("Collection N renders at frame  Start + (N − 1)   (e.g. Scs_3 → frame 4)")
        fh.setObjectName("sub")
        ro.addWidget(fh, 1, 2)
        ro.setColumnStretch(2, 1)
        v.addLayout(ro)
        outer.addWidget(f)

        f, v = self._dlg_card("Image size")
        g = QGridLayout()
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(8)
        for r, (name, key) in enumerate((("Scs_N", "scs"), ("Icon_N", "icon"))):
            lb = QLabel(name)
            lb.setObjectName("fieldLabel")
            g.addWidget(lb, r, 0)
            w_ = self._size_spin(DEFAULT_RES["Scs" if key == "scs" else "Icon"][0])
            h_ = self._size_spin(DEFAULT_RES["Scs" if key == "scs" else "Icon"][1])
            setattr(self, f"sp_{key}_w", w_)
            setattr(self, f"sp_{key}_h", h_)
            g.addWidget(w_, r, 1)
            x = QLabel("×")
            x.setObjectName("sub")
            g.addWidget(x, r, 2)
            g.addWidget(h_, r, 3)
        lp = QLabel("Resolution scale")
        lp.setObjectName("fieldLabel")
        g.addWidget(lp, 2, 0)
        self.sp_percent = QSpinBox()
        self.sp_percent.setRange(1, 100)
        self.sp_percent.setValue(100)
        self.sp_percent.setSuffix(" %")
        self.sp_percent.setToolTip("100% = exact size above. Use 10-25% for quick test renders.")
        self.sp_percent.valueChanged.connect(self._on_size_changed)
        g.addWidget(self.sp_percent, 2, 1)
        self.lbl_size_preview = QLabel("")
        self.lbl_size_preview.setObjectName("sub")
        g.addWidget(self.lbl_size_preview, 2, 2, 1, 3)
        g.addWidget(self._btn("Reset to default", self.reset_sizes,
                              tip="Scs 2796×2048, Icon 2048×2048, 100%"), 0, 4)
        g.setColumnStretch(5, 1)
        v.addLayout(g)
        outer.addWidget(f)

        return page

    def _build_info_page(self):
        page, outer = self._page("Info & Update", "About this app and software updates")

        f = QFrame()
        f.setObjectName("dlgCard")
        shadow(f, 20, 16, 4)
        hh = QHBoxLayout(f)
        hh.setContentsMargins(16, 14, 16, 14)
        hh.setSpacing(14)
        logo = QLabel()
        ico = os.path.join(APP_DIR, "ui", "icon.png")
        if os.path.isfile(ico):
            logo.setPixmap(QPixmap(ico).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        hh.addWidget(logo)
        tc = QVBoxLayout()
        tc.setSpacing(0)
        t = QLabel("SCS Batch Render")
        t.setObjectName("h1")
        tc.addWidget(t)
        ver = QLabel(f"Version {APP_VERSION}")
        ver.setObjectName("sub")
        tc.addWidget(ver)
        hh.addLayout(tc)
        hh.addStretch(1)
        outer.addWidget(f)

        f, v = self._dlg_card("About")
        g = QGridLayout()
        g.setColumnStretch(1, 1)
        g.setVerticalSpacing(8)
        a = QLabel("Created by")
        a.setObjectName("fieldLabel")
        g.addWidget(a, 0, 0)
        au = QLabel(APP_AUTHOR)
        au.setObjectName("author")
        g.addWidget(au, 0, 1)
        d = QLabel("Description")
        d.setObjectName("fieldLabel")
        g.addWidget(d, 1, 0, Qt.AlignTop)
        desc = QLabel("Batch renders Icon / SCS images (Scs_N, Icon_N, Map, Custom) from a prepared "
                      "Blender file, running Blender in the background.")
        desc.setWordWrap(True)
        desc.setMinimumHeight(58)
        g.addWidget(desc, 1, 1)
        gh = QLabel("GitHub")
        gh.setObjectName("fieldLabel")
        g.addWidget(gh, 2, 0)
        link = QLabel(f'<a style="color:{PURPLE}; text-decoration:none" href="{updater.REPO_URL}">'
                      f'{updater.REPO_URL.replace("https://", "")}</a>')
        link.setOpenExternalLinks(True)
        g.addWidget(link, 2, 1)
        v.addLayout(g)
        outer.addWidget(f)

        f, v = self._dlg_card("Update")
        self.lbl_update_status = QLabel(f"You are on v{APP_VERSION}. Not checked yet.")
        self.lbl_update_status.setWordWrap(True)
        v.addWidget(self.lbl_update_status)
        row = QHBoxLayout()
        self.btn_update = self._btn("  Check for updates", lambda: self.check_update(silent=False), "primary",
                                    f"Check {updater.RELEASES_URL}", icon="update", icon_color="#ffffff")
        self.btn_update.setMinimumHeight(42)
        row.addWidget(self.btn_update)
        rel = QLabel(f'<a style="color:{PURPLE}; text-decoration:none" href="{updater.RELEASES_URL}">'
                     f'View all releases</a>')
        rel.setOpenExternalLinks(True)
        row.addWidget(rel)
        row.addStretch(1)
        v.addLayout(row)
        self.chk_auto_update = QCheckBox("Check for updates when the app starts")
        v.addWidget(self.chk_auto_update)
        outer.addWidget(f)

        foot = QLabel(f"© {time.strftime('%Y')} {APP_AUTHOR}. All rights reserved.")
        foot.setObjectName("sub")
        outer.addWidget(foot)
        return page

    # ------------------------------------------------------------------ page switching
    PAGES = {"dash": 0, "settings": 1, "info": 2}

    def show_page(self, key):
        if self.stack.currentIndex() == self.PAGES["settings"] and key != "settings":
            save_settings(self._collect_settings())
        self.stack.setCurrentIndex(self.PAGES[key])
        self.nav_buttons[key].setChecked(True)
        self._refresh_nav_icons()

    def _refresh_nav_icons(self):
        for b in self.nav_buttons.values():
            b.setIcon(make_icon(b.property("icon_name"), PURPLE if b.isChecked() else SUB))

    def open_settings(self):
        self.show_page("settings")

    def open_info(self):
        self.show_page("info")

    # ------------------------------------------------------------------ sizes
    def res_for(self, prefix):
        if prefix == "Scs":
            return self.sp_scs_w.value(), self.sp_scs_h.value()
        if prefix == "Icon":
            return self.sp_icon_w.value(), self.sp_icon_h.value()
        return None

    def reset_sizes(self):
        self.sp_scs_w.setValue(DEFAULT_RES["Scs"][0])
        self.sp_scs_h.setValue(DEFAULT_RES["Scs"][1])
        self.sp_icon_w.setValue(DEFAULT_RES["Icon"][0])
        self.sp_icon_h.setValue(DEFAULT_RES["Icon"][1])
        self.sp_percent.setValue(100)

    def _on_size_changed(self, *_):
        if not hasattr(self, "sp_percent") or not hasattr(self, "sp_icon_h") or not hasattr(self, "sp_frame"):
            return
        p = self.sp_percent.value() / 100.0
        sw, sh = self.res_for("Scs")
        iw, ih = self.res_for("Icon")
        self.lbl_size_preview.setText(f"Output: Scs {int(sw * p)}×{int(sh * p)}, Icon {int(iw * p)}×{int(ih * p)}")
        self._refresh_tree_res()
        self._refresh_cfg_label()

    def _refresh_cfg_label(self):
        if not all(hasattr(self, a) for a in ("btn_cfg", "sp_icon_h", "chk_gpu", "sp_frame")):
            return
        txt = self.cmb_blender.currentText()
        short = txt.split("  -  ")[0] if "  -  " in txt else (os.path.basename(txt) if txt else "")
        if not self.blender_exe():
            short = "No blender.exe selected"
        sw, sh = self.res_for("Scs")
        iw, ih = self.res_for("Icon")
        pct = self.sp_percent.value()
        gpu = "GPU" if self.chk_gpu.isChecked() else "Scene device"
        self.btn_cfg.setText(f"⚙  {short}  ·  {gpu}  ·  Start frame {self.sp_frame.value()}\n"
                             f"     Scs {sw}×{sh}  ·  Icon {iw}×{ih}" + (f"  ·  Scale {pct}%" if pct != 100 else ""))

    def _refresh_tree_res(self):
        if not hasattr(self, "tree"):
            return
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            d = top.data(0, Qt.UserRole) or {}
            res = self.res_for(d.get("prefix"))
            if res and "number" in d:
                frame = self.sp_frame.value() + d["number"] - 1
                top.setText(1, f"{res[0]}×{res[1]}  ·  F{frame}")
        self.tree.blockSignals(False)

    def _res_args(self):
        sw, sh = self.res_for("Scs")
        iw, ih = self.res_for("Icon")
        return ["--scs-res", f"{sw}x{sh}", "--icon-res", f"{iw}x{ih}"]

    # ------------------------------------------------------------------ settings io
    def _load_into_ui(self):
        s = self.settings
        self.ed_blend.setText(s.get("blend_file", ""))
        self.ed_out.setText(s.get("output_dir", ""))
        self.chk_gpu.setChecked(s.get("gpu", True))
        self.sp_frame.setValue(int(s.get("start_frame", 2)))
        self.sp_percent.setValue(int(s.get("percent", 100)))
        sr = s.get("scs_res") or DEFAULT_RES["Scs"]
        ir = s.get("icon_res") or DEFAULT_RES["Icon"]
        self.sp_scs_w.setValue(int(sr[0]))
        self.sp_scs_h.setValue(int(sr[1]))
        self.sp_icon_w.setValue(int(ir[0]))
        self.sp_icon_h.setValue(int(ir[1]))
        self.chk_auto_update.setChecked(s.get("auto_check_update", True))
        (self.rb_checked if s.get("mode") == "checked" else self.rb_all).setChecked(True)
        if s.get("blender_exe") and os.path.isfile(s["blender_exe"]):
            self._add_blender_item(s["blender_exe"], s["blender_exe"], select=True)
        self._on_size_changed()

    def _collect_settings(self):
        s = self.settings
        s["blender_exe"] = self.blender_exe()
        s["blend_file"] = self.ed_blend.text().strip().strip('"')
        s["output_dir"] = self.ed_out.text().strip().strip('"')
        s["gpu"] = self.chk_gpu.isChecked()
        s["start_frame"] = self.sp_frame.value()
        s["percent"] = self.sp_percent.value()
        s["scs_res"] = list(self.res_for("Scs"))
        s["icon_res"] = list(self.res_for("Icon"))
        s["auto_check_update"] = self.chk_auto_update.isChecked()
        s["mode"] = "checked" if self.rb_checked.isChecked() else "all"
        return s

    def closeEvent(self, e):
        if self._busy():
            r = QMessageBox.question(self, APP_NAME, "Blender is still running. Stop it and quit?")
            if r != QMessageBox.Yes:
                e.ignore()
                return
            self.stop_now()
        self._remember_unchecked()
        save_settings(self._collect_settings())
        super().closeEvent(e)

    # ------------------------------------------------------------------ log
    def write_log(self, text):
        self.log.appendPlainText(text)

    def save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save log", os.path.join(self.ed_out.text() or APP_DIR,
                                           f"render_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"), "Text (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())

    # ------------------------------------------------------------------ blender exe
    def blender_exe(self):
        return self.cmb_blender.currentData() or ""

    def _add_blender_item(self, path, label, select=False):
        for i in range(self.cmb_blender.count()):
            if os.path.normcase(self.cmb_blender.itemData(i) or "") == os.path.normcase(path):
                if label and label != path:
                    self.cmb_blender.setItemText(i, label)
                if select:
                    self.cmb_blender.setCurrentIndex(i)
                self._refresh_cfg_label()
                return
        self.cmb_blender.addItem(label or path, path)
        if select:
            self.cmb_blender.setCurrentIndex(self.cmb_blender.count() - 1)
        self._refresh_cfg_label()

    def find_blenders(self):
        self.btn_find.setEnabled(False)
        self.btn_find.setText("Detecting...")
        self.write_log("Detecting Blender installs...")
        th = FindBlenderThread()
        th.found.connect(self._on_blenders_found)
        th.finished.connect(lambda: self.threads.remove(th) if th in self.threads else None)
        self.threads.append(th)
        th.start()

    def _on_blenders_found(self, items):
        self.btn_find.setEnabled(True)
        self.btn_find.setText("Detect again")
        keep = self.blender_exe() or self.settings.get("blender_exe", "")
        for b in items:
            self._add_blender_item(b["path"], b["label"])
        if items:
            self.write_log(f"Found {len(items)} Blender install(s):")
            for b in items:
                self.write_log("   " + b["label"])
        else:
            self.write_log("!!! No blender.exe found automatically - pick it in Settings > Browse...")
        if keep and os.path.isfile(keep):
            self._add_blender_item(keep, "", select=True)
        elif items:
            self._add_blender_item(items[0]["path"], items[0]["label"], select=True)

    def browse_blender(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select blender.exe", "",
                                              "blender.exe (blender.exe);;Programs (*.exe)")
        if path:
            path = os.path.abspath(path)
            v = blender_finder.get_blender_version(path)
            label = (f"Blender {'.'.join(map(str, v))}  -  " if v else "") + path
            self._add_blender_item(path, label, select=True)

    # ------------------------------------------------------------------ paths
    def browse_blend(self):
        start = os.path.dirname(self.ed_blend.text()) if self.ed_blend.text() else ""
        path, _ = QFileDialog.getOpenFileName(self, "Select .blend file", start, "Blender (*.blend)")
        if path:
            self.set_blend(path)

    def set_blend(self, path):
        self._remember_unchecked()
        self.ed_blend.setText(os.path.abspath(path))
        if not self.ed_out.text().strip():
            self.ed_out.setText(os.path.join(os.path.dirname(path), "Render"))
        self.start_scan()

    def browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Select output folder", self.ed_out.text())
        if d:
            self.ed_out.setText(os.path.abspath(d))

    def open_out(self):
        d = self.ed_out.text().strip()
        if d and os.path.isdir(d):
            QDesktopServices.openUrl(QUrl.fromLocalFile(d))
        else:
            QMessageBox.information(self, APP_NAME, "The output folder does not exist yet.")

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if p.lower().endswith(".blend"):
                self.set_blend(p)
                return
            if os.path.isdir(p):
                self.ed_out.setText(p)
                return
            if os.path.basename(p).lower() == "blender.exe":
                self._add_blender_item(p, p, select=True)
                return

    # ------------------------------------------------------------------ validation
    def _check_inputs(self, need_out=True):
        exe = self.blender_exe()
        blend = self.ed_blend.text().strip().strip('"')
        out = self.ed_out.text().strip().strip('"')
        if not exe or not os.path.isfile(exe):
            QMessageBox.warning(self, APP_NAME, "No valid blender.exe selected.\nPlease choose one on the Settings page.")
            self.open_settings()
            return None
        if not blend or not os.path.isfile(blend):
            QMessageBox.warning(self, APP_NAME, "Please select a .blend file (the file was not found).")
            return None
        if need_out and not out:
            QMessageBox.warning(self, APP_NAME, "Please select an output folder.")
            return None
        if not os.path.isfile(CORE_SCRIPT):
            QMessageBox.critical(self, APP_NAME, f"Missing {CORE_SCRIPT}. Please update the app (Info > Update).")
            return None
        return exe, blend, out

    def _busy(self):
        return self.proc is not None and self.proc.state() != QProcess.NotRunning

    def _set_running(self, running):
        self.btn_render.setEnabled(not running)
        self.btn_scan.setEnabled(not running)
        self.btn_update.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    # ------------------------------------------------------------------ process
    def _start_process(self, exe, args, mode):
        self.proc = QProcess(self)
        self.proc_mode = mode
        self.proc_buffer = ""
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUNBUFFERED", "1")
        self.proc.setProcessEnvironment(env)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._on_output)
        self.proc.finished.connect(self._on_finished)
        self.proc.errorOccurred.connect(self._on_proc_error)
        self.write_log("> " + " ".join(f'"{a}"' if " " in a else a for a in [exe] + args))
        self.stop_requested = False
        self._set_running(True)
        self.proc.start(exe, args)

    def _on_proc_error(self, err):
        if err == QProcess.FailedToStart:
            self.write_log("!!! Could not start Blender (wrong path or blocked).")
            self._set_running(False)

    def _on_output(self):
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.proc_buffer += data.replace("\r\n", "\n").replace("\r", "\n")
        while "\n" in self.proc_buffer:
            line, self.proc_buffer = self.proc_buffer.split("\n", 1)
            self._handle_line(line)

    def _handle_line(self, line):
        if line.startswith("@@SCS "):
            try:
                self._handle_marker(json.loads(line[6:]))
            except Exception:
                pass
            return
        m = self.RE_SAMPLE.search(line)
        if m:
            cur, tot = int(m.group(1)), int(m.group(2))
            self.ring.set_value(cur / max(1, tot), f"{int(100 * cur / max(1, tot))}%", f"sample {cur}/{tot}")
            r = self.RE_REMAIN.search(line)
            self.item_remaining = r.group(1) if r else ""
            if not self.chk_verbose.isChecked():
                return
        elif line.startswith("Fra:") and not self.chk_verbose.isChecked():
            return
        if line.strip():
            self.write_log(line)

    def _handle_marker(self, d):
        ev = d.get("ev")
        if ev == "total":
            self.total = d["total"]
            self._update_progress()
        elif ev == "item":
            self.item_start = time.time()
            self.item_remaining = ""
            self.ring.set_value(0, "0%", "preparing")
            self.lbl_now.setText(f"{d['collection']}  ›  {d['label']}")
            res = d.get("res") or ["?", "?"]
            self.lbl_now_info.setText(f"Image {d['i']} of {d['total']}   ·   {res[0]}×{res[1]}   ·   "
                                      f"Frame {d.get('frame')}\n{os.path.basename(d.get('path', ''))}")
            self.lbl_status.setText(f"Rendering {d['i']}/{d['total']}: {d['collection']} › {d['label']}")
            self._mark_item(d["key"], "Rendering...", C_RENDERING, scroll=True)
        elif ev == "done":
            self.done_count += 1
            self.done_secs.append(d.get("sec", 0))
            self.ring.set_value(1, "100%", "saved")
            self._mark_item(d["key"], f"Done  {d.get('sec', 0)}s", C_DONE)
            self.last_paths[d["key"]] = d.get("path")
            self.show_image(d.get("path"))
            self._update_progress()
        elif ev == "error":
            self.done_count += 1
            self.error_count += 1
            self._mark_item(d["key"], "ERROR", C_ERROR)
            self.write_log(f"!!! ERROR {d.get('key')}: {d.get('msg')}")
            self._update_progress()
        elif ev == "finish":
            self.finish_info = d

    def _update_progress(self):
        t = max(self.total, 0)
        pct = int(100 * self.done_count / t) if t else 0
        self.st_done.set(f"{self.done_count} / {t}",
                         f"{pct}% complete  ·  " + (f"{self.error_count} error(s)" if self.error_count else "no errors"))

    def _mark_item(self, key, text, color, scroll=False):
        it = self.key_to_item.get(key)
        if not it:
            return
        self.tree.blockSignals(True)
        it.setText(2, text)
        it.setForeground(2, QBrush(color))
        self.tree.blockSignals(False)
        if scroll:
            self.tree.scrollToItem(it)

    def _on_tick(self):
        if not self._busy() or self.proc_mode != "render":
            return
        el = time.time() - self.render_start
        it = time.time() - self.item_start if self.item_start else 0
        txt = f"This image: {human_time(it)}"
        if self.item_remaining:
            txt += f"  (~{self.item_remaining} left)"
        eta = "--:--"
        if self.done_secs and self.total:
            avg = sum(self.done_secs) / len(self.done_secs)
            eta = human_time(avg * (self.total - self.done_count))
            txt += f"\nAverage {avg:.1f}s per image"
        self.lbl_time.setText(txt)
        self.st_time.set(human_time(el), f"ETA {eta}")

    def _on_finished(self, code, status):
        if self.proc_buffer.strip():
            self._handle_line(self.proc_buffer)
            self.proc_buffer = ""
        mode = self.proc_mode
        self.proc_mode = None
        self._set_running(False)

        if mode == "scan":
            self._on_scan_finished(code)
        elif mode == "render":
            el = human_time(time.time() - self.render_start)
            self.st_time.set(el, "Finished")
            if self.stop_requested:
                self.lbl_now.setText("Stopped")
                self.lbl_now_info.setText(f"Stopped by user after {el}.")
                self.lbl_status.setText(f"Stopped after {el}. {self.done_count}/{self.total} images done.")
                self.write_log(f"\n=== STOPPED by user | {self.done_count}/{self.total} images | {el} ===")
                for key, it in self.key_to_item.items():
                    if it.text(2) == "Rendering...":
                        self._mark_item(key, "Stopped", C_ERROR)
            else:
                fi = self.finish_info or {}
                ok, fail = fi.get("ok", self.done_count), fi.get("fail", 0)
                if fi:
                    self.lbl_now.setText("All done ✓" if not fail else "Finished with errors")
                    msg = f"Finished: {ok} OK, {fail} failed, total {el}."
                else:
                    self.lbl_now.setText("Blender exited")
                    msg = f"Blender exited (code {code}) before finishing - see the log."
                self.lbl_now_info.setText(msg)
                self.lbl_status.setText(msg)
                self.write_log("\n=== " + msg + " ===")
                QApplication.alert(self)
        self._cleanup_temp()

    def _cleanup_temp(self):
        p = self.select_json_path
        if p and os.path.isfile(p):
            try:
                os.remove(p)
            except Exception:
                pass
        self.select_json_path = None

    def stop_now(self):
        if not self._busy():
            return
        self.stop_requested = True
        self.write_log("\n>>> STOP NOW - killing Blender...")
        kill_tree(self.proc.processId())
        self.proc.kill()

    # ------------------------------------------------------------------ scan
    def start_scan(self):
        if self._busy():
            return
        r = self._check_inputs(need_out=False)
        if not r:
            return
        exe, blend, _ = r
        save_settings(self._collect_settings())
        fd, self.scan_json_path = tempfile.mkstemp(prefix="scs_scan_", suffix=".json")
        os.close(fd)
        self.lbl_scene.setText("Scanning scene (Blender is opening the file)...")
        self.lbl_status.setText("Scanning scene...")
        self.write_log(f"\n=== SCAN SCENE: {blend} ===")
        args = ["--background", blend, "--python", CORE_SCRIPT, "--python-exit-code", "1", "--",
                "--scan-json", self.scan_json_path, "--start-frame", str(self.sp_frame.value())] + self._res_args()
        self._start_process(exe, args, "scan")

    def _on_scan_finished(self, code):
        data = None
        try:
            with open(self.scan_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
        try:
            os.remove(self.scan_json_path)
        except Exception:
            pass
        if not data:
            self.lbl_scene.setText("Scan failed - see the Render Log.")
            self.lbl_status.setText(f"Scan failed (code {code}).")
            return
        self.scan_data = data
        self.populate_tree(data)
        self.lbl_status.setText("Scan complete.")

    TYPE_NAMES = {"map": "Map", "map_event": "Map event", "object": "Object"}

    def populate_tree(self, data):
        self.tree.blockSignals(True)
        self.tree.clear()
        self.key_to_item = {}
        self.last_paths = {}
        unchecked = set(self.settings.get("unchecked", {}).get(self._blend_key(), []))

        n_scs = n_icon = img_scs = img_icon = 0
        for c in data.get("collections", []):
            res = self.res_for(c["prefix"]) or c["resolution"]
            frame = self.sp_frame.value() + c["number"] - 1
            top = QTreeWidgetItem([c["name"], f"{res[0]}×{res[1]}  ·  F{frame}", f"{len(c['items'])} image" + ("s" if len(c['items']) != 1 else "")])
            top.setFlags(top.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            top.setData(0, Qt.UserRole, {"kind": "col", "prefix": c["prefix"], "name": c["name"],
                                         "number": c["number"]})
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)
            top.setForeground(2, QBrush(QColor(SUB)))
            self.tree.addTopLevelItem(top)
            for i in c["items"]:
                ch = QTreeWidgetItem([i["label"], self.TYPE_NAMES.get(i["type"], i["type"]), ""])
                ch.setFlags(ch.flags() | Qt.ItemIsUserCheckable)
                ch.setData(0, Qt.UserRole, {"kind": "item", "key": i["key"], "prefix": c["prefix"],
                                            "type": i["type"]})
                ch.setCheckState(0, Qt.Unchecked if i["key"] in unchecked else Qt.Checked)
                top.addChild(ch)
                self.key_to_item[i["key"]] = ch
            if not c["items"]:
                top.setCheckState(0, Qt.Unchecked)
            if c["prefix"] == "Scs":
                n_scs += 1
                img_scs += len(c["items"])
            else:
                n_icon += 1
                img_icon += len(c["items"])

        custom = data.get("custom", [])
        if custom:
            top = QTreeWidgetItem(["Custom (scs_render_separate)", "original frame", f"{len(custom)} image" + ("s" if len(custom) != 1 else "")])
            top.setFlags(top.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            top.setData(0, Qt.UserRole, {"kind": "col", "prefix": "Custom", "name": "Custom"})
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)
            top.setForeground(2, QBrush(QColor(SUB)))
            self.tree.addTopLevelItem(top)
            for i in custom:
                ch = QTreeWidgetItem([i["label"], f"Custom ({i.get('collection', '')})", ""])
                ch.setFlags(ch.flags() | Qt.ItemIsUserCheckable)
                ch.setData(0, Qt.UserRole, {"kind": "item", "key": i["key"], "prefix": "Custom",
                                            "type": "custom"})
                ch.setCheckState(0, Qt.Unchecked if i["key"] in unchecked else Qt.Checked)
                top.addChild(ch)
                self.key_to_item[i["key"]] = ch

        if len(self.key_to_item) < 80:
            self.tree.expandAll()
        self.tree.blockSignals(False)
        self._refresh_check_colors()

        total = img_scs + img_icon + len(custom)
        self.scene_counts = (img_scs, img_icon, len(custom), total)
        self.st_total.set(total, f"Scs {img_scs}  ·  Icon {img_icon}  ·  Custom {len(custom)}")

        warn = []
        if not data.get("has_setup"):
            warn.append("no 'Setup' collection")
        if data.get("engine") != "CYCLES":
            warn.append(f"engine is {data.get('engine')} (GPU option only works with Cycles)")
        self.lbl_scene.setText(f"{os.path.basename(data.get('blend') or '')}  ·  scene '{data.get('scene')}'  ·  "
                               f"{n_scs} Scs + {n_icon} Icon collections  ·  Map: {'yes' if data.get('has_map') else 'no'}"
                               + ("   ⚠ " + ", ".join(warn) if warn else ""))
        self.write_log(f"Scan complete: Scs {n_scs} ({img_scs} images), Icon {n_icon} ({img_icon} images), "
                       f"Custom {len(custom)}, total {total} images.")
        if warn:
            self.write_log("!!! Warning: " + "; ".join(warn))
        self.apply_filter()
        self._update_stats()

    def _blend_key(self):
        return os.path.normcase(os.path.abspath(self.ed_blend.text().strip().strip('"') or "_"))

    def _remember_unchecked(self):
        if not self.key_to_item:
            return
        un = [k for k, it in self.key_to_item.items() if it.checkState(0) != Qt.Checked]
        self.settings.setdefault("unchecked", {})[self._blend_key()] = un

    def checked_keys(self):
        return [k for k, it in self.key_to_item.items() if it.checkState(0) == Qt.Checked]

    def _on_tree_changed(self, item, col):
        if col == 0:
            self._refresh_check_colors()
            self._update_stats()

    def _refresh_check_colors(self):
        self.tree.blockSignals(True)
        for it in self.key_to_item.values():
            col = C_ON if it.checkState(0) == Qt.Checked else C_DIM
            it.setForeground(0, QBrush(col))
            it.setForeground(1, QBrush(col if col == C_DIM else QColor(SUB)))
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            st = top.checkState(0)
            top.setForeground(0, QBrush(C_ON if st == Qt.Checked else C_PART if st == Qt.PartiallyChecked else C_DIM))
            top.setForeground(1, QBrush(QColor(SUB)))
        self.tree.blockSignals(False)

    def _on_tree_double(self, item, col):
        d = item.data(0, Qt.UserRole) or {}
        p = self.last_paths.get(d.get("key")) if d.get("kind") == "item" else None
        if p and os.path.isfile(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _update_stats(self):
        n_all = len(self.key_to_item)
        n_chk = len(self.checked_keys())
        if self.rb_checked.isChecked():
            self.st_selected.set(n_chk, f"Checked only  ·  {n_all - n_chk} skipped")
        else:
            self.st_selected.set(n_all, f"Render all  ·  {n_chk} of {n_all} ticked" if n_all else "Mode: render all")


    def set_all_checked(self, state):
        self.tree.blockSignals(True)
        for it in self.key_to_item.values():
            it.setCheckState(0, Qt.Checked if state else Qt.Unchecked)
        self.tree.blockSignals(False)
        self._refresh_check_colors()
        self._update_stats()

    def check_prefix(self, prefix):
        self.tree.blockSignals(True)
        for it in self.key_to_item.values():
            p = (it.data(0, Qt.UserRole) or {}).get("prefix")
            it.setCheckState(0, Qt.Checked if p == prefix else Qt.Unchecked)
        self.tree.blockSignals(False)
        self._refresh_check_colors()
        self.rb_checked.setChecked(True)
        self._update_stats()

    def apply_filter(self, *_):
        text = self.ed_search.text().strip().lower()
        mode = self.cmb_filter.currentIndex()
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            prefix = (top.data(0, Qt.UserRole) or {}).get("prefix")
            visible_children = 0
            for j in range(top.childCount()):
                ch = top.child(j)
                t = (ch.data(0, Qt.UserRole) or {}).get("type")
                ok = True
                if mode == 1:
                    ok = prefix == "Scs"
                elif mode == 2:
                    ok = prefix == "Icon"
                elif mode == 3:
                    ok = prefix == "Custom"
                elif mode == 4:
                    ok = t in ("map", "map_event")
                elif mode == 5:
                    ok = t == "object"
                if ok and text:
                    ok = text in ch.text(0).lower() or text in top.text(0).lower()
                ch.setHidden(not ok)
                visible_children += ok
            top.setHidden(visible_children == 0 and top.childCount() > 0)
            if text and visible_children:
                top.setExpanded(True)

    # ------------------------------------------------------------------ render
    def start_render(self):
        if self._busy():
            return
        r = self._check_inputs()
        if not r:
            return
        exe, blend, out = r
        only_checked = self.rb_checked.isChecked()
        keys = []
        if only_checked:
            if not self.key_to_item:
                QMessageBox.information(self, APP_NAME, "Please Scan the scene first to choose what to render.")
                return
            keys = self.checked_keys()
            if not keys:
                QMessageBox.information(self, APP_NAME, "Nothing is checked.")
                return
        os.makedirs(out, exist_ok=True)
        self._remember_unchecked()
        save_settings(self._collect_settings())

        for key in self.key_to_item:
            self._mark_item(key, "", C_NORMAL)
        self.done_count = 0
        self.error_count = 0
        self.done_secs = []
        self.total = 0
        self.finish_info = None
        self.item_start = 0
        self.render_start = time.time()
        self._update_progress()
        self.ring.set_value(0, "0%", "this image")
        self.st_time.set("00:00", "ETA --:--")
        self.lbl_now.setText("Starting Blender...")
        self.lbl_now_info.setText("The first image can take a few minutes (shader compile / loading the scene).")

        args = ["--background", blend, "--python", CORE_SCRIPT, "--python-exit-code", "1", "--",
                "--output", out, "--start-frame", str(self.sp_frame.value()),
                "--percent", str(self.sp_percent.value())] + self._res_args()
        if self.sp_percent.value() < 100:
            self.write_log(f"!!! Note: rendering at {self.sp_percent.value()}% resolution (test render).")
        if self.chk_gpu.isChecked():
            args.append("--gpu")
        if only_checked:
            fd, self.select_json_path = tempfile.mkstemp(prefix="scs_select_", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(keys, f, ensure_ascii=False)
            args += ["--select", self.select_json_path]
            self.write_log(f"\n=== RENDER {len(keys)} CHECKED ITEM(S) ===")
        else:
            self.write_log("\n=== RENDER ALL ===")
        self._start_process(exe, args, "render")

    # ------------------------------------------------------------------ preview
    def show_image(self, path):
        if not path or not os.path.isfile(path):
            return
        pm = QPixmap(path)
        if pm.isNull():
            return
        self.last_image = path
        self.img.setPixmap(pm.scaled(self.img.width() - 8, self.img.height() - 8,
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.lbl_img.setText(self._elide(os.path.basename(path), 26) + f"  ·  {pm.width()}×{pm.height()}")
        self.lbl_img.setToolTip(path)

    def open_last_image(self):
        if self.last_image and os.path.isfile(self.last_image):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_image))

    # ------------------------------------------------------------------ update
    def check_update(self, silent=False):
        if self._busy():
            return
        self.btn_update.setEnabled(False)
        self.btn_update.setText("  Checking...")
        th = UpdateCheckThread()
        th.result.connect(lambda info, err: self._on_update_checked(info, err, silent))
        th.finished.connect(lambda: self.threads.remove(th) if th in self.threads else None)
        self.threads.append(th)
        th.start()

    def _on_update_checked(self, info, err, silent):
        self.btn_update.setEnabled(not self._busy())
        self.btn_update.setText("  Check for updates")
        if err:
            if not silent:
                QMessageBox.warning(self, "Update", f"Could not check for updates:\n{err}")
            self.write_log(f"[update] error: {err}")
            self.lbl_update_status.setText(f"You are on v{APP_VERSION}. Could not check: {err}")
            return
        lver = updater.local_version()
        rver = info.get("version") or "?"
        self.lbl_update_status.setText(
            f"You are on v{lver}. Latest release: {info.get('tag')} ({info.get('date', '')}).")
        if not updater.is_newer(info, lver):
            self.nav_info.setText("  Info && Update")
            self.nav_info.setStyleSheet("")
            self.write_log(f"[update] Up to date (v{lver}, latest release {info.get('tag')}).")
            if not silent:
                QMessageBox.information(self, "Update", f"You are using the latest version (v{lver}).")
            return
        self.nav_info.setText("  Info && Update  ●")
        self.nav_info.setStyleSheet(f"color:{RED};")
        self.nav_info.setToolTip(f"New version {info.get('tag')} available")
        self.lbl_update_status.setText(f"<b style='color:{GREEN}'>New version {info.get('tag')} available</b> "
                                       f"({info.get('date', '')}). You are on v{lver}.")
        notes = info.get("notes", "")
        if len(notes) > 900:
            notes = notes[:900] + "..."
        msg = (f"A new version is available: {info.get('name')}  ({info.get('date', '')})\n"
               f"Current: v{lver}  →  New: v{rver}\n\n{notes}\n\n"
               f"Update now? (The app will restart)")
        if QMessageBox.question(self, "Update", msg) != QMessageBox.Yes:
            return
        self.btn_update.setEnabled(False)
        self.btn_update.setText("  Downloading...")
        th = UpdateInstallThread(info)
        th.log.connect(lambda s: self.write_log("[update] " + s))
        th.done.connect(self._on_update_installed)
        th.finished.connect(lambda: self.threads.remove(th) if th in self.threads else None)
        self.threads.append(th)
        th.start()

    def _on_update_installed(self, ok, err):
        self.btn_update.setEnabled(True)
        self.btn_update.setText("  Check for updates")
        if not ok:
            QMessageBox.critical(self, "Update", f"Update failed:\n{err}")
            return
        QMessageBox.information(self, "Update", "Update installed. The app will now restart.")
        self._remember_unchecked()
        save_settings(self._collect_settings())
        subprocess.Popen([sys.executable, os.path.abspath(__file__)], cwd=APP_DIR)
        QApplication.quit()


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("3DSix.SCSBatchRender")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(build_style())
    for ico in ("icon.ico", os.path.join("ui", "icon.png")):
        p = os.path.join(APP_DIR, ico)
        if os.path.isfile(p):
            app.setWindowIcon(QIcon(p))
            break
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
