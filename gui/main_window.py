"""
메인 GUI 윈도우 (PyQt5)
상품 대량등록 솔루션의 메인 화면
"""
import os
import sys
import shutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QGroupBox, QMessageBox,
    QAbstractItemView, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.excel_reader import read_excel, get_valid_products
from core.uploader import Uploader
from gui.settings_window import SettingsWindow

from api.smartstore import SmartStoreClient
from api.coupang import CoupangClient
from api.st11 import St11Client
from api.gmarket import GmarketClient
from api.auction import AuctionClient


# ── 색상 팔레트 ──────────────────────────────
COLOR_HEADER     = "#2C3E50"
COLOR_BG         = "#F5F5F5"
COLOR_WHITE      = "#FFFFFF"
COLOR_TEXT       = "#2C3E50"
COLOR_SUCCESS    = "#27AE60"
COLOR_ERROR      = "#E74C3C"
COLOR_WARNING    = "#F39C12"
COLOR_LOG_BG     = "#1E1E1E"
COLOR_LOG_FG     = "#D4D4D4"
COLOR_BORDER     = "#DDE1E7"
COLOR_BTN_PRIMARY   = "#2C3E50"
COLOR_BTN_DANGER    = "#E74C3C"
COLOR_BTN_SECONDARY = "#7F8C8D"

PLATFORMS = ["스마트스토어", "쿠팡", "11번가", "지마켓", "옥션"]

# ── 스타일시트 ───────────────────────────────
QSS = f"""
QMainWindow, QWidget#central {{
    background-color: {COLOR_BG};
}}
QGroupBox {{
    font-family: '맑은 고딕';
    font-size: 10px;
    font-weight: bold;
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    margin-top: 10px;
    padding: 8px;
    background-color: {COLOR_WHITE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT};
}}
QPushButton {{
    font-family: '맑은 고딕';
    font-size: 10px;
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
}}
QPushButton#btn_primary {{
    background-color: {COLOR_BTN_PRIMARY};
    color: white;
    border: none;
}}
QPushButton#btn_primary:hover {{
    background-color: #3D5166;
}}
QPushButton#btn_primary:disabled {{
    background-color: #95A5A6;
}}
QPushButton#btn_danger {{
    background-color: {COLOR_BTN_DANGER};
    color: white;
    border: none;
}}
QPushButton#btn_danger:hover {{
    background-color: #C0392B;
}}
QPushButton#btn_danger:disabled {{
    background-color: #BDC3C7;
}}
QPushButton#btn_secondary {{
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
}}
QPushButton#btn_secondary:hover {{
    background-color: #ECF0F1;
}}
QTableWidget {{
    font-family: '맑은 고딕';
    font-size: 9px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    gridline-color: {COLOR_BORDER};
    background-color: {COLOR_WHITE};
    selection-background-color: #D6EAF8;
    selection-color: {COLOR_TEXT};
}}
QTableWidget QHeaderView::section {{
    background-color: {COLOR_HEADER};
    color: white;
    font-family: '맑은 고딕';
    font-size: 9px;
    font-weight: bold;
    padding: 5px;
    border: none;
}}
QProgressBar {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: #ECF0F1;
    height: 18px;
    text-align: center;
    font-family: '맑은 고딕';
    font-size: 9px;
    color: {COLOR_TEXT};
}}
QProgressBar::chunk {{
    background-color: {COLOR_SUCCESS};
    border-radius: 3px;
}}
QCheckBox {{
    font-family: '맑은 고딕';
    font-size: 10px;
    color: {COLOR_TEXT};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {COLOR_BORDER};
    border-radius: 3px;
    background-color: white;
}}
QCheckBox::indicator:checked {{
    background-color: {COLOR_BTN_PRIMARY};
    border-color: {COLOR_BTN_PRIMARY};
}}
QLabel {{
    font-family: '맑은 고딕';
    color: {COLOR_TEXT};
}}
QLineEdit {{
    font-family: '맑은 고딕';
    font-size: 10px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT};
}}
QLineEdit:focus {{
    border-color: {COLOR_BTN_PRIMARY};
}}
QLineEdit:read-only {{
    background-color: #F8F9FA;
    color: #6C757D;
}}
"""


# ── 업로드 워커 스레드 ────────────────────────
class UploadWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, uploader: Uploader, products, platforms):
        super().__init__()
        self.uploader = uploader
        self.products = products
        self.platforms = platforms

    def run(self):
        self.uploader.upload(
            products=self.products,
            platforms=self.platforms,
            on_progress=lambda msg: self.progress.emit(msg),
            on_complete=lambda results: self.finished.emit(self.uploader.get_summary()),
        )


