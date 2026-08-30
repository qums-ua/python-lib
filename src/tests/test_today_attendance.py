"""Tests for GetTodayAttendance endpoint."""

import pytest

REQUIRED_KEYS = [
    "Period",
    "Duration",
    "subject",
    "SubjectCode",
    "Employeename",
    "Attend",
    "Y",
    "flag",
]


def test_has_required_keys(client):
    attendance = client.today_attendance
    assert isinstance(attendance, list)

    if len(attendance) == 0:
        pytest.skip("No attendance records for today (weekend/holiday)")

    entry = attendance[0]
    assert isinstance(entry, dict)
    for key in REQUIRED_KEYS:
        assert key in entry, f"Missing key: {key}"


def test_field_types(client):
    attendance = client.today_attendance
    if len(attendance) == 0:
        pytest.skip("No attendance records for today")

    entry = attendance[0]
    assert isinstance(entry["Period"], str)
    assert isinstance(entry["Duration"], str)
    assert isinstance(entry["subject"], str)
    assert isinstance(entry["SubjectCode"], str)
    assert entry["Attend"] in ("P", "A", "N.M.", "L", "")
