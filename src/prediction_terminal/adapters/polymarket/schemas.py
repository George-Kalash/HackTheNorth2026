from pydantic import BaseModel, ConfigDict, Field


class WireBook(BaseModel):
    model_config = ConfigDict(extra="allow")
    asset_id: str
    bids: list[dict[str, str]] = Field(default_factory=list)
    asks: list[dict[str, str]] = Field(default_factory=list)
    timestamp: str | int
    hash: str = ""
    min_order_size: str | None = None
    tick_size: str | None = None
