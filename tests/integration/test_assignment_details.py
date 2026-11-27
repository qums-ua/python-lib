import pytest

from qums_fetch import Client

COMMON_REQUIRED_KEYS = [
    "AssignID",
    "AssignmentDetailID",
    "EMPID",
    "EMPLOYEENAME",
    "SUBJECTID",
    "CLASSSUBJECT",
    "ASSIGNMENTSUBJECT",
    "Extension",
    "DATEFROM",
    "DATETO",
    "Assignmenttype",
    "MaxMarks",
    "Obtainmarks",
    "Keywords",
    "References",
    "Status",
    "SubmitStartEndTime",
]
AVAILABLE_REQUIRED_KEYS = [
    *COMMON_REQUIRED_KEYS,
    "SNo",
    "TimeFrom",
    "TimeTo",
    "AssignmenttypeID",
    "Count",
    "ExcellentID",
    "UploadFlag",
    "DateTimeValidation",
    "PromotionDate",
    "AdmissionDate",
]
UPLOADED_REQUIRED_KEYS = [
    *COMMON_REQUIRED_KEYS,
    "UploadID",
    "RegId",
    "AcceptRejectBy",
    "Remark",
    "UploadDate",
]


@pytest.fixture
def available_assignments(client: Client):
    assignments = client.assignment.available
    assert isinstance(assignments, list)
    if not assignments:
        pytest.skip("No available assignments for this account.")
    return assignments


@pytest.fixture
def uploaded_assignments(client: Client):
    submissions = client.assignment.uploaded
    assert isinstance(submissions, list)
    if not submissions:
        pytest.skip("No uploaded assignments for this account.")
    return submissions


def test_available_assignments_have_required_keys(available_assignments):
    for assignment in available_assignments:
        assert isinstance(assignment, dict)
        for key in AVAILABLE_REQUIRED_KEYS:
            assert key in assignment, f"Missing key: {key}"


def test_available_assignment_field_types(available_assignments):
    for assignment in available_assignments:
        assert isinstance(assignment["AssignmentDetailID"], int)
        assert isinstance(assignment["ASSIGNMENTSUBJECT"], str)
        assert isinstance(assignment["MaxMarks"], int)
        assert isinstance(assignment["Status"], int)
        assert isinstance(assignment["TimeFrom"], str | None)
        assert isinstance(assignment["TimeTo"], str | None)


def test_uploaded_assignments_have_required_keys(uploaded_assignments):
    for submission in uploaded_assignments:
        assert isinstance(submission, dict)
        for key in UPLOADED_REQUIRED_KEYS:
            assert key in submission, f"Missing key: {key}"


def test_uploaded_assignment_field_types(uploaded_assignments):
    for submission in uploaded_assignments:
        assert isinstance(submission["UploadID"], int)
        assert isinstance(submission["RegId"], int)
        assert isinstance(submission["AssignmentDetailID"], int)
        assert isinstance(submission["ASSIGNMENTSUBJECT"], str)
        assert isinstance(submission["MaxMarks"], int)
        assert isinstance(submission["Status"], str)
        assert isinstance(submission["UploadDate"], str)
