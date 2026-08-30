"""Tests for GetMonthRegister endpoint."""

import pytest


def test_overview_structure(client):
    month_att = client.month_attendance
    assert isinstance(month_att, dict)
    assert "overview" in month_att
    assert "details" in month_att

    overview = month_att["overview"]
    required_keys = ["Total", "Present", "Absent", "Percet"]
    for key in required_keys:
        assert key in overview, f"Missing overview key: {key}"
    assert isinstance(overview["Total"], str)
    assert "%" in overview["Percet"]


def test_details_structure(client):
    details = client.month_attendance["details"]
    assert isinstance(details, list)

    if len(details) == 0:
        pytest.skip("No attendance details for this month (holiday/break)")

    entry = details[0]
    assert "Subject" in entry
