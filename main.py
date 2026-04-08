"""
상품 대량등록 솔루션 - 진입점 (PyQt5)
"""
import os
import sys
import logging

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# 로그 설정
os.makedirs(os.path.join(ROOT_DIR, "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(ROOT_DIR, "logs", "app.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ]
)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("맑은 고딕", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
