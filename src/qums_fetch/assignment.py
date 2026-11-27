from mimetypes import guess_file_type
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

from ._internal.responses import Row, read_base64, read_first_row, read_rows
from .exceptions import AssignmentUploadError, InvalidResponseError

if TYPE_CHECKING:
    from requests import Response

    from .client import Client


class Assignment:
    def __init__(self, client: Client):
        self._client = client
        self._clear_cache()

    def _clear_cache(self) -> None:
        self._available: list[Row] | None = None
        self._uploaded: list[Row] | None = None
        self.details: dict[int, Row] = {}
        self.uploaded_details: dict[int, Row] = {}

    @property
    def available(self) -> list[Row]:
        if self._available is None:
            return self.get_available()
        return self._available

    def get_available(self) -> list[Row]:
        self._available = self._get_rows("Web_StudentAcademic/GetStudentAssignment")
        for row in self._available:
            assignment_detail_id = row.get("AssignmentDetailID")
            if isinstance(assignment_detail_id, int):
                self.details.setdefault(assignment_detail_id, {}).update(row)
        return self._available

    @property
    def uploaded(self) -> list[Row]:
        if self._uploaded is None:
            return self.get_uploaded()
        return self._uploaded

    def get_uploaded(self) -> list[Row]:
        self._uploaded = self._get_rows("Web_Teaching/GetUploadStudentAssignment")
        for row in self._uploaded:
            upload_id = row.get("UploadID")
            if isinstance(upload_id, int):
                self.uploaded_details.setdefault(upload_id, {}).update(row)
        return self._uploaded

    def _get_rows(self, endpoint: str) -> list[Row]:
        details = self._client.student._ensure_details()
        return read_rows(self._client._post(endpoint, {"RegID": details["RegID"]}))

    def download(self, assignment_detail_id: int) -> bytes:
        document, row = self._download(
            "GetAssignmentImage",
            "AssignmentDetailID",
            assignment_detail_id,
            "Assignment",
        )
        for field in ("AssignmentII", "AssignmentIII", "AssignmentIV", "AssignmentV"):
            row.pop(field, None)
        self.details.setdefault(assignment_detail_id, {}).update(row)
        return document

    def download_uploaded(self, upload_id: int) -> bytes:
        document, row = self._download(
            "GetUploadedAssignmentDocument", "UploadID", upload_id, "Answer"
        )
        self.uploaded_details.setdefault(upload_id, {}).update(row)
        return document

    def _download(
        self, endpoint: str, id_field: str, document_id: int, response_field: str
    ) -> tuple[bytes, Row]:
        self._client._ensure_session()
        response = self._client._post(
            f"Web_Teaching/{endpoint}", {id_field: document_id}, timeout=60
        )
        if not 200 <= response.status_code < 300:
            raise InvalidResponseError(
                f"Unexpected assignment download status: {response.status_code}."
            )
        row = read_first_row(response, "data")
        document = read_base64(row, response_field)
        del row[response_field]
        return document, row

    def upload(self, assignment_detail_id: int, file_path: str | Path) -> Response:
        """Submit a file and return the response after QUMS confirms success."""
        path = Path(file_path)
        content_type = guess_file_type(path)[0] or "application/octet-stream"

        with path.open("rb") as file:
            details = self._client.student._ensure_details()
            query = urlencode(
                {
                    "AssignmentDetailID": assignment_detail_id,
                    "fileName": f" {path.stem}",
                    "fileExtension": f" {path.suffix}",
                    "RegID": f" {details['RegID']}",
                },
                quote_via=quote,
            )
            response = self._client._post(
                f"Web_Teaching/UploadStudentAssignment?{query}",
                files={"helpSectionImages": (path.name, file, content_type)},
                timeout=60,
            )

        if not 200 <= response.status_code < 300:
            raise InvalidResponseError(
                f"Unexpected assignment upload status: {response.status_code}."
            )
        result = response.text.strip()
        if result in ("2", '"2"'):
            raise AssignmentUploadError(
                "QUMS reported an unsuccessful assignment upload."
            )
        if result not in ("1", '"1"'):
            raise InvalidResponseError(
                "Expected an assignment upload result of 1 or 2."
            )
        self._clear_cache()
        return response
