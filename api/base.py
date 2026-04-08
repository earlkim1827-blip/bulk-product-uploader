"""
API 클라이언트 베이스 클래스
모든 쇼핑몰 API 클라이언트가 상속하는 공통 인터페이스
"""
import requests
import logging
from abc import ABC, abstractmethod
from core.product_model import Product

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """모든 쇼핑몰 API 클라이언트의 기반 클래스"""

    PLATFORM_NAME = "Unknown"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._is_configured = False

    @abstractmethod
    def configure(self, **kwargs):
        """API 키 등 인증 정보 설정"""
        pass

    @abstractmethod
    def register_product(self, product: Product) -> dict:
        """
        상품 등록
        Returns:
            {"success": bool, "product_id": str, "message": str, "error": str}
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """API 연결 테스트"""
        pass

    def is_configured(self) -> bool:
        return self._is_configured

    def _success(self, product_id: str, message: str = "") -> dict:
        return {"success": True, "product_id": str(product_id), "message": message, "error": ""}

    def _failure(self, error: str) -> dict:
        return {"success": False, "product_id": "", "message": "", "error": error}

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        try:
            resp = self.session.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.Timeout:
            raise Exception(f"[{self.PLATFORM_NAME}] 요청 시간 초과")
        except requests.exceptions.ConnectionError:
            raise Exception(f"[{self.PLATFORM_NAME}] 네트워크 연결 오류")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"[{self.PLATFORM_NAME}] HTTP 오류 {e.response.status_code}: {e.response.text[:200]}")
