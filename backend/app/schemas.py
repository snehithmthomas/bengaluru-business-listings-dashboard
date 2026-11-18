import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


def _clean_text(value: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError("This field cannot be blank")
    return cleaned


class ListingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    business_name: Annotated[str, Field(min_length=1, max_length=255)]
    category: Annotated[str, Field(min_length=1, max_length=120)]
    city: Annotated[str, Field(min_length=1, max_length=120)]
    address: Annotated[str, Field(min_length=1, max_length=512)]
    phone: Annotated[str | None, Field(max_length=64)] = None
    source: Annotated[str, Field(min_length=1, max_length=80)]
    source_url: HttpUrl
    source_id: Annotated[str | None, Field(max_length=512)] = None
    latitude: float | None = None
    longitude: float | None = None

    @field_validator("business_name", "category", "city", "address", "source")
    @classmethod
    def require_nonblank(cls, value: str) -> str:
        return _clean_text(value)

    @field_validator("city")
    @classmethod
    def normalize_bengaluru_city(cls, value: str) -> str:
        if "bangalore" in value.casefold() or "bengaluru" in value.casefold():
            return "Bengaluru"
        return value

    @field_validator("phone")
    @classmethod
    def require_plausible_phone(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        digits = re.sub(r"\D", "", value)
        if not 8 <= len(digits) <= 24:
            raise ValueError("Phone must contain between 8 and 24 digits")
        return value.strip()

    @field_validator("source_id")
    @classmethod
    def clean_source_id(cls, value: str | None) -> str | None:
        return _clean_text(value) if value is not None else None


class BulkListingsInput(BaseModel):
    listings: Annotated[list[ListingInput], Field(min_length=1, max_length=5000)]


class CountRow(BaseModel):
    label: str
    count: int


class DashboardSummary(BaseModel):
    total_listings: int
    categories: int
    sources: int
    addresses_with_phone: int
