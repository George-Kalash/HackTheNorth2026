from pydantic import BaseModel, ConfigDict, Field


class WireMarket(BaseModel):
    model_config = ConfigDict(extra="allow")
    ticker: str
    title: str
    event_ticker: str
    rules_primary: str = ""
    rules_secondary: str = ""


class WireBook(BaseModel):
    model_config = ConfigDict(extra="allow")
    orderbook_fp: dict[str, list[list[str]] | None] = Field(default_factory=dict)