# ── 메인 윈도우 ──────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("상품 대량등록 솔루션 v1.0")
        self.setMinimumSize(900, 720)
        self.resize(960, 780)
        self.setStyleSheet(QSS)

        self.uploader = Uploader()
        self.products = []
        self.worker = None

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        body = QWidget()
        body.setObjectName("central")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 14, 16, 14)
        body_layout.setSpacing(10)

        body_layout.addWidget(self._build_file_section())
        body_layout.addWidget(self._build_platform_section())
        body_layout.addWidget(self._build_preview_section())
        body_layout.addWidget(self._build_log_section(), stretch=1)
        body_layout.addWidget(self._build_button_bar())

        layout.addWidget(body)
        self._apply_clients()

    # ── UI 빌더 ─────────────────────────────

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {COLOR_HEADER};")

        layout = QVBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(2)

        title = QLabel("상품 대량등록 솔루션")
        title.setFont(QFont("맑은 고딕", 16, QFont.Bold))
        title.setStyleSheet("color: white;")

        subtitle = QLabel("스마트스토어  |  쿠팡  |  11번가  |  지마켓  |  옥션")
        subtitle.setFont(QFont("맑은 고딕", 9))
        subtitle.setStyleSheet("color: #BDC3C7;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return header

    def _build_file_section(self) -> QGroupBox:
        box = QGroupBox("1.  엑셀 파일 선택")
        layout = QHBoxLayout(box)
        layout.setSpacing(8)

        from PyQt5.QtWidgets import QLineEdit
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText("엑셀 파일을 선택하세요 (.xlsx)")

        btn_select = QPushButton("파일 선택")
        btn_select.setObjectName("btn_primary")
        btn_select.setFixedWidth(90)
        btn_select.clicked.connect(self._select_file)

        btn_template = QPushButton("템플릿 저장")
        btn_template.setObjectName("btn_secondary")
        btn_template.setFixedWidth(90)
        btn_template.clicked.connect(self._save_template)

        layout.addWidget(self.file_edit)
        layout.addWidget(btn_select)
        layout.addWidget(btn_template)
        return box

    def _build_platform_section(self) -> QGroupBox:
        box = QGroupBox("2.  등록할 쇼핑몰 선택")
        layout = QHBoxLayout(box)
        layout.setSpacing(16)

        self.platform_checks = {}
        for platform in PLATFORMS:
            cb = QCheckBox(platform)
            cb.setChecked(True)
            self.platform_checks[platform] = cb
            layout.addWidget(cb)

        layout.addStretch()

        btn_settings = QPushButton("⚙  API 키 설정")
        btn_settings.setObjectName("btn_secondary")
        btn_settings.setFixedWidth(110)
        btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(btn_settings)
        return box

    def _build_preview_section(self) -> QGroupBox:
        box = QGroupBox("3.  상품 미리보기")
        layout = QVBoxLayout(box)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["번호", "상품명", "판매가", "재고", "카테고리", "상태"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 70)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(160)

        layout.addWidget(self.table)
        return box

    def _build_log_section(self) -> QGroupBox:
        box = QGroupBox("4.  등록 진행 상황")
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        # 진행바 + 상태
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%  (%v / %m)")

        self.status_label = QLabel("대기 중")
        self.status_label.setFont(QFont("맑은 고딕", 9))
        self.status_label.setStyleSheet("color: #7F8C8D;")

        # 로그창
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Consolas", 9))
        self.log_edit.setStyleSheet(
            f"background-color: {COLOR_LOG_BG}; color: {COLOR_LOG_FG};"
            "border: none; border-radius: 4px; padding: 6px;"
        )

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_edit)
        return box

    def _build_button_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("central")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        btn_clear = QPushButton("로그 지우기")
        btn_clear.setObjectName("btn_secondary")
        btn_clear.clicked.connect(self.log_edit.clear)

        btn_save_log = QPushButton("로그 저장")
        btn_save_log.setObjectName("btn_secondary")
        btn_save_log.clicked.connect(self._save_log)

        self.btn_stop = QPushButton("중단")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_upload)

        self.btn_start = QPushButton("▶  등록 시작")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setFixedWidth(120)
        self.btn_start.clicked.connect(self._start_upload)

        layout.addWidget(btn_clear)
        layout.addWidget(btn_save_log)
        layout.addStretch()
        layout.addWidget(self.btn_stop)
        layout.addWidget(self.btn_start)
        return bar

    # ── 이벤트 핸들러 ────────────────────────

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "엑셀 파일 선택", "",
            "Excel 파일 (*.xlsx *.xls);;모든 파일 (*.*)"
        )
        if path:
            self.file_edit.setText(path)
            self._load_products(path)

    def _load_products(self, path: str):
        self.table.setRowCount(0)
        self._log(f"파일 로드 중: {os.path.basename(path)}")
        self.products, errors = read_excel(path)

        self.progress_bar.setMaximum(len(self.products))
        self.progress_bar.setValue(0)

        for i, p in enumerate(self.products):
            self.table.insertRow(i)
            items = [
                str(i + 1), p.name, f"{p.price:,}원",
                str(p.stock), p.category,
                "정상" if p.is_valid else "오류"
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter if col != 1 else Qt.AlignVCenter | Qt.AlignLeft)
                if not p.is_valid:
                    item.setForeground(QColor(COLOR_ERROR))
                self.table.setItem(i, col, item)

        valid = len(get_valid_products(self.products))
        total = len(self.products)
        self._log(f"총 {total}개 로드 완료 — 정상: {valid}개 / 오류: {total - valid}개")
        for e in errors:
            self._log(f"  [오류] {e}", color=COLOR_ERROR)

    def _open_settings(self):
        dlg = SettingsWindow(self)
        dlg.exec_()
        self._apply_clients()

    def _apply_clients(self):
        config = SettingsWindow.load_config()

        ss = SmartStoreClient()
        ss.configure(**config.get("smartstore", {}))
        self.uploader.register_client("스마트스토어", ss)

        cp = CoupangClient()
        cp.configure(**config.get("coupang", {}))
        self.uploader.register_client("쿠팡", cp)

        st = St11Client()
        cfg_11 = config.get("st11", {})
        if cfg_11.get("api_key"):
            st.configure(api_key=cfg_11["api_key"])
        self.uploader.register_client("11번가", st)

        gm = GmarketClient()
        gm.configure(**config.get("gmarket", {}))
        self.uploader.register_client("지마켓", gm)

        ac = AuctionClient()
        ac.configure(**config.get("auction", {}))
        self.uploader.register_client("옥션", ac)

    def _start_upload(self):
        if not self.file_edit.text():
            QMessageBox.warning(self, "파일 없음", "엑셀 파일을 먼저 선택하세요.")
            return

        valid_products = get_valid_products(self.products)
        if not valid_products:
            QMessageBox.warning(self, "상품 없음", "등록 가능한 상품이 없습니다.")
            return

        selected = [p for p, cb in self.platform_checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "플랫폼 없음", "등록할 쇼핑몰을 하나 이상 선택하세요.")
            return

        total = len(valid_products) * len(selected)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(0)
        self._progress_done = 0

        self._log(f"\n{'━' * 52}")
        self._log(f"등록 시작: {len(valid_products)}개 상품 × {len(selected)}개 플랫폼 = {total}건")
        self._log(f"대상 플랫폼: {', '.join(selected)}")
        self._log(f"{'━' * 52}")

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.worker = UploadWorker(self.uploader, valid_products, selected)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_complete)
        self.worker.start()

    def _stop_upload(self):
        self.uploader.stop()
        self._log("사용자가 중단을 요청했습니다.", color=COLOR_WARNING)
        self.btn_stop.setEnabled(False)

    def _on_progress(self, message: str):
        self._log(message)
        if "완료" in message or "실패" in message:
            self._progress_done = getattr(self, "_progress_done", 0) + 1
            self.progress_bar.setValue(self._progress_done)
            total = self.progress_bar.maximum()
            self.status_label.setText(f"진행 중... {self._progress_done} / {total}")

    def _on_complete(self, summary: dict):
        self._log(f"\n{'━' * 52}")
        self._log(
            f"등록 완료!  성공: {summary['success']}건  /  실패: {summary['fail']}건  /  전체: {summary['total']}건",
            color=COLOR_SUCCESS
        )
        self._log(f"{'━' * 52}")
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText(
            f"완료 — 성공 {summary['success']}건 / 실패 {summary['fail']}건"
        )
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        msg = QMessageBox(self)
        msg.setWindowTitle("등록 완료")
        msg.setText(f"성공: {summary['success']}건\n실패: {summary['fail']}건")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    def _log(self, message: str, color: str = None):
        ts = datetime.now().strftime("%H:%M:%S")
        c = color or COLOR_LOG_FG
        html = (
            f'<span style="color:#6C757D;">[{ts}]</span> '
            f'<span style="color:{c};">{message}</span>'
        )
        self.log_edit.append(html)

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "로그 저장", f"등록로그_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "텍스트 파일 (*.txt)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_edit.toPlainText())
            QMessageBox.information(self, "저장 완료", f"로그가 저장되었습니다:\n{path}")

    def _save_template(self):
        src = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "templates", "상품등록_템플릿.xlsx"
        )
        if not os.path.exists(src):
            QMessageBox.critical(self, "오류", "템플릿 파일을 찾을 수 없습니다.")
            return
        dst, _ = QFileDialog.getSaveFileName(
            self, "템플릿 저장", "상품등록_템플릿.xlsx", "Excel 파일 (*.xlsx)"
        )
        if dst:
            shutil.copy(src, dst)
            QMessageBox.information(self, "저장 완료", f"템플릿이 저장되었습니다:\n{dst}")
