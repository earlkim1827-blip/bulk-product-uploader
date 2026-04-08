"""
상품 대량등록 솔루션 - 진입점
"""
import os
import sys
import logging

# 프로젝트 루트 경로 설정
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

from gui.main_window import MainWindow


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
