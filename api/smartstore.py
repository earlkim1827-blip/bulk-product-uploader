"""
네이버 스마트스토어 API 클라이언트
네이버 커머스 API v1 사용
인증: Client ID / Client Secret → Access Token 발급
"""
import json
import logging
from api.base import BaseAPIClient
from core.product_model import Product

logger = logging.getLogger(__name__)

BASE_URL = "https://api.commerce.naver.com/external"


class SmartStoreClient(BaseAPIClient):

    PLATFORM_NAME = "스마트스토어"

    def __init__(self):
        super().__init__()
        self.client_id = ""
        self.client_secret = ""
        self.access_token = ""

    def configure(self, client_id: str = "", client_secret: str = "", **kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        self._is_configured = bool(client_id and client_secret)

    def test_connection(self) -> bool:
        try:
            token = self._get_access_token()
            return bool(token)
        except Exception as e:
            logger.error(f"스마트스토어 연결 실패: {e}")
            return False

    def _get_access_token(self) -> str:
        """OAuth2 Access Token 발급"""
        import time, hmac, hashlib, base64
        timestamp = str(int(time.time() * 1000))
        password = f"{self.client_id}_{timestamp}"
        hashed = hmac.new(
            self.client_secret.encode("utf-8"),
            password.encode("utf-8"),
            hashlib.sha256
        ).digest()
        client_secret_sign = base64.b64encode(hashed).decode()

        resp = self._request(
            "POST",
            f"{BASE_URL}/v1/oauth2/token",
            data={
                "client_id": self.client_id,
                "timestamp": timestamp,
                "client_secret_sign": client_secret_sign,
                "grant_type": "client_credentials",
                "type": "SELF",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        data = resp.json()
        self.access_token = data.get("access_token", "")
        self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
        return self.access_token

    def register_product(self, product: Product) -> dict:
        if not self._is_configured:
            return self._failure("API 키가 설정되지 않았습니다")
        try:
            if not self.access_token:
                self._get_access_token()

            payload = self._build_payload(product)
            resp = self._request("POST", f"{BASE_URL}/v1/products", json=payload)
            data = resp.json()
            product_id = data.get("originProductNo", "")
            return self._success(product_id, "등록 완료")
        except Exception as e:
            return self._failure(str(e))

    def _build_payload(self, p: Product) -> dict:
        return {
            "originProduct": {
                "statusType": "SALE",
                "saleType": "NEW",
                "leafCategoryId": p.category,
                "name": p.name,
                "detailContent": p.description,
                "images": {
                    "representativeImage": {"url": p.images[0] if p.images else ""},
                    "optionalImages": [{"url": u} for u in p.images[1:]]
                },
                "salePrice": p.price,
                "stockQuantity": p.stock,
                "deliveryInfo": {
                    "deliveryFee": {
                        "deliveryFeeType": "FREE" if p.delivery_fee == 0 else "CHARGE",
                        "baseFee": p.delivery_fee,
                    }
                },
            },
            "smartstoreChannelProduct": {
                "naverShoppingRegistration": True,
            }
        }
