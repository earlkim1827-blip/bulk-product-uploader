"""
11번가 Open API 클라이언트
인증: API Key (헤더)
"""
import logging
from api.base import BaseAPIClient
from core.product_model import Product

logger = logging.getLogger(__name__)

BASE_URL = "https://api.11st.co.kr/rest"


class St11Client(BaseAPIClient):

    PLATFORM_NAME = "11번가"

    def __init__(self):
        super().__init__()
        self.api_key = ""

    def configure(self, api_key: str):
        self.api_key = api_key
        self._is_configured = bool(api_key)
        if api_key:
            self.session.headers.update({"openapikey": api_key})

    def test_connection(self) -> bool:
        try:
            resp = self.session.get(f"{BASE_URL}/prodservices/product/search", params={"keyword": "test", "pageSize": "1"}, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"11번가 연결 실패: {e}")
            return False

    def register_product(self, product: Product) -> dict:
        if not self._is_configured:
            return self._failure("API 키가 설정되지 않았습니다")
        try:
            payload = self._build_payload(product)
            resp = self._request("POST", f"{BASE_URL}/sellerapi/product/registration", json=payload)
            data = resp.json()
            if data.get("ResultCode") == "00":
                product_id = str(data.get("ProductNo", ""))
                return self._success(product_id, "등록 완료")
            else:
                return self._failure(data.get("ResultMessage", "등록 실패"))
        except Exception as e:
            return self._failure(str(e))

    def _build_payload(self, p: Product) -> dict:
        return {
            "ProductNm": p.name,
            "ProductPrice": str(p.price),
            "StockCnt": str(p.stock),
            "CateNo": p.category,
            "BrandNm": p.brand,
            "MakerNm": p.manufacturer,
            "OriginNm": p.origin,
            "ProductDesc": p.description,
            "MainImageUrl": p.images[0] if p.images else "",
            "SubImageUrls": ",".join(p.images[1:]) if len(p.images) > 1 else "",
            "DeliveryFee": str(p.delivery_fee),
            "DeliveryMethodCd": "01",  # 택배
        }
