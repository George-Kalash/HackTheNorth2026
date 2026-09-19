"""Versioned, bounded layout state. Quotes, credentials and executable callbacks are not persisted."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Group = Literal["A", "B", "C"]


class ScannerFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=2000, strict=True)
    q: str = ""
    review: str = ""
    classification: str = ""
    quantity: str = "10"
    minCapacity: str = "0"
    minNet: str = ""
    maxAge: str = "45"
    expiry: str = ""
    verified: bool = False


def default_selected() -> dict[Group, str | None]:
    return {"A": None, "B": None, "C": None}


def default_ranges() -> dict[Group, Literal[1, 7, 30]]:
    return {"A": 7, "B": 7, "C": 7}


class WorkspaceState(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=2000, strict=True)
    schema_version: Literal[1] = 1
    preset: Literal["Research", "Compare", "Scan", "Rules Review"] = "Research"
    group: Group = "A"
    selected: dict[Group, str | None] = Field(default_factory=default_selected)
    ranges: dict[Group, Literal[1, 7, 30]] = Field(default_factory=default_ranges)
    tabs: list[str] = Field(default_factory=list, max_length=100)
    leftWidth: float = Field(default=270, ge=180, le=700, allow_inf_nan=False)
    rightWidth: float = Field(default=360, ge=180, le=700, allow_inf_nan=False)
    collapsed: list[str] = Field(default_factory=list, max_length=100)
    maximized: str | None = None
    rightTab: Literal["RULES", "TRADE", "DETAILS"] = "RULES"
    mobileTab: Literal["chart", "books", "rules", "trade"] = "chart"
    priceType: Literal["provider", "midpoint", "bid", "ask"] = "provider"
    query: str = ""
    scannerFilters: ScannerFilters = Field(default_factory=ScannerFilters)
