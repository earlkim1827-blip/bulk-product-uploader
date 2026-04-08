"""
메인 GUI 윈도우
상품 대량등록 솔루션의 메인 화면
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.excel_reader import read_excel, get_valid_products, get_invalid_products
from core.uploader import Uploader
from gui.settings_window import SettingsWindow

from api.smartstore import SmartStoreClient
from api.coupang import CoupangClient
from api.st11 import St11Client
from api.gmarket import GmarketClient
from api.auction import AuctionClient


PLATFORMS = ["스마트스토어", "쿠팡", "11번가", "지마켓", "옥션"]

PLATFORM_CLIENT_MAP = {
    "스마트스토어": SmartStoreClient,
    "쿠팡": CoupangClient,
    "11번가": St11Client,
    "지마켓": GmarketClient,
    "옥션": AuctionClient,
}


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("상품 대량등록 솔루션 v1.0")
        self.geometry("800x680")
        self.minsize(700, 600)
        self.configure(bg="#f5f5f5")

        self.uploader = Uploader()
        self.products = []
        self.excel_path = tk.StringVar()

        self._build_ui()
        self._apply_clients()

    # ───────────────────────── UI 구성 ─────────────────────────

    def _build_ui(self):
        # 상단 타이틀
        title_frame = tk.Frame(self, bg="#2c3e50", pady=12)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="상품 대량등록 솔루션",
                 font=("맑은 고딕", 16, "bold"), fg="white", bg="#2c3e50").pack()
        tk.Label(title_frame, text="스마트스토어 | 쿠팡 | 11번가 | 지마켓 | 옥션",
                 font=("맑은 고딕", 9), fg="#bdc3c7", bg="#2c3e50").pack()

        main = tk.Frame(self, bg="#f5f5f5", padx=15, pady=10)
        main.pack(fill="both", expand=True)

        # 1. 엑셀 파일 선택
        self._build_file_section(main)

        # 2. 플랫폼 선택
        self._build_platform_section(main)

        # 3. 상품 미리보기
        self._build_preview_section(main)

        # 4. 진행 상황 & 로그
        self._build_log_section(main)

        # 5. 하단 버튼
        self._build_buttons(main)

    def _build_file_section(self, parent):
        frame = ttk.LabelFrame(parent, text="1. 엑셀 파일 선택", padding=10)
        frame.pack(fill="x", pady=(0, 8))

        ttk.Entry(frame, textvariable=self.excel_path, state="readonly", width=60).pack(side="left", fill="x", expand=True)
        ttk.Button(frame, text="파일 선택", command=self._select_file).pack(side="left", padx=(8, 0))
        ttk.Button(frame, text="템플릿 저장", command=self._save_template).pack(side="left", padx=(4, 0))

    def _build_platform_section(self, parent):
        frame = ttk.LabelFrame(parent, text="2. 등록할 쇼핑몰 선택", padding=10)
        frame.pack(fill="x", pady=(0, 8))

        self.platform_vars = {}
        for i, platform in enumerate(PLATFORMS):
            var = tk.BooleanVar(value=True)
            self.platform_vars[platform] = var
            ttk.Checkbutton(frame, text=platform, variable=var).grid(row=0, column=i, padx=15)

        ttk.Button(frame, text="API 키 설정", command=self._open_settings).grid(row=0, column=len(PLATFORMS) + 1, padx=(20, 0))

    def _build_preview_section(self, parent):
        frame = ttk.LabelFrame(parent, text="3. 상품 미리보기", padding=10)
        frame.pack(fill="x", pady=(0, 8))

        cols = ("번호", "상품명", "가격", "재고", "카테고리", "상태")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        widths = [40, 250, 80, 60, 120, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if col != "상품명" else "w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.preview_label = tk.Label(frame, text="", fg="gray", bg="white")

    def _build_log_section(self, parent):
        frame = ttk.LabelFrame(parent, text="4. 등록 진행 상황", padding=10)
        frame.pack(fill="both", expand=True, pady=(0, 8))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(0, 6))

        self.status_label = tk.Label(frame, text="대기 중", fg="#555", bg="#f5f5f5", anchor="w")
        self.status_label.pack(fill="x")

        self.log_text = tk.Text(frame, height=8, state="disabled",
                                font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4",
                                relief="flat", padx=6, pady=4)
        self.log_text.pack(fill="both", expand=True, pady=(4, 0))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _build_buttons(self, parent):
        frame = tk.Frame(parent, bg="#f5f5f5")
        frame.pack(fill="x")

        self.btn_start = ttk.Button(frame, text="등록 시작", command=self._start_upload, width=16)
        self.btn_start.pack(side="right", padx=4)

        self.btn_stop = ttk.Button(frame, text="중단", command=self._stop_upload, state="disabled", width=10)
        self.btn_stop.pack(side="right", padx=4)

        ttk.Button(frame, text="로그 저장", command=self._save_log, width=12).pack(side="right", padx=4)
        ttk.Button(frame, text="로그 지우기", command=self._clear_log, width=12).pack(side="right", padx=4)

    # ───────────────────────── 이벤트 핸들러 ─────────────────────────

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel 파일", "*.xlsx *.xls"), ("모든 파일", "*.*")]
        )
        if path:
            self.excel_path.set(path)
            self._load_products(path)

    def _load_products(self, path: str):
        self._clear_tree()
        self._log(f"파일 로드 중: {os.path.basename(path)}")
        self.products, errors = read_excel(path)

        for i, p in enumerate(self.products, 1):
            status = "정상" if p.is_valid else "오류"
            tag = "error" if not p.is_valid else ""
            self.tree.insert("", "end", values=(i, p.name, f"{p.price:,}원", p.stock, p.category, status), tags=(tag,))

        self.tree.tag_configure("error", foreground="red")

        valid = len(get_valid_products(self.products))
        total = len(self.products)
        self._log(f"총 {total}개 상품 로드 완료 (정상: {valid}개, 오류: {total - valid}개)")
        for e in errors:
            self._log(f"  [오류] {e}")

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _open_settings(self):
        SettingsWindow(self)
        self.after(300, self._apply_clients)

    def _apply_clients(self):
        """설정 파일에서 API 키를 읽어 클라이언트 등록"""
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
        if not self.excel_path.get():
            messagebox.showwarning("파일 없음", "엑셀 파일을 먼저 선택하세요.")
            return

        valid_products = get_valid_products(self.products)
        if not valid_products:
            messagebox.showwarning("상품 없음", "등록 가능한 상품이 없습니다.")
            return

        selected_platforms = [p for p, v in self.platform_vars.items() if v.get()]
        if not selected_platforms:
            messagebox.showwarning("플랫폼 없음", "등록할 쇼핑몰을 하나 이상 선택하세요.")
            return

        total = len(valid_products) * len(selected_platforms)
        self._log(f"\n{'='*50}")
        self._log(f"등록 시작: {len(valid_products)}개 상품 × {len(selected_platforms)}개 플랫폼 = {total}건")
        self._log(f"대상 플랫폼: {', '.join(selected_platforms)}")
        self._log(f"{'='*50}")

        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.progress_var.set(0)
        self._progress_counter = 0
        self._progress_total = total

        self.uploader.upload(
            products=valid_products,
            platforms=selected_platforms,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
        )

    def _stop_upload(self):
        self.uploader.stop()
        self._log("[중단] 사용자가 중단을 요청했습니다.")
        self.btn_stop.config(state="disabled")

    def _on_progress(self, message: str):
        self.after(0, lambda: self._log(message))
        if "완료" in message or "실패" in message:
            self._progress_counter = getattr(self, "_progress_counter", 0) + 1
            total = getattr(self, "_progress_total", 1)
            pct = min(100, int(self._progress_counter / total * 100))
            self.after(0, lambda: self.progress_var.set(pct))
            self.after(0, lambda: self.status_label.config(text=f"진행 중... {self._progress_counter}/{total}"))

    def _on_complete(self, results):
        summary = self.uploader.get_summary()
        self.after(0, lambda: self._finish_upload(summary))

    def _finish_upload(self, summary):
        self._log(f"\n{'='*50}")
        self._log(f"등록 완료! 성공: {summary['success']}건 / 실패: {summary['fail']}건 / 전체: {summary['total']}건")
        self._log(f"{'='*50}")
        self.progress_var.set(100)
        self.status_label.config(text=f"완료 - 성공 {summary['success']}건 / 실패 {summary['fail']}건")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        messagebox.showinfo("등록 완료", f"성공: {summary['success']}건\n실패: {summary['fail']}건")

    def _log(self, message: str):
        self.log_text.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt")],
            initialfile=f"등록로그_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if path:
            content = self.log_text.get("1.0", "end")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("저장 완료", f"로그가 저장되었습니다:\n{path}")

    def _save_template(self):
        """엑셀 템플릿 다운로드"""
        import shutil
        src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "상품등록_템플릿.xlsx")
        if not os.path.exists(src):
            messagebox.showerror("오류", "템플릿 파일을 찾을 수 없습니다.")
            return
        dst = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel 파일", "*.xlsx")],
            initialfile="상품등록_템플릿.xlsx"
        )
        if dst:
            shutil.copy(src, dst)
            messagebox.showinfo("저장 완료", f"템플릿이 저장되었습니다:\n{dst}")
