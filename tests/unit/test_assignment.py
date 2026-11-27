from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from qums_fetch import (
    AssignmentUploadError,
    Client,
    InvalidResponseError,
)
from qums_fetch.client import BASE_URL


def test_available_assignments_are_cached_and_can_be_refreshed(post: Mock, records):
    details = records(state=[{"RegID": 4}])
    post.side_effect = [
        details,
        details,
        records(state=[]),
        details,
        records(state=[{"Subject": "Math"}]),
    ]
    client = Client("user", "pass", cookies={"session": "active"})

    assert client.assignment.available == []
    assert client.assignment.available == []
    assert post.call_count == 3
    assert post.call_args.args[0] == (
        f"{BASE_URL}/Web_StudentAcademic/GetStudentAssignment"
    )
    assert post.call_args.kwargs["data"] == {"RegID": 4}

    assert client.assignment.get_available() == [{"Subject": "Math"}]
    assert client.assignment.available == [{"Subject": "Math"}]
    assert post.call_count == 5


def test_uploaded_assignments_are_cached_and_can_be_downloaded(post: Mock, records):
    details = records(state=[{"RegID": 4}])
    submission = {"UploadID": 42, "AssignmentDetailID": 123}
    post.side_effect = [
        details,
        details,
        records(state=[]),
        details,
        records(state=[submission]),
        details,
        records(data=[{"Answer": "YQ==", "Name": "submission.pdf", "Ext": ".pdf"}]),
    ]
    client = Client("user", "pass", cookies={"session": "active"})

    assert client.assignment.uploaded == []
    assert client.assignment.uploaded == []
    assert post.call_count == 3
    assert post.call_args.args[0] == (
        f"{BASE_URL}/Web_Teaching/GetUploadStudentAssignment"
    )
    assert post.call_args.kwargs["data"] == {"RegID": 4}

    uploaded = client.assignment.get_uploaded()
    assert uploaded == [submission]
    assert client.assignment.uploaded is uploaded
    assert post.call_count == 5

    assert client.assignment.download_uploaded(uploaded[0]["UploadID"]) == b"a"
    assert client.assignment.uploaded_details[42] == {
        **submission,
        "Name": "submission.pdf",
        "Ext": ".pdf",
    }
    assert client.assignment.uploaded == [submission]


@pytest.mark.parametrize(
    ("extension", "content_type", "body"),
    [
        (".pdf", "application/pdf", "1"),
        (
            ".pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            '"1"',
        ),
        (".qums-test-unknown", "application/octet-stream", " 1\n"),
    ],
)
def test_upload_assignment_sends_file_and_refreshes_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    records,
    response,
    extension: str,
    content_type: str,
    body: str,
):
    assignment = {"AssignID": 123, "AssignmentDetailID": 47254}
    details = records(state=[{"RegID": 10048}])
    upload_response = response(body)
    send = Mock(
        side_effect=[
            details,
            details,
            records(state=[assignment]),
            details,
            upload_response,
            details,
            records(state=[]),
        ]
    )
    monkeypatch.setattr(requests.Session, "send", send)
    path = tmp_path / f"compressed fcc{extension}"
    contents = b"\x00Test submission\xff"
    path.write_bytes(contents)
    client = Client("user", "pass", cookies={"session": "active"})

    selected = client.assignment.available[0]
    assert client.assignment.upload(selected["AssignmentDetailID"], path) is (
        upload_response
    )

    request = send.call_args.args[0]
    assert request.method == "POST"
    assert request.url == (
        f"{BASE_URL}/Web_Teaching/UploadStudentAssignment?AssignmentDetailID=47254"
        f"&fileName=%20compressed%20fcc&fileExtension=%20{extension}&RegID=%2010048"
    )
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert f'name="helpSectionImages"; filename="{path.name}"'.encode() in request.body
    assert f"Content-Type: {content_type}\r\n\r\n".encode() + contents in request.body
    assert send.call_args.kwargs["allow_redirects"] is False
    assert client.assignment.available == []


