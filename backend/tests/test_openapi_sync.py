"""Story 1.2: frontend/openapi.json matches the API, so the generated client cannot drift."""

import json

from app.export_openapi import OPENAPI_PATH, current_schema


def test_committed_openapi_json_matches_the_app() -> None:
    committed = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))

    assert committed == current_schema(), (
        "frontend/openapi.json er utdatert. Kjør `uv run python -m app.export_openapi` i backend/ "
        "og `npm run gen:api` i frontend/."
    )
