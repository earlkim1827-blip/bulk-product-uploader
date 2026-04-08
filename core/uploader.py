"""
업로드 관리 모듈
여러 플랫폼에 상품을 등록하고 결과를 관리
"""
import threading
import time
from typing import List, Callable, Dict
from core.product_model import Product


class UploadResult:
    """단일 상품 등록 결과"""
    def __init__(self, product: Product, platform: str):
        self.product = product
        self.platform = platform
        self.success = False
        self.product_id = ""      # 등록된 상품 ID
        self.message = ""
        self.error = ""

    def __str__(self):
        status = "성공" if self.success else "실패"
        msg = self.product_id if self.success else self.error
        return f"[{self.platform}] {self.product.name} - {status}: {msg}"


class Uploader:
    """
    멀티 플랫폼 상품 업로드 관리자
    각 플랫폼 API 클라이언트를 등록하고 상품을 업로드
    """

    def __init__(self):
        self._clients: Dict[str, object] = {}
        self._results: List[UploadResult] = []
        self._is_running = False
        self._stop_flag = False

    def register_client(self, platform_name: str, client):
        """API 클라이언트 등록"""
        self._clients[platform_name] = client

    def get_registered_platforms(self) -> List[str]:
        return list(self._clients.keys())

    def upload(
        self,
        products: List[Product],
        platforms: List[str],
        on_progress: Callable[[str], None] = None,
        on_complete: Callable[[List[UploadResult]], None] = None,
    ):
        """
        비동기로 상품 업로드 실행
        Args:
            products: 등록할 상품 목록
            platforms: 등록할 플랫폼 목록
            on_progress: 진행상황 콜백 (메시지 문자열)
            on_complete: 완료 콜백 (결과 리스트)
        """
        self._results = []
        self._stop_flag = False
        self._is_running = True

        thread = threading.Thread(
            target=self._upload_thread,
            args=(products, platforms, on_progress, on_complete),
            daemon=True
        )
        thread.start()

    def stop(self):
        """업로드 중단 요청"""
        self._stop_flag = True

    def _upload_thread(self, products, platforms, on_progress, on_complete):
        try:
            total = len(products) * len(platforms)
            done = 0

            for platform in platforms:
                if self._stop_flag:
                    break

                client = self._clients.get(platform)
                if not client:
                    if on_progress:
                        on_progress(f"[경고] {platform} 클라이언트가 등록되지 않았습니다.")
                    continue

                for product in products:
                    if self._stop_flag:
                        break

                    result = UploadResult(product, platform)
                    if on_progress:
                        on_progress(f"[{platform}] '{product.name}' 등록 중...")

                    try:
                        resp = client.register_product(product)
                        result.success = resp.get("success", False)
                        result.product_id = resp.get("product_id", "")
                        result.message = resp.get("message", "")
                        result.error = resp.get("error", "")
                    except Exception as e:
                        result.success = False
                        result.error = str(e)

                    self._results.append(result)
                    done += 1

                    status = "완료" if result.success else f"실패({result.error})"
                    if on_progress:
                        on_progress(f"  -> {status} ({done}/{total})")

                    time.sleep(0.3)  # API 과호출 방지

        finally:
            self._is_running = False
            if on_complete:
                on_complete(self._results)

    def get_summary(self) -> Dict:
        """업로드 결과 요약"""
        total = len(self._results)
        success = sum(1 for r in self._results if r.success)
        fail = total - success
        return {
            "total": total,
            "success": success,
            "fail": fail,
            "results": self._results,
        }
