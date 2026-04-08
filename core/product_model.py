"""
공통 상품 데이터 모델
모든 쇼핑몰 API에서 공통으로 사용하는 상품 구조
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProductOption:
    """상품 옵션 (색상, 사이즈 등)"""
    option_name: str          # 옵션명 (예: 색상)
    option_value: str         # 옵션값 (예: 빨강)
    add_price: int = 0        # 추가금액
    stock: int = 0            # 옵션 재고


@dataclass
class Product:
    """공통 상품 모델"""
    # 필수 항목
    name: str                              # 상품명
    price: int                             # 판매가
    stock: int                             # 재고
    category: str                          # 카테고리

    # 선택 항목
    product_code: str = ""                 # 상품코드 (자체 관리용)
    original_price: int = 0               # 정가 (원가)
    brand: str = ""                        # 브랜드
    manufacturer: str = ""                 # 제조사
    origin: str = ""                       # 원산지
    description: str = ""                  # 상품 상세설명 (HTML 가능)
    short_description: str = ""            # 간략설명
    images: List[str] = field(default_factory=list)  # 이미지 URL 목록
    options: List[ProductOption] = field(default_factory=list)  # 옵션 목록

    # 배송 정보
    delivery_fee: int = 0                  # 배송비 (0이면 무료)
    delivery_type: str = "일반배송"         # 배송방법

    # 상태
    is_valid: bool = True                  # 유효성 검사 통과 여부
    error_message: str = ""               # 오류 메시지

    def validate(self) -> bool:
        """필수 항목 유효성 검사"""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("상품명이 비어있습니다")
        if self.price <= 0:
            errors.append(f"가격이 올바르지 않습니다: {self.price}")
        if self.stock < 0:
            errors.append(f"재고가 올바르지 않습니다: {self.stock}")
        if not self.category or not self.category.strip():
            errors.append("카테고리가 비어있습니다")

        if errors:
            self.is_valid = False
            self.error_message = " | ".join(errors)
        else:
            self.is_valid = True
            self.error_message = ""

        return self.is_valid

    def to_dict(self) -> dict:
        return {
            "product_code": self.product_code,
            "name": self.name,
            "price": self.price,
            "original_price": self.original_price,
            "stock": self.stock,
            "category": self.category,
            "brand": self.brand,
            "manufacturer": self.manufacturer,
            "origin": self.origin,
            "description": self.description,
            "short_description": self.short_description,
            "images": self.images,
            "delivery_fee": self.delivery_fee,
            "delivery_type": self.delivery_type,
        }
