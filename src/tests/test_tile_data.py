"""Tests for GetStudentTileData endpoint."""

REQUIRED_KEYS = [
    "AttendPer",
    "DueAmount",
    "CreditAmount",
    "CompanyVisit",
    "placeStudent",
    "ObtainMarks",
    "Totalmarks",
    "Result",
    "CGPA",
    "BackCount",
    "FeeSession",
]


def test_has_required_keys(client):
    tile = client.tile_data
    assert isinstance(tile, list)
    assert len(tile) >= 1

    entry = tile[0]
    assert isinstance(entry, dict)
    for key in REQUIRED_KEYS:
        assert key in entry, f"Missing key: {key}"


def test_field_types(client):
    entry = client.tile_data[0]
    assert isinstance(entry["AttendPer"], (int, float))
    assert isinstance(entry["DueAmount"], (int, float))
    assert isinstance(entry["Result"], str)
    assert isinstance(entry["CGPA"], str)
    assert isinstance(entry["FeeSession"], str)
