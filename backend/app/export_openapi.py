"""Write the API's OpenAPI schema to frontend/openapi.json (Story 1.2).

The frontend generates its typed client from that file (`npm run gen:api`), and
tests/test_openapi_sync.py fails if it is out of date. Run from backend/:

    uv run python -m app.export_openapi
"""

import json
from pathlib import Path
from typing import Any

from app.config import Settings
from app.main import create_app

OPENAPI_PATH = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def current_schema() -> dict[str, Any]:
    # The schema does not depend on settings; a placeholder URL avoids reading the environment.
    return create_app(Settings(database_url="postgresql+psycopg://unused")).openapi()


def main() -> None:
    text = json.dumps(current_schema(), indent=2, ensure_ascii=False) + "\n"
    with OPENAPI_PATH.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    print(f"Skrev {OPENAPI_PATH}")


if __name__ == "__main__":
    main()
