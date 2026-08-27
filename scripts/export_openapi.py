import sys
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from app.main import app

target = root / "gpt-action.openapi.yaml"
schema = app.openapi()
target.write_text(
    yaml.safe_dump(schema, allow_unicode=True, sort_keys=False, width=100),
    encoding="utf-8",
)
print(f"OpenAPI {schema['info']['version']} exported to {target}")
