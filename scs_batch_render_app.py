# -*- coding: utf-8 -*-
"""
SCS Batch Render - App UI (PySide6)
Chay Blender o che do background de render hang loat Scs_N / Icon_N.
Repo: https://github.com/3DSixStudio/Render-Batch
"""

import os
import re
import sys
import json
import time
import tempfile
import subprocess

from PySide6.QtCore import Qt, QThread, Signal, QProcess, QProcessEnvironment, QTimer, QUrl
from PySide6.QtGui import QPixmap, QDesktopServices, QFont, QColor, QBrush, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QGroupBox, QCheckBox, QRadioButton,
    QButtonGroup, QSpinBox, QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QProgressBar,
    QSplitter, QMessageBox, QHeaderView, QSizePolicy, QFrame, QDialog, QDialogButtonBox,
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

# Mau trang thai item
C_RENDERING = QColor("#f0c050")
C_DONE = QColor("#6fd36f")
C_ERROR = QColor("#ff6b6b")
C_DIM = QColor("#6b7079")
C_ON = QColor("#ffffff")
C_PART = QColor("#9fc6ff")

STYLE = """
QWidget { background:#23262b; color:#dfe3e8; font-family:'Segoe UI'; font-size:10pt; }
QGroupBox { border:1px solid #3a3f47; border-radius:6px; margin-top:10px; padding:8px 6px 6px 6px; font-weight:bold; }
QGroupBox::title { subcontrol-origin: margin; left:10px; padding:0 4px; color:#8fc1ff; }
QLineEdit, QComboBox, QSpinBox { background:#1a1c20; border:1px solid #3a3f47; border-radius:4px; padding:4px 6px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border:1px solid #4d8fe0; }
QComboBox QAbstractItemView { background:#1a1c20; selection-background-color:#35537a; }
QPushButton { background:#353a42; border:1px solid #454b55; border-radius:4px; padding:5px 12px; }
QPushButton:hover { background:#404652; }
QPushButton:pressed { background:#2b2f36; }
QPushButton:disabled { color:#6b7079; background:#2b2e33; }
QPushButton#render { background:#2f7d46; border-color:#3b9658; font-weight:bold; font-size:11pt; padding:8px 18px; }
QPushButton#render:hover { background:#379152; }
QPushButton#stop { background:#a33a3a; border-color:#c04848; font-weight:bold; font-size:11pt; padding:8px 18px; }
QPushButton#stop:hover { background:#bb4444; }
QPushButton#update { background:#2d5b8c; border-color:#3a70aa; }
QPushButton#update:hover { background:#356aa3; }
QTreeWidget { background:#1a1c20; border:1px solid #3a3f47; border-radius:4px; alternate-background-color:#1f2126; }
QTreeWidget::item { padding:2px; }
QTreeWidget::item:selected { background:#35537a; }
QHeaderView::section { background:#2b2f36; border:none; border-right:1px solid #3a3f47; padding:4px; }
QPlainTextEdit { background:#121417; border:1px solid #3a3f47; border-radius:4px; font-family:Consolas,'Courier New'; font-size:9pt; }
QProgressBar { background:#1a1c20; border:1px solid #3a3f47; border-radius:4px; text-align:center; height:16px; }
QProgressBar::chunk { background:#3d8ee0; border-radius:3px; }
QProgressBar#overall::chunk { background:#3b9658; }
QFrame#preview { background:#15171a; border:1px solid #3a3f47; border-radius:6px; }
QFrame#preview QLabel { background:transparent; }
QLabel#now { font-size:13pt; font-weight:bold; color:#f0c050; }
QLabel#title { font-size:14pt; font-weight:bold; color:#8fc1ff; }
QLabel#dim { color:#8a8f98; }
QSplitter::handle { background:#2b2f36; }
QDialog { background:#23262b; }
QFrame#hline { background:#3a3f47; border:none; }
QPushButton#toolbar { background:transparent; border:1px solid transparent; border-radius:4px;
    padding:5px 14px; font-weight:bold; color:#dfe3e8; }
QPushButton#toolbar:hover { background:#353a42; border-color:#454b55; }
QPushButton#toolbar:pressed { background:#2b2f36; }
QPushButton#cfg { background:transparent; border:none; color:#8a8f98; padding:2px 4px; }
QPushButton#cfg:hover { color:#8fc1ff; }
QLabel#author { font-size:13pt; font-weight:bold; color:#f0c050; }

/* ---- O tich / radio: to, vien ro, tich = nen xanh + dau check trang ---- */
QCheckBox, QRadioButton { spacing:8px; }
QCheckBox::indicator, QTreeView::indicator {
    width:16px; height:16px; border:2px solid #9aa3b0; border-radius:4px; background:#121417; }
QCheckBox::indicator:hover, QTreeView::indicator:hover { border-color:#5aa0ff; background:#1b2230; }
QCheckBox::indicator:checked, QTreeView::indicator:checked {
    border-color:#2f80ed; background:#2f80ed; image:url(@UI@/check.svg); }
QCheckBox::indicator:checked:hover, QTreeView::indicator:checked:hover { background:#4a93f5; border-color:#4a93f5; }
QCheckBox::indicator:indeterminate, QTreeView::indicator:indeterminate {
    border-color:#2f80ed; background:#1f4f8f; image:url(@UI@/partial.svg); }
QCheckBox::indicator:disabled, QTreeView::indicator:disabled { border-color:#4a4f57; background:#202226; }
QRadioButton::indicator { width:16px; height:16px; border:2px solid #9aa3b0; border-radius:10px; background:#121417; }
QRadioButton::indicator:hover { border-color:#5aa0ff; }
QRadioButton::indicator:checked { border-color:#2f80ed;
    background:qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 #2f80ed, stop:0.5 #2f80ed, stop:0.6 #121417, stop:1 #121417); }
QRadioButton:checked, QCheckBox:checked { color:#ffffff; }
QRadioButton#mode { font-weight:bold; padding:4px 10px; border:1px solid #3a3f47; border-radius:5px; }
QRadioButton#mode:checked { background:#1f3550; border-color:#2f80ed; }
QTreeView::item { padding:3px 2px; }
"""


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
    result = Signal(dict, str)   # info, error

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
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VERSION}")
        self.resize(1280, 860)
        self.setAcceptDrops(True)

        self.settings = load_settings()
        self.proc = None
        self.proc_mode = None          # "scan" | "render"
        self.proc_buffer = ""
        self.scan_json_path = None
        self.select_json_path = None
        self.scan_data = None
        self.key_to_item = {}
        self.stop_requested = False
        self.render_start = 0.0
        self.item_start = 0.0
        self.done_count = 0
        self.done_secs = []
        self.total = 0
        self.threads = []
        self.finish_info = None
        self.item_remaining = ""
        self.last_paths = {}

        self._build_ui()
        self._load_into_ui()

        self.tick = QTimer(self)
        self.tick.timeout.connect(self._on_tick)
        self.tick.start(1000)

        self.find_blenders()
        if self.settings.get("auto_check_update", True):
            QTimer.singleShot(1500, lambda: self.check_update(silent=True))

    # ------------------------------------------------------------------ UI
    def _btn(self, text, slot=None, obj_name=None, tip=None):
        b = QPushButton(text)
        if obj_name:
            b.setObjectName(obj_name)
        if slot:
            b.clicked.connect(slot)
        if tip:
            b.setToolTip(tip)
        return b

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(10, 8, 10, 8)

        # --- thanh cong cu ngang (tren cung ben trai): Setting | Info
        bar = QHBoxLayout()
        bar.setSpacing(2)
        self.btn_setting = self._btn("⚙  Setting", self.open_settings, "toolbar", "Blender.exe, size ảnh")
        self.btn_info = self._btn("ⓘ  Info", self.open_info, "toolbar", "Thông tin app & Update")
        bar.addWidget(self.btn_setting)
        bar.addWidget(self.btn_info)
        bar.addStretch(1)
        t = QLabel("SCS BATCH RENDER")
        t.setObjectName("title")
        bar.addWidget(t)
        self.lbl_ver = QLabel(f"v{APP_VERSION}")
        self.lbl_ver.setObjectName("dim")
        bar.addWidget(self.lbl_ver)
        main.addLayout(bar)
        line = QFrame()
        line.setObjectName("hline")
        line.setFixedHeight(1)
        main.addWidget(line)

        self._build_settings_dialog()
        self._build_info_dialog()

        # --- paths
        g = QGroupBox("Đường dẫn")
        grid = QGridLayout(g)
        grid.setColumnStretch(1, 1)

        grid.addWidget(QLabel("File .blend:"), 1, 0)
        self.ed_blend = QLineEdit()
        self.ed_blend.setPlaceholderText("Kéo thả file .blend đã setup vào cửa sổ, hoặc bấm Chọn...")
        grid.addWidget(self.ed_blend, 1, 1)
        row = QHBoxLayout()
        row.addWidget(self._btn("Chọn...", self.browse_blend))
        self.btn_scan = self._btn("Quét scene", self.start_scan, tip="Đọc file .blend, liệt kê Scs_N / Icon_N")
        row.addWidget(self.btn_scan)
        grid.addLayout(row, 1, 2)

        grid.addWidget(QLabel("Thư mục lưu ảnh:"), 2, 0)
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Thư mục xuất ảnh PNG")
        grid.addWidget(self.ed_out, 2, 1)
        row = QHBoxLayout()
        row.addWidget(self._btn("Chọn...", self.browse_out))
        row.addWidget(self._btn("Mở", self.open_out))
        grid.addLayout(row, 2, 2)

        opt = QHBoxLayout()
        self.chk_gpu = QCheckBox("Ép dùng GPU (Cycles)")
        opt.addWidget(self.chk_gpu)
        opt.addSpacing(20)
        opt.addWidget(QLabel("Start frame:"))
        self.sp_frame = QSpinBox()
        self.sp_frame.setRange(-100000, 100000)
        self.sp_frame.setValue(2)
        self.sp_frame.setToolTip("Frame của collection số N = Start + (N-1)")
        opt.addWidget(self.sp_frame)
        opt.addStretch(1)
        self.btn_cfg = self._btn("", self.open_settings, "cfg", "Bấm để mở ⚙ Setting")
        opt.addWidget(self.btn_cfg)
        grid.addLayout(opt, 3, 0, 1, 3)
        main.addWidget(g)

        # --- middle: tree | preview
        split = QSplitter(Qt.Vertical)
        mid = QSplitter(Qt.Horizontal)

        left = QGroupBox("Danh sách trong scene")
        lv = QVBoxLayout(left)
        self.lbl_summary = QLabel("Chưa quét scene.")
        self.lbl_summary.setWordWrap(True)
        lv.addWidget(self.lbl_summary)

        mode = QHBoxLayout()
        self.rb_all = QRadioButton("Render tất cả")
        self.rb_checked = QRadioButton("Chỉ render mục được tích")
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_all)
        self.mode_group.addButton(self.rb_checked)
        self.rb_all.setObjectName("mode")
        self.rb_checked.setObjectName("mode")
        self.rb_all.setChecked(True)
        self.rb_all.toggled.connect(self._update_tree_enabled)
        mode.addWidget(self.rb_all)
        mode.addWidget(self.rb_checked)
        mode.addStretch(1)
        lv.addLayout(mode)

        tb = QHBoxLayout()
        tb.addWidget(self._btn("Tích hết", lambda: self.set_all_checked(True)))
        tb.addWidget(self._btn("Bỏ hết", lambda: self.set_all_checked(False)))
        tb.addWidget(self._btn("Chỉ Scs", lambda: self.check_prefix("Scs")))
        tb.addWidget(self._btn("Chỉ Icon", lambda: self.check_prefix("Icon")))
        tb.addWidget(self._btn("Mở rộng/Thu gọn", self.toggle_expand))
        tb.addStretch(1)
        lv.addLayout(tb)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Tên", "Loại", "Trạng thái"])
        self.tree.setAlternatingRowColors(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.itemChanged.connect(self._on_tree_changed)
        self.tree.itemDoubleClicked.connect(self._on_tree_double)
        lv.addWidget(self.tree, 1)
        self.lbl_selected = QLabel("")
        self.lbl_selected.setObjectName("dim")
        lv.addWidget(self.lbl_selected)
        mid.addWidget(left)

        right = QGroupBox("Đang render")
        rv = QVBoxLayout(right)
        frame = QFrame()
        frame.setObjectName("preview")
        fv = QVBoxLayout(frame)
        self.lbl_now = QLabel("— Chưa chạy —")
        self.lbl_now.setObjectName("now")
        self.lbl_now.setWordWrap(True)
        fv.addWidget(self.lbl_now)
        self.lbl_now_info = QLabel("")
        self.lbl_now_info.setObjectName("dim")
        self.lbl_now_info.setWordWrap(True)
        fv.addWidget(self.lbl_now_info)

        fv.addWidget(QLabel("Ảnh hiện tại (sample):"))
        self.pb_item = QProgressBar()
        self.pb_item.setRange(0, 100)
        self.pb_item.setValue(0)
        fv.addWidget(self.pb_item)
        fv.addWidget(QLabel("Tổng:"))
        self.pb_all = QProgressBar()
        self.pb_all.setObjectName("overall")
        self.pb_all.setRange(0, 1)
        self.pb_all.setValue(0)
        self.pb_all.setFormat("%v / %m")
        fv.addWidget(self.pb_all)
        self.lbl_time = QLabel("")
        self.lbl_time.setObjectName("dim")
        fv.addWidget(self.lbl_time)

        fv.addWidget(QLabel("Ảnh vừa xong:"))
        self.img = QLabel("(chưa có)")
        self.img.setAlignment(Qt.AlignCenter)
        self.img.setMinimumSize(300, 220)
        self.img.setStyleSheet("background:#0e0f11; border:1px solid #3a3f47; border-radius:4px;")
        self.img.setCursor(Qt.PointingHandCursor)
        self.img.mousePressEvent = lambda e: self.open_last_image()
        fv.addWidget(self.img, 1)
        self.lbl_img = QLabel("")
        self.lbl_img.setObjectName("dim")
        self.lbl_img.setWordWrap(True)
        fv.addWidget(self.lbl_img)
        rv.addWidget(frame)
        mid.addWidget(right)
        mid.setSizes([700, 420])
        split.addWidget(mid)

        logbox = QGroupBox("Log")
        lb = QVBoxLayout(logbox)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(30000)
        lb.addWidget(self.log)
        lrow = QHBoxLayout()
        self.chk_verbose = QCheckBox("Hiện cả dòng sample của Blender")
        lrow.addWidget(self.chk_verbose)
        lrow.addStretch(1)
        lrow.addWidget(self._btn("Lưu log...", self.save_log))
        lrow.addWidget(self._btn("Xóa log", self.log.clear))
        lb.addLayout(lrow)
        split.addWidget(logbox)
        split.setSizes([520, 260])
        main.addWidget(split, 1)

        # --- bottom buttons
        bot = QHBoxLayout()
        self.lbl_status = QLabel("Sẵn sàng.")
        bot.addWidget(self.lbl_status, 1)
        self.btn_render = self._btn("▶  RENDER", self.start_render, "render")
        self.btn_stop = self._btn("■  DỪNG NGAY", self.stop_now, "stop")
        self.btn_stop.setEnabled(False)
        bot.addWidget(self.btn_render)
        bot.addWidget(self.btn_stop)
        main.addLayout(bot)

        self.last_image = None

    # ------------------------------------------------------------------ popups
    def _size_spin(self, val):
        sp = QSpinBox()
        sp.setRange(16, 16384)
        sp.setSingleStep(2)
        sp.setValue(val)
        sp.setSuffix(" px")
        sp.setMinimumWidth(110)
        sp.valueChanged.connect(self._on_size_changed)
        return sp

    def _build_settings_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("⚙  Setting")
        dlg.setMinimumWidth(720)
        v = QVBoxLayout(dlg)
        v.setSpacing(10)

        gb = QGroupBox("Blender.exe")
        gl = QGridLayout(gb)
        gl.setColumnStretch(0, 1)
        self.cmb_blender = QComboBox()
        self.cmb_blender.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_blender.setToolTip("Tự động dò các bản Blender trong máy (registry, Program Files, Steam, PATH...)")
        self.cmb_blender.currentIndexChanged.connect(lambda *_: self._refresh_cfg_label())
        gl.addWidget(self.cmb_blender, 0, 0)
        self.btn_find = self._btn("Dò lại", self.find_blenders)
        gl.addWidget(self.btn_find, 0, 1)
        gl.addWidget(self._btn("Chọn...", self.browse_blender), 0, 2)
        hint = QLabel("App tự dò Blender trong máy (registry, Program Files, Steam, PATH...). "
                      "Danh sách xếp bản mới nhất lên đầu; bấm Chọn... nếu không thấy bản bạn cần.")
        hint.setObjectName("dim")
        hint.setWordWrap(True)
        gl.addWidget(hint, 1, 0, 1, 3)
        v.addWidget(gb)

        gs = QGroupBox("Size ảnh xuất ra")
        g = QGridLayout(gs)
        g.addWidget(QLabel("Scs_N:"), 0, 0)
        self.sp_scs_w = self._size_spin(DEFAULT_RES["Scs"][0])
        self.sp_scs_h = self._size_spin(DEFAULT_RES["Scs"][1])
        g.addWidget(self.sp_scs_w, 0, 1)
        g.addWidget(QLabel("×"), 0, 2)
        g.addWidget(self.sp_scs_h, 0, 3)
        g.addWidget(QLabel("Icon_N:"), 1, 0)
        self.sp_icon_w = self._size_spin(DEFAULT_RES["Icon"][0])
        self.sp_icon_h = self._size_spin(DEFAULT_RES["Icon"][1])
        g.addWidget(self.sp_icon_w, 1, 1)
        g.addWidget(QLabel("×"), 1, 2)
        g.addWidget(self.sp_icon_h, 1, 3)
        g.addWidget(QLabel("Độ phân giải:"), 2, 0)
        self.sp_percent = QSpinBox()
        self.sp_percent.setRange(1, 100)
        self.sp_percent.setValue(100)
        self.sp_percent.setSuffix(" %")
        self.sp_percent.setToolTip("100% = đúng size ở trên. Đặt 10-25% để render thử nhanh.")
        self.sp_percent.valueChanged.connect(self._on_size_changed)
        g.addWidget(self.sp_percent, 2, 1)
        self.lbl_size_preview = QLabel("")
        self.lbl_size_preview.setObjectName("dim")
        g.addWidget(self.lbl_size_preview, 2, 2, 1, 3)
        g.addWidget(self._btn("Về mặc định", self.reset_sizes, tip="Scs 2796×2048, Icon 2048×2048, 100%"), 0, 4)
        g.setColumnStretch(5, 1)
        v.addWidget(gs)

        v.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText("Đóng")
        bb.rejected.connect(dlg.close)
        v.addWidget(bb)
        dlg.finished.connect(lambda *_: save_settings(self._collect_settings()))
        self.dlg_settings = dlg

    def _build_info_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("ⓘ  Info")
        dlg.setMinimumWidth(480)
        v = QVBoxLayout(dlg)
        v.setSpacing(8)

        t = QLabel("SCS BATCH RENDER")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)
        ver = QLabel(f"Phiên bản v{APP_VERSION}")
        ver.setObjectName("dim")
        ver.setAlignment(Qt.AlignCenter)
        v.addWidget(ver)

        gi = QGroupBox("Thông tin")
        gl = QGridLayout(gi)
        gl.setColumnStretch(1, 1)
        gl.addWidget(QLabel("Người làm app:"), 0, 0)
        au = QLabel(APP_AUTHOR)
        au.setObjectName("author")
        gl.addWidget(au, 0, 1)
        gl.addWidget(QLabel("Chức năng:"), 1, 0)
        desc = QLabel("Render hàng loạt ảnh Icon / SCS (Scs_N, Icon_N, Map, Custom) "
                      "từ file Blender đã setup, chạy Blender ở chế độ nền.")
        desc.setWordWrap(True)
        gl.addWidget(desc, 1, 1)
        gl.addWidget(QLabel("GitHub:"), 2, 0)
        link = QLabel(f'<a style="color:#8fc1ff" href="{updater.REPO_URL}">{updater.REPO_URL}</a>')
        link.setOpenExternalLinks(True)
        gl.addWidget(link, 2, 1)
        v.addWidget(gi)

        gu = QGroupBox("Update")
        ul = QVBoxLayout(gu)
        self.lbl_update_status = QLabel(f"Đang dùng v{APP_VERSION}. Chưa kiểm tra bản mới.")
        self.lbl_update_status.setWordWrap(True)
        ul.addWidget(self.lbl_update_status)
        row = QHBoxLayout()
        self.btn_update = self._btn("⟳  Kiểm tra update", lambda: self.check_update(silent=False), "update",
                                    f"Kiểm tra & cập nhật từ {updater.RELEASES_URL}")
        row.addWidget(self.btn_update)
        rel = QLabel(f'<a style="color:#8fc1ff" href="{updater.RELEASES_URL}">Xem các bản phát hành</a>')
        rel.setOpenExternalLinks(True)
        row.addWidget(rel)
        row.addStretch(1)
        ul.addLayout(row)
        self.chk_auto_update = QCheckBox("Tự kiểm tra update khi mở app")
        ul.addWidget(self.chk_auto_update)
        v.addWidget(gu)

        foot = QLabel(f"© {time.strftime('%Y')} {APP_AUTHOR}")
        foot.setObjectName("dim")
        foot.setAlignment(Qt.AlignCenter)
        v.addWidget(foot)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText("Đóng")
        bb.rejected.connect(dlg.close)
        v.addWidget(bb)
        dlg.finished.connect(lambda *_: save_settings(self._collect_settings()))
        self.dlg_info = dlg

    def _popup(self, dlg):
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def open_settings(self):
        self._popup(self.dlg_settings)

    def open_info(self):
        self._popup(self.dlg_info)

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
        p = self.sp_percent.value() / 100.0
        sw, sh = self.res_for("Scs")
        iw, ih = self.res_for("Icon")
        if hasattr(self, "lbl_size_preview"):
            self.lbl_size_preview.setText(f"→ thực tế: Scs {int(sw * p)}×{int(sh * p)}, Icon {int(iw * p)}×{int(ih * p)}")
        self._refresh_tree_res()
        self._refresh_cfg_label()

    def _refresh_cfg_label(self):
        if not hasattr(self, "btn_cfg"):
            return
        txt = self.cmb_blender.currentText()
        short = txt.split("  -  ")[0] if "  -  " in txt else (os.path.basename(txt) if txt else "")
        if not self.blender_exe():
            short = "⚠ chưa có blender.exe"
        sw, sh = self.res_for("Scs")
        iw, ih = self.res_for("Icon")
        pct = self.sp_percent.value()
        self.btn_cfg.setText(f"{short}   |   Scs {sw}×{sh}   |   Icon {iw}×{ih}"
                             + (f"   |   {pct}%" if pct != 100 else "") + "   ⚙")

    def _refresh_tree_res(self):
        if not hasattr(self, "tree"):
            return
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            d = top.data(0, Qt.UserRole) or {}
            res = self.res_for(d.get("prefix"))
            if res and "frame" in d:
                top.setText(1, f"{res[0]}×{res[1]}  F{d['frame']}")
        self.tree.blockSignals(False)

    def _res_args(self):
        sw, sh = self.res_for("Scs")
        iw, ih = self.res_for("Icon")
        return ["--scs-res", f"{sw}x{sh}", "--icon-res", f"{iw}x{ih}"]

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
        self._on_size_changed()
        self.chk_auto_update.setChecked(s.get("auto_check_update", True))
        (self.rb_checked if s.get("mode") == "checked" else self.rb_all).setChecked(True)
        if s.get("blender_exe") and os.path.isfile(s["blender_exe"]):
            self._add_blender_item(s["blender_exe"], f"{s['blender_exe']}", select=True)
        self._update_tree_enabled()

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
        if self.proc and self.proc.state() != QProcess.NotRunning:
            r = QMessageBox.question(self, APP_NAME, "Blender đang chạy. Dừng và thoát?")
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
        path, _ = QFileDialog.getSaveFileName(self, "Lưu log", os.path.join(self.ed_out.text() or APP_DIR,
                                              f"render_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"), "Text (*.txt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log.toPlainText())

    # ------------------------------------------------------------------ blender exe
    def blender_exe(self):
        d = self.cmb_blender.currentData()
        return d or ""

    def _add_blender_item(self, path, label, select=False):
        for i in range(self.cmb_blender.count()):
            if os.path.normcase(self.cmb_blender.itemData(i) or "") == os.path.normcase(path):
                if label and label != path:
                    self.cmb_blender.setItemText(i, label)
                if select:
                    self.cmb_blender.setCurrentIndex(i)
                return
        self.cmb_blender.addItem(label or path, path)
        if select:
            self.cmb_blender.setCurrentIndex(self.cmb_blender.count() - 1)

    def find_blenders(self):
        self.btn_find.setEnabled(False)
        self.btn_find.setText("Đang dò...")
        self.write_log("Đang tự dò Blender trong máy...")
        th = FindBlenderThread()
        th.found.connect(self._on_blenders_found)
        th.finished.connect(lambda: self.threads.remove(th) if th in self.threads else None)
        self.threads.append(th)
        th.start()

    def _on_blenders_found(self, items):
        self.btn_find.setEnabled(True)
        self.btn_find.setText("Dò lại")
        keep = self.blender_exe() or self.settings.get("blender_exe", "")
        for b in items:
            self._add_blender_item(b["path"], b["label"])
        if items:
            self.write_log(f"Tìm thấy {len(items)} bản Blender:")
            for b in items:
                self.write_log("   " + b["label"])
        else:
            self.write_log("!!! Không tự tìm thấy blender.exe — bấm 'Chọn...' để chỉ đường dẫn.")
        # Giu lua chon cu neu con ton tai, neu khong chon ban moi nhat
        if keep and os.path.isfile(keep):
            self._add_blender_item(keep, "", select=True)
        elif items:
            self._add_blender_item(items[0]["path"], items[0]["label"], select=True)

    def browse_blender(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn blender.exe", "", "blender.exe (blender.exe);;Exe (*.exe)")
        if path:
            path = os.path.abspath(path)
            v = blender_finder.get_blender_version(path)
            label = (f"Blender {'.'.join(map(str, v))}  -  " if v else "") + path
            self._add_blender_item(path, label, select=True)

    # ------------------------------------------------------------------ paths
    def browse_blend(self):
        start = os.path.dirname(self.ed_blend.text()) if self.ed_blend.text() else ""
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file .blend", start, "Blender (*.blend)")
        if path:
            self.set_blend(path)

    def set_blend(self, path):
        self._remember_unchecked()
        self.ed_blend.setText(os.path.abspath(path))
        if not self.ed_out.text().strip():
            self.ed_out.setText(os.path.join(os.path.dirname(path), "Render"))
        self.start_scan()

    def browse_out(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu ảnh", self.ed_out.text())
        if d:
            self.ed_out.setText(os.path.abspath(d))

    def open_out(self):
        d = self.ed_out.text().strip()
        if d and os.path.isdir(d):
            QDesktopServices.openUrl(QUrl.fromLocalFile(d))

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
            QMessageBox.warning(self, APP_NAME, "Chưa có blender.exe hợp lệ.\nHãy chọn trong ⚙ Setting.")
            self.open_settings()
            return None
        if not blend or not os.path.isfile(blend):
            QMessageBox.warning(self, APP_NAME, "Chưa chọn file .blend (hoặc file không tồn tại).")
            return None
        if need_out and not out:
            QMessageBox.warning(self, APP_NAME, "Chưa chọn thư mục lưu ảnh.")
            return None
        if not os.path.isfile(CORE_SCRIPT):
            QMessageBox.critical(self, APP_NAME, f"Thiếu file {CORE_SCRIPT}. Hãy bấm Update online.")
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
            self.write_log("!!! Không chạy được Blender (sai đường dẫn hoặc bị chặn).")
            self._set_running(False)

    def _on_output(self):
        data = bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self.proc_buffer += data.replace("\r\n", "\n").replace("\r", "\n")
        while "\n" in self.proc_buffer:
            line, self.proc_buffer = self.proc_buffer.split("\n", 1)
            self._handle_line(line)

    RE_SAMPLE = re.compile(r"Sample (\d+)/(\d+)")
    RE_REMAIN = re.compile(r"Remaining:\s*([\d:.]+)")

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
            self.pb_item.setRange(0, max(1, tot))
            self.pb_item.setValue(cur)
            self.pb_item.setFormat(f"Sample {cur}/{tot}")
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
            self.pb_all.setRange(0, max(1, self.total))
            self.pb_all.setValue(0)
        elif ev == "item":
            self.item_start = time.time()
            self.item_remaining = ""
            self.pb_item.setRange(0, 100)
            self.pb_item.setValue(0)
            self.pb_item.setFormat("Đang chuẩn bị...")
            self.lbl_now.setText(f"[{d['i']}/{d['total']}]  {d['collection']}  ›  {d['label']}")
            res = d.get("res") or ["?", "?"]
            self.lbl_now_info.setText(f"Resolution {res[0]}×{res[1]}  |  Frame {d.get('frame')}\n"
                                      f"→ {os.path.basename(d.get('path', ''))}")
            self.lbl_status.setText(f"Đang render {d['i']}/{d['total']}: {d['collection']} › {d['label']}")
            self._mark_item(d["key"], "Đang render...", C_RENDERING, scroll=True)
        elif ev == "done":
            self.done_count += 1
            self.done_secs.append(d.get("sec", 0))
            self.pb_all.setValue(self.done_count)
            self.pb_item.setValue(self.pb_item.maximum())
            self._mark_item(d["key"], f"Xong ({d.get('sec', 0)}s)", C_DONE)
            self.last_paths[d["key"]] = d.get("path")
            self.show_image(d.get("path"))
        elif ev == "error":
            self.done_count += 1
            self.pb_all.setValue(self.done_count)
            self._mark_item(d["key"], "LỖI", C_ERROR)
            self.write_log(f"!!! LỖI {d.get('key')}: {d.get('msg')}")
        elif ev == "finish":
            self.finish_info = d
        elif ev == "scan_done":
            pass

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
        txt = f"Tổng thời gian: {human_time(el)}   |   Ảnh này: {human_time(it)}"
        if getattr(self, "item_remaining", ""):
            txt += f" (còn ~{self.item_remaining})"
        if self.done_secs and self.total:
            avg = sum(self.done_secs) / len(self.done_secs)
            txt += f"\nTrung bình {avg:.1f}s/ảnh  |  Ước tính còn: {human_time(avg * (self.total - self.done_count))}"
        self.lbl_time.setText(txt)

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
            if self.stop_requested:
                self.lbl_now.setText("■ ĐÃ DỪNG")
                self.lbl_status.setText(f"Đã dừng sau {el}. Xong {self.done_count}/{self.total}.")
                self.write_log(f"\n=== ĐÃ DỪNG theo yêu cầu | {self.done_count}/{self.total} ảnh | {el} ===")
                for key, it in self.key_to_item.items():
                    if it.text(2) == "Đang render...":
                        self._mark_item(key, "Đã dừng", C_ERROR)
            else:
                fi = getattr(self, "finish_info", None) or {}
                ok, fail = fi.get("ok", self.done_count), fi.get("fail", 0)
                self.lbl_now.setText("✔ HOÀN TẤT" if not fail and code in (0, 2) and fi else "Kết thúc")
                msg = f"Hoàn tất: {ok} OK, {fail} lỗi, tổng {el}."
                if not fi:
                    msg = f"Blender thoát (code {code}) trước khi xong — xem log."
                self.lbl_status.setText(msg)
                self.write_log("\n=== " + msg + " ===")
                QApplication.alert(self)
            self.pb_item.setFormat("")
        self._cleanup_temp()

    def _cleanup_temp(self):
        for p in (self.select_json_path,):
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
        self.write_log("\n>>> DỪNG NGAY - đang kill Blender...")
        pid = self.proc.processId()
        kill_tree(pid)
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
        self.lbl_summary.setText("Đang quét scene (Blender đang mở file, có thể mất vài giây)...")
        self.lbl_status.setText("Đang quét scene...")
        self.write_log(f"\n=== QUÉT SCENE: {blend} ===")
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
            self.lbl_summary.setText("Quét thất bại — xem log.")
            self.lbl_status.setText(f"Quét lỗi (code {code}).")
            return
        self.scan_data = data
        self.populate_tree(data)
        self.lbl_status.setText("Quét xong.")

    def populate_tree(self, data):
        self.tree.blockSignals(True)
        self.tree.clear()
        self.key_to_item = {}
        unchecked = set(self.settings.get("unchecked", {}).get(self._blend_key(), []))

        n_scs = n_icon = img_scs = img_icon = 0
        for c in data.get("collections", []):
            res = self.res_for(c["prefix"]) or c["resolution"]
            top = QTreeWidgetItem([f"{c['name']}", f"{res[0]}×{res[1]}  F{c['frame']}",
                                   f"{len(c['items'])} ảnh"])
            top.setFlags(top.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            top.setData(0, Qt.UserRole, {"kind": "col", "prefix": c["prefix"], "name": c["name"],
                                         "frame": c["frame"]})
            f = top.font(0)
            f.setBold(True)
            top.setFont(0, f)
            self.tree.addTopLevelItem(top)
            for i in c["items"]:
                ch = QTreeWidgetItem([i["label"], {"map": "Map", "map_event": "Map event",
                                                   "object": "Object"}.get(i["type"], i["type"]), ""])
                ch.setFlags(ch.flags() | Qt.ItemIsUserCheckable)
                ch.setData(0, Qt.UserRole, {"kind": "item", "key": i["key"], "prefix": c["prefix"]})
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
            top = QTreeWidgetItem(["Custom (scs_render_separate)", "frame gốc", f"{len(custom)} ảnh"])
            top.setFlags(top.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            top.setData(0, Qt.UserRole, {"kind": "col", "prefix": "Custom", "name": "Custom"})
            self.tree.addTopLevelItem(top)
            for i in custom:
                ch = QTreeWidgetItem([i["label"], f"Custom ({i.get('collection', '')})", ""])
                ch.setFlags(ch.flags() | Qt.ItemIsUserCheckable)
                ch.setData(0, Qt.UserRole, {"kind": "item", "key": i["key"], "prefix": "Custom"})
                ch.setCheckState(0, Qt.Unchecked if i["key"] in unchecked else Qt.Checked)
                top.addChild(ch)
                self.key_to_item[i["key"]] = ch

        if len(self.key_to_item) < 80:
            self.tree.expandAll()
        self.tree.blockSignals(False)
        self._refresh_check_colors()

        warn = []
        if not data.get("has_setup"):
            warn.append("⚠ không có collection 'Setup'")
        if data.get("engine") != "CYCLES":
            warn.append(f"⚠ engine = {data.get('engine')} (GPU chỉ áp dụng cho Cycles)")
        total = img_scs + img_icon + len(custom)
        self.lbl_summary.setText(
            f"<b>Scs:</b> {n_scs} collection ({img_scs} ảnh) &nbsp;&nbsp; "
            f"<b>Icon:</b> {n_icon} collection ({img_icon} ảnh) &nbsp;&nbsp; "
            f"<b>Custom:</b> {len(custom)} &nbsp;&nbsp; <b>Tổng:</b> {total} ảnh"
            f"<br><span style='color:#8a8f98'>Scene '{data.get('scene')}' | Map: "
            f"{'có' if data.get('has_map') else 'không'}</span>"
            + ("<br><span style='color:#f0c050'>" + " | ".join(warn) + "</span>" if warn else ""))
        self.write_log(f"Quét xong: Scs {n_scs} ({img_scs} ảnh), Icon {n_icon} ({img_icon} ảnh), "
                       f"Custom {len(custom)}, tổng {total} ảnh.")
        self._update_selected_label()
        self._update_tree_enabled()

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
            self._update_selected_label()

    def _refresh_check_colors(self):
        """Muc duoc tich: chu sang; khong tich: chu mo -> nhin la biet ngay."""
        self.tree.blockSignals(True)
        for it in self.key_to_item.values():
            on = it.checkState(0) == Qt.Checked
            col = C_ON if on else C_DIM
            it.setForeground(0, QBrush(col))
            it.setForeground(1, QBrush(col))
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            st = top.checkState(0)
            top.setForeground(0, QBrush(C_ON if st == Qt.Checked else C_PART if st == Qt.PartiallyChecked else C_DIM))
        self.tree.blockSignals(False)

    def _on_tree_double(self, item, col):
        d = item.data(0, Qt.UserRole) or {}
        p = self.last_paths.get(d.get("key")) if d.get("kind") == "item" else None
        if p and os.path.isfile(p):
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _update_selected_label(self):
        n = len(self.checked_keys())
        self.lbl_selected.setText(f"Đang tích: {n}/{len(self.key_to_item)} ảnh")

    def _update_tree_enabled(self):
        only = self.rb_checked.isChecked()
        self.tree.setEnabled(True)
        self.lbl_selected.setVisible(only)

    def set_all_checked(self, state):
        self.tree.blockSignals(True)
        for it in self.key_to_item.values():
            it.setCheckState(0, Qt.Checked if state else Qt.Unchecked)
        self.tree.blockSignals(False)
        self._refresh_check_colors()
        self._update_selected_label()

    def check_prefix(self, prefix):
        self.tree.blockSignals(True)
        for it in self.key_to_item.values():
            p = (it.data(0, Qt.UserRole) or {}).get("prefix")
            it.setCheckState(0, Qt.Checked if p == prefix else Qt.Unchecked)
        self.tree.blockSignals(False)
        self._refresh_check_colors()
        self._update_selected_label()
        self.rb_checked.setChecked(True)

    def toggle_expand(self):
        any_open = any(self.tree.topLevelItem(i).isExpanded() for i in range(self.tree.topLevelItemCount()))
        self.tree.collapseAll() if any_open else self.tree.expandAll()

    # ------------------------------------------------------------------ render
    def start_render(self):
        if self._busy():
            return
        r = self._check_inputs()
        if not r:
            return
        exe, blend, out = r
        only_checked = self.rb_checked.isChecked()
        if only_checked:
            if not self.key_to_item:
                QMessageBox.information(self, APP_NAME, "Hãy 'Quét scene' trước để chọn mục cần render.")
                return
            keys = self.checked_keys()
            if not keys:
                QMessageBox.information(self, APP_NAME, "Chưa tích mục nào.")
                return
        os.makedirs(out, exist_ok=True)
        self._remember_unchecked()
        save_settings(self._collect_settings())

        # reset trang thai tree + preview
        for key in self.key_to_item:
            self._mark_item(key, "", QColor("#dfe3e8"))
        self.done_count = 0
        self.done_secs = []
        self.total = 0
        self.finish_info = None
        self.item_start = 0
        self.render_start = time.time()
        self.pb_all.setRange(0, 1)
        self.pb_all.setValue(0)
        self.lbl_now.setText("Đang khởi động Blender...")
        self.lbl_now_info.setText("Lần đầu có thể mất vài phút để biên dịch shader / load scene lên GPU.")

        args = ["--background", blend, "--python", CORE_SCRIPT, "--python-exit-code", "1", "--",
                "--output", out, "--start-frame", str(self.sp_frame.value()),
                "--percent", str(self.sp_percent.value())] + self._res_args()
        if self.sp_percent.value() < 100:
            self.write_log(f"!!! Lưu ý: đang render ở {self.sp_percent.value()}% độ phân giải (render thử).")
        if self.chk_gpu.isChecked():
            args.append("--gpu")
        if only_checked:
            fd, self.select_json_path = tempfile.mkstemp(prefix="scs_select_", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(keys, f, ensure_ascii=False)
            args += ["--select", self.select_json_path]
            self.write_log(f"\n=== RENDER {len(keys)} MỤC ĐƯỢC TÍCH ===")
        else:
            self.write_log("\n=== RENDER TẤT CẢ ===")
        self._start_process(exe, args, "render")

    # ------------------------------------------------------------------ preview image
    def show_image(self, path):
        if not path or not os.path.isfile(path):
            return
        pm = QPixmap(path)
        if pm.isNull():
            return
        self.last_image = path
        self.img.setPixmap(pm.scaled(self.img.width() - 6, self.img.height() - 6,
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.lbl_img.setText(f"{os.path.basename(path)}  ({pm.width()}×{pm.height()}) — bấm để mở")

    def open_last_image(self):
        if self.last_image and os.path.isfile(self.last_image):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_image))

    # ------------------------------------------------------------------ update
    def check_update(self, silent=False):
        if self._busy():
            return
        self.btn_update.setEnabled(False)
        self.btn_update.setText("Đang kiểm tra...")
        th = UpdateCheckThread()
        th.result.connect(lambda info, err: self._on_update_checked(info, err, silent))
        th.finished.connect(lambda: self.threads.remove(th) if th in self.threads else None)
        self.threads.append(th)
        th.start()

    def _on_update_checked(self, info, err, silent):
        self.btn_update.setEnabled(not self._busy())
        self.btn_update.setText("⟳  Kiểm tra update")
        if err:
            if not silent:
                QMessageBox.warning(self, "Update", f"Không kiểm tra được update:\n{err}")
            self.write_log(f"[update] lỗi: {err}")
            self.lbl_update_status.setText(f"Đang dùng v{APP_VERSION}. Không kiểm tra được: {err}")
            return
        lver = updater.local_version()
        rver = info.get("version") or "?"
        self.lbl_update_status.setText(
            f"Đang dùng v{lver}. Bản mới nhất trên GitHub: {info.get('tag')} ({info.get('date', '')}).")
        if not updater.is_newer(info, lver):
            self.btn_info.setText("ⓘ  Info")
            self.write_log(f"[update] Đang dùng bản mới nhất (v{lver}, release mới nhất: {info.get('tag')}).")
            if not silent:
                QMessageBox.information(self, "Update", f"Bạn đang dùng bản mới nhất (v{lver}).")
            return
        self.btn_info.setText("ⓘ  Info  ●")
        self.btn_info.setToolTip(f"Có bản mới {info.get('tag')} — mở Info để update")
        self.lbl_update_status.setText(f"<b style='color:#6fd36f'>Có bản mới {info.get('tag')}</b> "
                                       f"({info.get('date', '')}). Đang dùng v{lver}.")
        notes = info.get("notes", "")
        if len(notes) > 900:
            notes = notes[:900] + "..."
        msg = (f"Có bản mới: {info.get('name')}  ({info.get('date', '')})\n"
               f"Hiện tại: v{lver}  →  Mới: v{rver}\n\n{notes}\n\n"
               f"Cập nhật ngay? (App sẽ tự khởi động lại)")
        if QMessageBox.question(self, "Update", msg) != QMessageBox.Yes:
            return
        self.btn_update.setEnabled(False)
        self.btn_update.setText("Đang tải...")
        th = UpdateInstallThread(info)
        th.log.connect(lambda s: self.write_log("[update] " + s))
        th.done.connect(self._on_update_installed)
        th.finished.connect(lambda: self.threads.remove(th) if th in self.threads else None)
        self.threads.append(th)
        th.start()

    def _on_update_installed(self, ok, err):
        self.btn_update.setEnabled(True)
        self.btn_update.setText("⟳  Kiểm tra update")
        if not ok:
            QMessageBox.critical(self, "Update", f"Cập nhật thất bại:\n{err}")
            return
        QMessageBox.information(self, "Update", "Cập nhật xong. App sẽ khởi động lại.")
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
    app.setStyleSheet(build_style())
    ico = os.path.join(APP_DIR, "icon.ico")
    if os.path.isfile(ico):
        app.setWindowIcon(QIcon(ico))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
