"""
API 설정 창
각 쇼핑몰 API 키를 입력/저장하는 설정 윈도우
"""
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


class SettingsWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("API 키 설정")
        self.geometry("560x640")
        self.resizable(False, False)
        self.grab_set()  # 모달

        self.config_data = self._load_config()
        self._build_ui()
        self._fill_fields()

    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self, data: dict):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.entries = {}

        # 스마트스토어
        self._add_tab(notebook, "스마트스토어", "smartstore", [
            ("Client ID", "client_id"),
            ("Client Secret", "client_secret"),
        ])

        # 쿠팡
        self._add_tab(notebook, "쿠팡", "coupang", [
            ("Access Key", "access_key"),
            ("Secret Key", "secret_key"),
            ("Vendor ID", "vendor_id"),
        ])

        # 11번가
        self._add_tab(notebook, "11번가", "st11", [
            ("API Key", "api_key"),
        ])

        # 지마켓
        self._add_tab(notebook, "지마켓", "gmarket", [
            ("App Key", "app_key"),
            ("Cert Key", "cert_key"),
            ("판매자 ID", "seller_id"),
        ])

        # 옥션
        self._add_tab(notebook, "옥션", "auction", [
            ("App Key", "app_key"),
            ("Cert Key", "cert_key"),
            ("판매자 ID", "seller_id"),
        ])

        # 저장 버튼
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="저장", command=self._on_save, width=15).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="취소", command=self.destroy, width=15).pack(side="right")

    def _add_tab(self, notebook, label: str, platform: str, fields: list):
        frame = ttk.Frame(notebook, padding=15)
        notebook.add(frame, text=label)
        self.entries[platform] = {}

        for i, (display_name, key) in enumerate(fields):
            ttk.Label(frame, text=display_name + ":").grid(row=i, column=0, sticky="w", pady=6)
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=42, show="*" if "secret" in key.lower() or "key" in key.lower() else "")
            entry.grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=6)
            self.entries[platform][key] = var

        frame.columnconfigure(1, weight=1)

        # API 가이드 링크 안내
        guides = {
            "smartstore": "네이버 커머스 API: https://developer.naver.com/docs/serviceapi/commerce",
            "coupang":    "쿠팡 Open API: https://developers.coupangapis.com",
            "st11":       "11번가 Open API: https://openapi.11st.co.kr",
            "gmarket":    "ESM Plus API: https://www.esmplus.com",
            "auction":    "ESM Plus API: https://www.esmplus.com",
        }
        ttk.Label(frame, text=guides.get(platform, ""), foreground="gray", wraplength=380, justify="left").grid(
            row=len(fields) + 1, column=0, columnspan=2, sticky="w", pady=(20, 0)
        )

    def _fill_fields(self):
        for platform, fields in self.entries.items():
            platform_data = self.config_data.get(platform, {})
            for key, var in fields.items():
                var.set(platform_data.get(key, ""))

    def _on_save(self):
        data = {}
        for platform, fields in self.entries.items():
            data[platform] = {key: var.get().strip() for key, var in fields.items()}
        self._save_config(data)
        messagebox.showinfo("저장 완료", "API 키가 저장되었습니다.")
        self.destroy()

    @staticmethod
    def load_config() -> dict:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
