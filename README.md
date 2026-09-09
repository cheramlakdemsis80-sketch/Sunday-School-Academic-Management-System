# Sunday School Student Academic Management System — Phase 1 + 2 + 3 + 4

This package contains the complete foundation through Phase 4.

## Phase 1
- Custom User model and roles: Admin, Teacher, Student
- Login/logout and role-based dashboards

## Phase 2
- Academic years and semesters
- Only one active semester per academic year
- Classes/sections
- Subjects
- Students and teachers
- Teacher assignments
- Admin CRUD and profiles

## Phase 3
- Teacher result entry
- Save Draft / Submit Results
- Student result view (approved results only)

## Phase 4 — Assessment components + approval + calculations
### Assessment components
Every subject can have its own maximum mark for:
1. Midterm (አጋማሽ ፈተና)
2. Assignment (አሳይንመንት)
3. Summary (ማጠቃለያ)
4. Exam (ፈተና)
5. Notebook (ደብተር)

The Subject admin page lets the Admin set these five maximums and the pass mark. The total maximum is automatically calculated as the sum of the five components. If a subject does not use one component, its maximum can be set to 0.

### Active semester rule
A Teacher can enter results **only for the currently active semester** and active academic year. Other semesters are not offered on the Teacher Result Entry page and are blocked server-side as well.

### Result workflow
Teacher enters component marks → Save Draft → Submit → Admin reviews → Approve or Reject.

- Approved results are visible to students.
- Rejected results can be corrected and submitted again by the teacher.
- Submitted results are locked for teacher editing until Admin action.

### Calculations
- Subject total = Midterm + Assignment + Summary + Exam + Notebook
- Pass/Fail uses the subject-specific pass mark
- Student semester total and average are calculated from approved results
- Student class rank is calculated from approved semester totals

## Important setup
This ZIP intentionally does not include a database or generated migration files. This prevents old local data/accounts from being mixed into the new project.

### Windows PowerShell / CMD
From the extracted project folder:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py makemigrations
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py createsuperuser
venv\Scripts\python.exe manage.py runserver
```

Then open:

- Login: http://127.0.0.1:8000/login/
- Admin: http://127.0.0.1:8000/admin/
- Teacher results: http://127.0.0.1:8000/results/teacher/

If PowerShell blocks `Activate.ps1`, you do not need to activate the venv. The commands above call the venv's Python directly.

## Initial recommended configuration
1. Create Academic Year, e.g. `2019 E.C.` and set it Active.
2. Create Semester 1 and Semester 2. Set only the semester currently accepting marks to Active.
3. Create the six subjects and configure their five assessment maximums. A default 20+20+20+20+20 = 100 is provided.
4. Create classes/sections.
5. Create teachers and students.
6. Create teacher assignments.
7. Log in as a teacher and enter marks only for the active semester.
8. Submit results.
9. Log in as Admin and approve/reject submitted results.
10. Log in as a Student to view approved results, totals, average, pass/fail and rank.

## Next planned phase
Phase 5 will add certificate generation, certificate numbers and QR verification.

## Phase 5 — Certificates + QR verification
- Certificates are generated automatically after the final required subject result for a student/semester is approved.
- Admin can review eligible students at `/certificates/` and download PDFs.
- Students can view/download their certificates from `/certificates/`.
- Each PDF includes a certificate number and QR code.
- QR verification is public at `/certificates/verify/<token>/` and does not require login.
- PDF generation uses ReportLab; QR generation uses qrcode.
