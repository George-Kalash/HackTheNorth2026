from dataclasses import dataclass
from typing import Any

from .adapters.common.transport import Transport
from .adapters.kalshi.rest import KalshiFeed
from .adapters.polymarket.clob import PolymarketFeed
from .application.comparison import ComparisonService
from .application.scanner import ScannerService
from .application.search import SearchService
from .application.simulation import SimulationService
from .application.watchlists import Watchlists
from .config import Settings
from .market_data.subscriptions import Subscriptions
from .observability.metrics import Metrics
from .persistence.database import database
from .persistence.raw_archive import RawArchive
from .persistence.repositories import SQLRepository


@dataclass
class Container:
    settings: Settings
    repo: SQLRepository
    transport: Transport
    feeds: dict[str, Any]
    search: SearchService
    comparison: ComparisonService
    scanner: ScannerService
    simulation: SimulationService
    watchlists: Watchlists
    metrics: Metrics
    subscriptions: Subscriptions


def build(settings=None):
    settings = settings or Settings()
    repo = SQLRepository(database(settings.database_url))
    metrics = Metrics()
    transport = Transport(settings, RawArchive(repo), metrics)
    feeds = {"kalshi": KalshiFeed(transport), "polymarket": PolymarketFeed(transport)}
    comparison = ComparisonService(feeds, repo, settings)
    return Container(
        settings,
        repo,
        transport,
        feeds,
        SearchService(feeds, repo),
        comparison,
        ScannerService(comparison, repo, settings),
        SimulationService(comparison, repo, settings),
        Watchlists(repo),
        metrics,
        Subscriptions(),
    )
