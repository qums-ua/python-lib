import base64
from typing import TYPE_CHECKING

import requests

from ._internal.responses import Row, read_first_row, read_rows
from .exceptions import InvalidResponseError

if TYPE_CHECKING:
    from .client import Client

STUDENT_DETAILS_PATH = "Account/GetStudentDetail"


class Student:
    def __init__(self, client: Client):
        self._client = client
        self._clear_cache()

    def _clear_cache(self) -> None:
        self._details: Row | None = None
        self._tile_data: list[Row] | None = None
        self.photo: bytes | None = None

    @property
    def details(self) -> Row:
        if self._details is None:
            return self.get_details()
        return self._details

    @property
    def tile_data(self) -> list[Row]:
        if self._tile_data is None:
            return self.get_tile_data()
        return self._tile_data

    def get_details(self) -> Row:
        return self._load_details(self._client._ensure_session())

    def get_tile_data(self) -> list[Row]:
        details = self._ensure_details()
        response = self._client._post(
            "Web_StudentAcademic/GetStudentTileData", {"RegID": details["RegID"]}
        )
        self._tile_data = read_rows(response)
        return self._tile_data

    def _check_session(self) -> Row | None:
        try:
            return self._fetch_details()
        except requests.RequestException, InvalidResponseError:
            return None

    def _ensure_details(self) -> Row:
        details = self._client._ensure_session()
        if self._details is None:
            return self._load_details(details)
        return self._details

    def _load_details(self, details: Row | None) -> Row:
        if details is None:
            details = self._fetch_details()
        self.photo = _decode_photo(details.pop("Photo", None))
        self._details = details
        return details

    def _fetch_details(self) -> Row:
        response = self._client._post(STUDENT_DETAILS_PATH)
        if response.status_code != 200:
            raise InvalidResponseError("Expected a student details response.")
        details = read_first_row(response)
        if not isinstance(details.get("RegID"), int):
            raise InvalidResponseError("Student details lack a valid RegID.")
        return details


def _decode_photo(value: object) -> bytes | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise InvalidResponseError("Expected a base64 string for the student photo.")
    try:
        return base64.b64decode("".join(value.split()), validate=True)
    except ValueError as exc:
        raise InvalidResponseError("Student photo contains invalid base64.") from exc
