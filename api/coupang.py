"""
쿠팡 Open API 클라이언트
인증: HMAC-SHA256 서명 방식
"""
import hmac
import hashlib
import time
import logging
from urllib.parse import urlparse, urlencode
from api.base import BaseAPIClient
from core.product_model import Product

logger = logging.getLogger(__name__)

BASE_URL = "https://api-gateway.coupang.com"
VENDOR_PRODUCT_URL = "/v2/providers/seller_api/apis/api/v1/marketplace/seller-products"


class CoupangClient(BaseAPIClient):

    PLATFORM_NAME = "쿠팡"

    def __init__(self):
        super().__init__()
        self.access_key = ""
        self.secret_key = ""
        self.vendor_id = ""

    def configure(self, access_key: str, secret_key: str, vendor_id: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.vendor_id = vendor_id
        self._is_configured = bool(access_key and secret_key and vendor_id)

    def test_connection(self) -> bool:
        try:
            url = f"/v2/providers/seller_api/apis/api/v1/vendor-items/vendor-id/{self.vendor_id}"
            headers = self._get_auth_headers("GET", url)
            resp = self.session.get(BASE_URL + url, headers=headers, timeout=10)
            return resp.status_code in (200, 404)
        except Exception as e:
            logger.error(f"쿠팡 연결 실패: {e}")
            return False

    def _get_auth_headers(self, method: str, path: str, query: str = "") -> dict:
        """HMAC-SHA256 서명 헤더 생성"""
        datetime_str = time.strftime("%y%m%dT%H%M%SZ", time.gmtime())
        message = datetime_str + method + path + query
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}",
        }

    def register_product(self, product: Product) -> dict:
        if not self._is_configured:
            return self._failure("API 키가 설정되지 않았습니다")
        try:
            payload = self._build_payload(product)
            headers = self._get_auth_headers("POST", VENDOR_PRODUCT_URL)
            resp = self._request("POST", BASE_URL + VENDOR_PRODUCT_URL, json=payload, headers=headers)
            data = resp.json()
            if data.get("code") == "200" or data.get("code") == 200:
                product_id = str(data.get("data", {}).get("sellerProductId", ""))
                return self._success(product_id, "등록 완료")
            else:
                return self._failure(data.get("message", "등록 실패"))
        except Exception as e:
            return self._failure(str(e))

    def _build_payload(self, p: Product) -> dict:
        images = [{"imageOrder": i, "imageType": "REPRESENTATION" if i == 0 else "DETAIL", "vendorPath": url}
                  for i, url in enumerate(p.images)]
        return {
            "displayCategoryCode": p.category,
            "sellerProductName": p.name,
            "vendorId": self.vendor_id,
            "salePrice": p.price,
            "stockQuantity": p.stock,
            "deliveryMethod": "PARCEL",
            "deliveryCompanyCode": "CJGLS",
            "deliveryChargeType": "FREE" if p.delivery_fee == 0 else "CHARGE",
            "basicDeliveryCharge": p.delivery_fee,
            "brand": p.brand,
            "manufacture": p.manufacturer,
            "images": images,
            "items": [{
                "itemName": p.name,
                "originalPrice": p.original_price or p.price,
                "salePrice": p.price,
                "maximumBuyCount": 999,
                "maximumBuyForPerson": 0,
                "unitCount": 1,
                "adultOnly": "EVERYONE",
                "taxType": "TAX",
                "parallelImported": "NOT_PARALLEL_IMPORTED",
                "outboundShippingTimeDay": 1,
                "attributes": [],
                "contents": [{
                    "contentsType": "TEXT",
                    "contentDetails": [{"content": p.description or p.name, "unitType": "PIECE"}]
                }],
                "notices": [],
                "keywords": [],
            }]
        }
