import json
from pathlib import Path

from prediction_terminal.api.app import create_app

Path("data").mkdir(exist_ok=True)
Path("data/openapi.json").write_text(json.dumps(create_app().openapi(), indent=2))
