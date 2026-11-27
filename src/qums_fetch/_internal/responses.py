import base64
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


def read_base64(row: Row, field: str) -> bytes:
    value = row.get(field)
    if not isinstance(value, str) or not (encoded := "".join(value.split())):
        raise InvalidResponseError(f"Expected a non-empty base64 string in {field!r}.")
    try:
        return base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise InvalidResponseError(f"{field!r} contains invalid base64.") from exc
