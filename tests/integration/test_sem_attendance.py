REQUIRED_KEYS = [
    "Subject",
    "SubjectCode",
    "SubjectID",
    "YearSem",
    "DateFrom",
    "DateTo",
    "TotalLecture",
    "TotalPresent",
    "TotalAbsent",
    "TotalLeave",
    "Percentage",
    "SubjectCredit",
]


def test_has_required_keys(client):
    sem = client.attendance.semester
    assert isinstance(sem, list)
    assert len(sem) >= 1

    entry = sem[0]
    assert isinstance(entry, dict)
    for key in REQUIRED_KEYS:
        assert key in entry, f"Missing key: {key}"


def test_field_types(client):
    entry = client.attendance.semester[0]
    assert isinstance(entry["Subject"], str)
    assert isinstance(entry["SubjectCode"], str)
    assert isinstance(entry["TotalLecture"], int)
    assert isinstance(entry["TotalPresent"], int)
    assert isinstance(entry["Percentage"], (int, float))
    assert 0 <= entry["Percentage"] <= 100
