"""
엑셀 파일 파싱 모듈
엑셀에서 상품 데이터를 읽어 Product 객체 리스트로 반환
"""
import pandas as pd
from typing import List, Tuple
from core.product_model import Product, ProductOption


# 엑셀 컬럼명 → Product 필드 매핑
COLUMN_MAP = {
    "상품코드":     "product_code",
    "상품명":       "name",
    "판매가":       "price",
    "정가":         "original_price",
    "재고":         "stock",
    "카테고리":     "category",
    "브랜드":       "brand",
    "제조사":       "manufacturer",
    "원산지":       "origin",
    "간략설명":     "short_description",
    "상세설명":     "description",
    "이미지URL":    "images",
    "배송비":       "delivery_fee",
    "배송방법":     "delivery_type",
}


def read_excel(file_path: str) -> Tuple[List[Product], List[str]]:
    """
    엑셀 파일을 읽어 상품 목록과 오류 목록을 반환
    Returns:
        (products, errors) - 파싱된 상품 리스트, 오류 메시지 리스트
    """
    products = []
    errors = []

    try:
        df = pd.read_excel(file_path, dtype=str)
        df = df.fillna("")  # NaN을 빈 문자열로
    except Exception as e:
        return [], [f"엑셀 파일 읽기 실패: {e}"]

    for idx, row in df.iterrows():
        row_num = idx + 2  # 엑셀은 2행부터 데이터
        try:
            product = _parse_row(row, row_num)
            product.validate()
            products.append(product)
            if not product.is_valid:
                errors.append(f"[{row_num}행] {product.name or '이름없음'}: {product.error_message}")
        except Exception as e:
            errors.append(f"[{row_num}행] 파싱 오류: {e}")

    return products, errors


def _parse_row(row: pd.Series, row_num: int) -> Product:
    """단일 행을 Product 객체로 변환"""

    def get(col_name: str, default="") -> str:
        for key in row.index:
            if str(key).strip() == col_name:
                return str(row[key]).strip()
        return default

    def get_int(col_name: str, default=0) -> int:
        val = get(col_name, str(default))
        try:
            return int(float(val)) if val else default
        except (ValueError, TypeError):
            return default

    # 이미지: 쉼표로 구분된 URL 목록
    images_raw = get("이미지URL", "")
    images = [img.strip() for img in images_raw.split(",") if img.strip()]

    product = Product(
        product_code=get("상품코드"),
        name=get("상품명"),
        price=get_int("판매가"),
        original_price=get_int("정가"),
        stock=get_int("재고"),
        category=get("카테고리"),
        brand=get("브랜드"),
        manufacturer=get("제조사"),
        origin=get("원산지"),
        short_description=get("간략설명"),
        description=get("상세설명"),
        images=images,
        delivery_fee=get_int("배송비"),
        delivery_type=get("배송방법") or "일반배송",
    )
    return product


def get_valid_products(products: List[Product]) -> List[Product]:
    """유효한 상품만 필터링"""
    return [p for p in products if p.is_valid]


def get_invalid_products(products: List[Product]) -> List[Product]:
    """유효하지 않은 상품만 필터링"""
    return [p for p in products if not p.is_valid]
