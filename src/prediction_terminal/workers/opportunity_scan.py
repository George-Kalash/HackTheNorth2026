from prediction_terminal.application.alerts import evaluate
from prediction_terminal.domain.opportunities import SimulationInputs


async def scan(c, ids):
    for id in ids:
        match = c.comparison.match(id)
        if match.review_state != "APPROVED":
            continue
        for reverse in [False, True]:
            result = await c.simulation.run(SimulationInputs(match_id=id, reverse=reverse))
            evaluate(c.repo, result)
