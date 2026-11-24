from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypedDict

from ._internal.responses import Row, read_first_row, read_rows
from .exceptions import InvalidResponseError

if TYPE_CHECKING:
    from .client import Client

ACADEMIC_PATH = "Web_StudentAcademic"


class MonthAttendance(TypedDict):
    overview: Row
    details: list[Row]


class Attendance:
    def __init__(self, client: Client):
        self._client = client
        self._clear_cache()

    def _clear_cache(self) -> None:
        self._today: list[Row] | None = None
        self._month: MonthAttendance | None = None
        self._semester: list[Row] | None = None

    @property
    def today(self) -> list[Row]:
        if self._today is None:
            return self.get_today()
        return self._today

    @property
    def month(self) -> MonthAttendance:
        if self._month is None:
            return self.get_month()
        return self._month

    @property
    def semester(self) -> list[Row]:
        if self._semester is None:
            return self.get_semester()
        return self._semester

    def get_today(self) -> list[Row]:
        details = self._client.student._ensure_details()
        response = self._client._post(
            f"{ACADEMIC_PATH}/GetTodayAttendance",
            {
                "RegID": details["RegID"],
                "date": datetime.now(tz=UTC).strftime("%d/%m/%Y"),
            },
        )
        self._today = read_rows(response)
        return self._today

    def get_month(self, month: int | None = None) -> MonthAttendance:
        details = self._client.student._ensure_details()
        response = self._client._post(
            f"{ACADEMIC_PATH}/GetMonthRegister",
            {
                "RegID": details["RegID"],
                "Month": datetime.now(tz=UTC).month if month is None else month,
            },
        )
        result = MonthAttendance(
            overview=read_first_row(response, "data"), details=read_rows(response)
        )
        if month is None:
            self._month = result
        return result

    def get_semester(self, sem: int | None = None) -> list[Row]:
        details = self._client.student._ensure_details()
        year_sem = details.get("YearSem") if sem is None else sem
        if not isinstance(year_sem, int):
            raise InvalidResponseError("Student details lack a valid YearSem.")
        response = self._client._post(
            f"{ACADEMIC_PATH}/GetYearSemWiseAttendance",
            {"RegID": details["RegID"], "YearSem": year_sem},
        )
        result = read_rows(response, "data")
        if sem is None:
            self._semester = result
        return result
