from sqlalchemy import JSON, Column, DateTime, ForeignKey, MetaData, String, Table, UniqueConstraint

metadata = MetaData()


def entity(name, *keys):
    return Table(
        name,
        metadata,
        Column("id", String(160), primary_key=True),
        Column("payload", JSON, nullable=False),
        Column("updated_at", DateTime(timezone=True), nullable=False),
        *keys,
    )


def fk(name, table, nullable=False):
    return Column(
        name, String(160), ForeignKey(table + ".id", ondelete="CASCADE"), nullable=nullable, index=True
    )


venue_events = entity(
    "venue_events",
    Column("venue", String(20), nullable=False),
    Column("external_id", String(250), nullable=False),
    UniqueConstraint("venue", "external_id"),
)
venue_markets = entity(
    "venue_markets",
    fk("event_id", "venue_events"),
    Column("venue", String(20), nullable=False),
    Column("external_id", String(250), nullable=False),
    UniqueConstraint("venue", "external_id"),
)
outcomes = entity("outcomes", fk("market_id", "venue_markets"))
rule_versions = entity("rule_versions", fk("market_id", "venue_markets"))
match_groups = entity("match_groups")
match_legs = entity("match_legs", fk("match_id", "match_groups"), fk("market_id", "venue_markets"))
match_reviews = entity("match_reviews", fk("match_id", "match_groups"))
price_points = entity("price_points", fk("market_id", "venue_markets"))
book_snapshots = entity("book_snapshots", fk("market_id", "venue_markets"))
opportunity_snapshots = entity("opportunity_snapshots", fk("match_id", "match_groups"))
watchlists = entity("watchlists")
watchlist_items = entity("watchlist_items", fk("watchlist_id", "watchlists"), fk("match_id", "match_groups"))
alert_rules = entity("alert_rules", fk("match_id", "match_groups", True))
alert_events = entity("alert_events", fk("rule_id", "alert_rules"))
workspaces = entity("workspaces")
ingestion_checkpoints = entity("ingestion_checkpoints")
raw_inputs = entity("raw_inputs")
TABLES = {t.name: t for t in metadata.tables.values()}
