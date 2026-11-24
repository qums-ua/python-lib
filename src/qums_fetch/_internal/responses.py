import json
from typing import Any

from requests import Response

from ..exceptions import InvalidResponseError

type Row = dict[str, Any]


def read_rows(response: Response, field: str = "state") -> list[Row]:
    try:
        rows = json.loads(response.json()[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidResponseError(
            f"Could not decode {field!r} in the response."
        ) from exc

    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise InvalidResponseError(f"Expected a list of records in {field!r}.")
    return rows


def read_first_row(response: Response, field: str = "state") -> Row:
    rows = read_rows(response, field)
    if not rows:
        raise InvalidResponseError(f"Expected a record in {field!r}.")
    return rows[0]
