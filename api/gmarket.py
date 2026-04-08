"""
지마켓 API 클라이언트
ESM Plus API 사용 (지마켓/옥션 통합 플랫폼)
인증: Application Key + 판매자 ID
"""
import logging
from api.base import BaseAPIClient
from core.product_model import Product

logger = logging.getLogger(__name__)

BASE_URL = "https://api.esmplus.com"


class GmarketClient(BaseAPIClient):

    PLATFORM_NAME = "지마켓"

    def __init__(self):
        super().__init__()
        self.app_key = ""
        self.cert_key = ""
        self.seller_id = ""

    def configure(self, app_key: str, cert_key: str, seller_id: str):
        self.app_key = app_key
        self.cert_key = cert_key
        self.seller_id = seller_id
        self._is_configured = bool(app_key and cert_key and seller_id)
        if self._is_configured:
            self.session.headers.update({
                "AppKey": app_key,
                "CertKey": cert_key,
            })

    def test_connection(self) -> bool:
        try:
            resp = self.session.get(
                f"{BASE_URL}/v1/sellers/{self.seller_id}/info",
                timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"지마켓 연결 실패: {e}")
            return False

    def register_product(self, product: Product) -> dict:
        if not self._is_configured:
            return self._failure("API 키가 설정되지 않았습니다")
        try:
            payload = self._build_payload(product)
            resp = self._request(
                "POST",
                f"{BASE_URL}/v1/sellers/{self.seller_id}/items/gmarket",
                json=payload
            )
            data = resp.json()
            if data.get("ResultCode") == "0":
                product_id = str(data.get("ItemCode", ""))
                return self._success(product_id, "등록 완료")
            else:
                return self._failure(data.get("ResultMsg", "등록 실패"))
        except Exception as e:
            return self._failure(str(e))

    def _build_payload(self, p: Product) -> dict:
        return {
            "ItemTitle": p.name,
            "SalePrice": p.price,
            "Quantity": p.stock,
            "CategoryCode": p.category,
            "Brand": p.brand,
            "Maker": p.manufacturer,
            "Origin": p.origin,
            "ShortDescription": p.short_description,
            "DetailContents": p.description,
            "MainImage": p.images[0] if p.images else "",
            "SubImages": p.images[1:],
            "ShippingFeeType": "F" if p.delivery_fee == 0 else "C",  # F=무료, C=유료
            "ShippingFee": p.delivery_fee,
        }