@pytest.mark.parametrize(
    ("body", "error"),
    [
        ("2", AssignmentUploadError),
        ('"2"', AssignmentUploadError),
        ("<html>Sign in</html>", InvalidResponseError),
        ("3", InvalidResponseError),
    ],
)
def test_unsuccessful_upload_preserves_cached_assignments(
    post: Mock, tmp_path: Path, records, response, body: str, error: type[Exception]
):
    assignment = {"AssignmentDetailID": 47254}
    details = records(state=[{"RegID": 4}])
    post.side_effect = [
        details,
        details,
        records(state=[assignment]),
        details,
        response(body),
    ]
    client = Client("user", "pass", cookies={"session": "active"})
    path = tmp_path / "submission.pdf"
    path.write_bytes(b"Test submission")

    cached = client.assignment.available
    with pytest.raises(error):
        client.assignment.upload(47254, path)

    assert client.assignment.available is cached
    assert client.assignment.details[47254] == assignment
    assert post.call_count == 5


@pytest.mark.parametrize(
    ("method", "endpoint", "field", "row", "cache", "metadata"),
    [
        (
            "download",
            "GetAssignmentImage",
            "AssignmentDetailID",
            {
                "Assignment": "AABh/w==",
                "AssignmentExt": ".docx     ",
                "AssignmentII": "YQ==",
                "AssignmentIIExt": ".txt",
            },
            "details",
            {"AssignmentExt": ".docx     ", "AssignmentIIExt": ".txt"},
        ),
        (
            "download_uploaded",
            "GetUploadedAssignmentDocument",
            "UploadID",
            {"Answer": "AABh/w==", "Ext": ".pdf", "Name": "submission.pdf"},
            "uploaded_details",
            {"Ext": ".pdf", "Name": "submission.pdf"},
        ),
    ],
)
def test_download_assignment_decodes_file_and_keeps_metadata(
    post: Mock,
    records,
    method: str,
    endpoint: str,
    field: str,
    row: dict[str, str],
    cache: str,
    metadata: dict[str, str],
):
    details = records(state=[{"RegID": 4}])
    post.side_effect = [details, details, records(data=[row])]
    client = Client("user", "pass", cookies={"session": "active"})

    assert getattr(client.assignment, method)(47794) == b"\x00\x00a\xff"
    assert post.call_args.args[0] == f"{BASE_URL}/Web_Teaching/{endpoint}"
    assert post.call_args.kwargs["data"] == {field: 47794}
    assert getattr(client.assignment, cache) == {47794: metadata}


def test_assignment_details_combine_listing_and_download(post: Mock, records):
    details = records(state=[{"RegID": 4}])
    listing = {
        "AssignmentDetailID": 47794,
        "ASSIGNMENTSUBJECT": "Unit 1",
        "EMPLOYEENAME": "Faculty",
        "Obtainmarks": "8",
        "MaxMarks": 10,
    }
    post.side_effect = [
        details,
        details,
        records(state=[listing]),
        details,
        records(data=[{"Assignment": "YQ==", "AssignmentExt": ".pdf"}]),
    ]
    client = Client("user", "pass", cookies={"session": "active"})

    assert client.assignment.available == [listing]
    assert client.assignment.details[47794] == listing
    assert client.assignment.download(47794) == b"a"
    assert client.assignment.details[47794] == {**listing, "AssignmentExt": ".pdf"}
    assert client.assignment.available == [listing]


@pytest.mark.parametrize(
    ("body", "status", "message"),
    [
        ("", 302, "Unexpected assignment download status"),
        ("<html></html>", 200, "Could not decode"),
        ('{"data": "[]"}', 200, "Expected a record"),
        ('{"data": "[{}]"}', 200, "Expected a non-empty"),
        ('{"data": "[{\\"Assignment\\": \\"\\"}]"}', 200, "Expected a non-empty"),
        ('{"data": "[{\\"Assignment\\": \\"not base64!\\"}]"}', 200, "invalid base64"),
    ],
)
def test_invalid_assignment_download_raises_client_error(
    post: Mock, records, response, body: str, status: int, message: str
):
    details = records(state=[{"RegID": 4}])
    post.side_effect = [details, details, response(body, status=status)]
    client = Client("user", "pass", cookies={"session": "active"})

    with pytest.raises(InvalidResponseError, match=message):
        client.assignment.download(47794)
