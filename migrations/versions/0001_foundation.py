"""Initial terminal schema (frozen DDL)."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ingestion_checkpoints",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    op.create_table(
        "match_groups",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    op.create_table(
        "raw_inputs",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    op.create_table(
        "venue_events",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column("venue", sa.String(length=20), primary_key=False, nullable=False),
        sa.Column("external_id", sa.String(length=250), primary_key=False, nullable=False),
        sa.UniqueConstraint("venue", "external_id"),
    )
    op.create_table(
        "watchlists",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
    )
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "match_id",
            sa.String(length=160),
            sa.ForeignKey("match_groups.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=True,
        ),
    )
    op.create_index("ix_alert_rules_match_id", "alert_rules", ["match_id"])
    op.create_table(
        "match_reviews",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "match_id",
            sa.String(length=160),
            sa.ForeignKey("match_groups.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_match_reviews_match_id", "match_reviews", ["match_id"])
    op.create_table(
        "opportunity_snapshots",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "match_id",
            sa.String(length=160),
            sa.ForeignKey("match_groups.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_opportunity_snapshots_match_id", "opportunity_snapshots", ["match_id"])
    op.create_table(
        "venue_markets",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "event_id",
            sa.String(length=160),
            sa.ForeignKey("venue_events.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
        sa.Column("venue", sa.String(length=20), primary_key=False, nullable=False),
        sa.Column("external_id", sa.String(length=250), primary_key=False, nullable=False),
        sa.UniqueConstraint("venue", "external_id"),
    )
    op.create_index("ix_venue_markets_event_id", "venue_markets", ["event_id"])
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "watchlist_id",
            sa.String(length=160),
            sa.ForeignKey("watchlists.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
        sa.Column(
            "match_id",
            sa.String(length=160),
            sa.ForeignKey("match_groups.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"])
    op.create_index("ix_watchlist_items_match_id", "watchlist_items", ["match_id"])
    op.create_table(
        "alert_events",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "rule_id",
            sa.String(length=160),
            sa.ForeignKey("alert_rules.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_alert_events_rule_id", "alert_events", ["rule_id"])
    op.create_table(
        "book_snapshots",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "market_id",
            sa.String(length=160),
            sa.ForeignKey("venue_markets.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_book_snapshots_market_id", "book_snapshots", ["market_id"])
    op.create_table(
        "match_legs",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "match_id",
            sa.String(length=160),
            sa.ForeignKey("match_groups.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
        sa.Column(
            "market_id",
            sa.String(length=160),
            sa.ForeignKey("venue_markets.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_match_legs_market_id", "match_legs", ["market_id"])
    op.create_index("ix_match_legs_match_id", "match_legs", ["match_id"])
    op.create_table(
        "outcomes",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "market_id",
            sa.String(length=160),
            sa.ForeignKey("venue_markets.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_outcomes_market_id", "outcomes", ["market_id"])
    op.create_table(
        "price_points",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "market_id",
            sa.String(length=160),
            sa.ForeignKey("venue_markets.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_price_points_market_id", "price_points", ["market_id"])
    op.create_table(
        "rule_versions",
        sa.Column("id", sa.String(length=160), primary_key=True, nullable=False),
        sa.Column("payload", sa.JSON(), primary_key=False, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), primary_key=False, nullable=False),
        sa.Column(
            "market_id",
            sa.String(length=160),
            sa.ForeignKey("venue_markets.id", ondelete="CASCADE"),
            primary_key=False,
            nullable=False,
        ),
    )
    op.create_index("ix_rule_versions_market_id", "rule_versions", ["market_id"])


def downgrade():
    op.drop_table("rule_versions")
    op.drop_table("price_points")
    op.drop_table("outcomes")
    op.drop_table("match_legs")
    op.drop_table("book_snapshots")
    op.drop_table("alert_events")
    op.drop_table("watchlist_items")
    op.drop_table("venue_markets")
    op.drop_table("opportunity_snapshots")
    op.drop_table("match_reviews")
    op.drop_table("alert_rules")
    op.drop_table("workspaces")
    op.drop_table("watchlists")
    op.drop_table("venue_events")
    op.drop_table("raw_inputs")
    op.drop_table("match_groups")
    op.drop_table("ingestion_checkpoints")
