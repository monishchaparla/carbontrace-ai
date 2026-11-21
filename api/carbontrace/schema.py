"""Shapes for extracted documents.

Gemini fills ExtractedDocument through structured output. Quantities stay strings exactly as
printed so no precision is lost before the deterministic engine parses them.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DocType(str, Enum):
    electricity_bill = "electricity_bill"
    fuel_receipt = "fuel_receipt"
    freight_invoice = "freight_invoice"
    supplier_invoice = "supplier_invoice"
    travel_invoice = "travel_invoice"
    other = "other"


class Category(str, Enum):
    electricity = "electricity"
    fuel = "fuel"
    freight = "freight"
    purchased_goods = "purchased_goods"
    business_travel = "business_travel"
    waste = "waste"
    water = "water"
    other = "other"


class LineItem(BaseModel):
    description: str = Field(description="Line item text as printed")
    quantity: str | None = Field(None, description="Numeric quantity as printed, digits only, no thousands separators")
    unit: str | None = Field(None, description="Unit exactly as printed, e.g. kWh, units, Ltr, MT, km")
    amount: str | None = Field(None, description="Money amount for this line as printed, digits only")
    category: Category = Field(description="Best emissions category for this line")
    is_activity: bool = Field(
        description=(
            "True only if this line measures consumption of energy, fuel or materials, or a transport/travel activity. "
            "False for charges, taxes, duties, demand or fixed charges, rent, and surcharges computed on another line's consumption."
        )
    )
    fuel_or_material: str | None = Field(None, description="Fuel type or material, e.g. diesel, steel coil")
    origin: str | None = Field(None, description="Freight origin city, if any")
    destination: str | None = Field(None, description="Freight destination city, if any")
    weight_tonnes: str | None = Field(None, description="Freight weight in tonnes, if printed")
    distance_km: str | None = Field(None, description="Freight distance in km, if printed")
    page: int = Field(1, description="1-based page number where the line appears")
    box_2d: list[int] | None = Field(
        None, description="Bounding box of the line on its page as [ymin, xmin, ymax, xmax], each 0-1000"
    )
    confidence: float = Field(description="0 to 1: how sure you are this line was read correctly")


class ExtractedDocument(BaseModel):
    doc_type: DocType
    supplier: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = Field(None, description="ISO date YYYY-MM-DD")
    period_start: str | None = Field(None, description="Billing or service period start, ISO date")
    period_end: str | None = Field(None, description="Billing or service period end, ISO date")
    currency: str | None = Field(None, description="ISO 4217 code, e.g. INR")
    country: str | None = Field(None, description="ISO 3166 alpha-2 code where the activity happened, e.g. IN")
    line_items: list[LineItem]


class Flag(BaseModel):
    code: str
    message: str
    line_index: int | None = None
