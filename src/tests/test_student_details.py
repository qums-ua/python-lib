"""Tests for GetStudentDetail endpoint."""

REQUIRED_KEYS = [
    "RegID",
    "StudentID",
    "EnrollmentNo",
    "StudentName",
    "FatherHusName",
    "MotherName",
    "College",
    "Course",
    "CourseSpecialization",
    "Univesity",
    "DOB",
    "YearSem",
    "CourseType",
    "Branch",
    "Section",
    "Email",
    "MobileNO",
    "BloodGroup",
]


def test_has_required_keys(client):
    details = client.student_details
    assert isinstance(details, dict)
    for key in REQUIRED_KEYS:
        assert key in details, f"Missing key: {key}"


def test_field_types(client):
    details = client.student_details
    assert isinstance(details["RegID"], int)
    assert isinstance(details["StudentID"], str)
    assert isinstance(details["StudentName"], str)
    assert isinstance(details["DOB"], str)
    assert isinstance(details["YearSem"], int)
    assert isinstance(details["MobileNO"], (int, str))
    assert len(str(details["MobileNO"])) == 10
