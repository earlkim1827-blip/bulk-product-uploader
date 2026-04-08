"""
API 설정 다이얼로그 (PyQt5)
각 쇼핑몰 API 키를 입력/저장하는 설정 창
"""
import json
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QFormLayout,
    QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

# ── 색상 ─────────────────────────────────────
COLOR_HEADER  = "#2C3E50"
COLOR_BG      = "#F5F5F5"
COLOR_WHITE   = "#FFFFFF"
COLOR_BORDER  = "#DDE1E7"
COLOR_TEXT    = "#2C3E50"
COLOR_MUTED   = "#7F8C8D"
COLOR_PRIMARY = "#2C3E50"

QSS = f"""
QDialog {{
    background-color: {COLOR_BG};
    font-family: '맑은 고딕';
}}
QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background-color: {COLOR_WHITE};
}}
QTabBar::tab {{
    font-family: '맑은 고딕';
    font-size: 10px;
    padding: 8px 20px;
    color: {COLOR_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    background-color: #F8F9FA;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {COLOR_WHITE};
    color: {COLOR_PRIMARY};
    font-weight: bold;
    border-bottom: 2px solid {COLOR_WHITE};
}}
QTabBar::tab:hover:!selected {{
    background-color: #ECF0F1;
    color: {COLOR_TEXT};
}}
QLineEdit {{
    font-family: '맑은 고딕';
    font-size: 10px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT};
    min-width: 320px;
}}
QLineEdit:focus {{
    border-color: {COLOR_PRIMARY};
}}
QLabel {{
    font-family: '맑은 고딕';
    font-size: 10px;
    color: {COLOR_TEXT};
}}
QLabel#guide {{
    color: {COLOR_MUTED};
    font-size: 9px;
}}
QPushButton#btn_save {{
    background-color: {COLOR_PRIMARY};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 24px;
    font-family: '맑은 고딕';
    font-size: 10px;
    font-weight: bold;
}}
QPushButton#btn_save:hover {{
    background-color: #3D5166;
}}
QPushButton#btn_cancel {{
    background-color: {COLOR_WHITE};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 8px 24px;
    font-family: '맑은 고딕';
    font-size: 10px;
}}
QPushButton#btn_cancel:hover {{
    background-color: #ECF0F1;
}}
"""

# 플랫폼별 설정 정의
PLATFORM_FIELDS = {
    "스마트스토어": {
        "key":    "smartstore",
        "guide":  "네이버 커머스 API  →  https://developer.naver.com",
        "fields": [
            ("Client ID",     "client_id",     False),
            ("Client Secret", "client_secret", True),
        ],
    },
    "쿠팡": {
        "key":    "coupang",
        "guide":  "쿠팡 Open API  →  https://developers.coupangapis.com",
        "fields": [
            ("Access Key", "access_key", False),
            ("Secret Key", "secret_key", True),
            ("Vendor ID",  "vendor_id",  False),
        ],
    },
    "11번가": {
        "key":    "st11",
        "guide":  "11번가 Open API  →  https://openapi.11st.co.kr",
        "fields": [
            ("API Key", "api_key", True),
        ],
    },
    "지마켓": {
        "key":    "gmarket",
        "guide":  "ESM Plus API  →  https://www.esmplus.com",
        "fields": [
            ("App Key",   "app_key",   True),
            ("Cert Key",  "cert_key",  True),
            ("판매자 ID", "seller_id", False),
        ],
    },
    "옥션": {
        "key":    "auction",
        "guide":  "ESM Plus API  →  https://www.esmplus.com",
        "fields": [
            ("App Key",   "app_key",   True),
            ("Cert Key",  "cert_key",  True),
            ("판매자 ID", "seller_id", False),
        ],
    },
}


class SettingsWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 키 설정")
        self.setFixedSize(520, 420)
        self.setStyleSheet(QSS)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.config_data = self._load_config()
        self.entries: dict[str, dict[str, QLineEdit]] = {}

        self._build_ui()
        self._fill_fields()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 탭 위젯
        self.tabs = QTabWidget()
        for platform, cfg in PLATFORM_FIELDS.items():
            tab = self._make_tab(platform, cfg)
            self.tabs.addTab(tab, platform)
        layout.addWidget(self.tabs)

        # 하단 버튼
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("취소")
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.setFixedWidth(90)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("저장")
        btn_save.setObjectName("btn_save")
        btn_save.setFixedWidth(90)
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _make_tab(self, platform: str, cfg: dict) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {COLOR_WHITE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(4)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setSpacing(12)

        self.entries[cfg["key"]] = {}
        for display, field_key, is_secret in cfg["fields"]:
            label = QLabel(display)
            label.setFont(QFont("맑은 고딕", 10))
            edit = QLineEdit()
            if is_secret:
                edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText(f"{display} 입력")
            form.addRow(label, edit)
            self.entries[cfg["key"]][field_key] = edit

        layout.addLayout(form)
        layout.addSpacing(12)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {COLOR_BORDER};")
        layout.addWidget(line)
        layout.addSpacing(8)

        guide = QLabel(cfg["guide"])
        guide.setObjectName("guide")
        guide.setWordWrap(True)
        layout.addWidget(guide)
        layout.addStretch()
        return tab

    def _fill_fields(self):
        for platform_key, fields in self.entries.items():
            saved = self.config_data.get(platform_key, {})
            for field_key, edit in fields.items():
                edit.setText(saved.get(field_key, ""))

    def _on_save(self):
        data = {}
        for platform_key, fields in self.entries.items():
            data[platform_key] = {k: e.text().strip() for k, e in fields.items()}
        self._save_config(data)
        QMessageBox.information(self, "저장 완료", "API 키가 저장되었습니다.")
        self.accept()

    @staticmethod
    def _load_config() -> dict:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @staticmethod
    def _save_config(data: dict):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_config() -> dict:
        return SettingsWindow._load_config()
