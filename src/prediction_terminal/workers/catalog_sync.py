from prediction_terminal.domain.markets import Event
from prediction_terminal.market_data.catalog import store_event


async def sync(c):
    errors = []
    for row in c.repo.list("venue_events", 100):
        e = Event.model_validate(row)
        try:
            store_event(c.repo, await c.feeds[e.venue].event(e.external_id))
        except Exception as exc:
            errors.append(type(exc).__name__)
    return errors
