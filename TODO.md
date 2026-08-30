### In Progress

- [ ] Implement remaining API functions
- [ ] Write API documentation
- [ ] Split `client.py` into multiple modules

### Completed

- [x] Release project as a standalone library
- [x] Save cookies across sessions
- [x] Solve captch using tesseract

### API Coverage

| Endpoint                                       | Purpose                                    | Status |
| ---------------------------------------------- | ------------------------------------------ | :----: |
| `Account/GetStudentDetail`                     | Fetch student details                      |   ✅   |
| `Account/ChangePassword`                       | Change password                            |   🕑   |
| `Account/ForgotPassword`                       | Change password (send email)               |   🕑   |
| `Web_StudentAcademic/GetStudentTileData`       | Get tile data (attendance, gpa, fee, etc.) |   ✅   |
| `Web_StudentAcademic/GetTodayAttendance`       | Get today's attendance                     |   ✅   |
| `Web_StudentAcademic/GetMonthRegister`         | Get monthly attendance                     |   ✅   |
| `Web_StudentAcademic/GetYearSemWiseAttendance` | Get semester attendance                    |   ✅   |
| `Web_StudentAcademic/GetStudentExamSummary`    | Get exam results                           |   🕑   |
| `Web_StudentAcademic/GetAllScholarshipDetail`  | Get scholarship details                    |   🕑   |
| `Web_StudentAcademic/GetLectureTodayStudent`   | Get today's lecture                        |   🕑   |
| `Web_StudentAcademic/GetAllDueDates`           | Get pending dues                           |   🕑   |
| `Web_StudentAcademic/GetStudentDuesDetail`     | Get due dates (academic)                   |   🕑   |
| `Web_StudentAcademic/GetSLctStuEventDetail`    | Get event participation details            |   🕑   |
| `Web_StudentAcademic/FillStudentTimeTable`     | Get timetable                              |   🕑   |
| `Web_StudentAcademic/GetStudentAssignment`     | Get available assignments                  |   🕑   |
| `Web_Teaching/GetUploadStudentAssignment`      | Get uploaded assignments                   |   🕑   |
| `Web_StudentAcademic/GetStudentSubject`        | Get subject details                        |   🕑   |
| `/Web_Exam/GetStudentInternalMarks`            | Get midsem marks                           |   🕑   |
