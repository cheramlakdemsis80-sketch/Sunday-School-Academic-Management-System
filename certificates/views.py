from io import BytesIO
from decimal import Decimal
from pathlib import Path
import re
from xml.sax.saxutils import escape

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import qrcode

from academics.models import Semester, TeacherAssignment
from students.models import Student
from results.models import Result
from .models import Certificate


# -----------------------------------------------------------------------------
# PDF resources
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
FONT_DIR = BASE_DIR / "static" / "fonts"
LOGO_PATH = BASE_DIR / "static" / "images" / "sunday_school_logo.png"

REGULAR_FONT = FONT_DIR / "NotoSansEthiopic-Regular.ttf"
BOLD_FONT = FONT_DIR / "NotoSansEthiopic-Bold.ttf"

try:
    pdfmetrics.registerFont(TTFont("NotoEthiopic", str(REGULAR_FONT)))
    pdfmetrics.registerFont(TTFont("NotoEthiopicBold", str(BOLD_FONT)))
    PDF_REGULAR = "NotoEthiopic"
    PDF_BOLD = "NotoEthiopicBold"
except Exception:
    PDF_REGULAR = "Helvetica"
    PDF_BOLD = "Helvetica-Bold"

PAGE_W, PAGE_H = landscape(A4)
MARGIN = 14 * mm
GAP = 6 * mm
COL_W = (PAGE_W - (2 * MARGIN) - GAP) / 2


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _eligible_students(semester):
    """Return active students whose required subjects are all approved."""
    if not semester:
        return []

    students = Student.objects.filter(
        status=Student.Status.ACTIVE,
        school_class__academic_year=semester.academic_year,
    ).select_related("school_class", "user")

    eligible = []
    for student in students:
        required = set(
            TeacherAssignment.objects.filter(
                school_class=student.school_class,
                academic_year=semester.academic_year,
                subject__is_active=True,
            ).values_list("subject_id", flat=True).distinct()
        )
        approved = set(
            Result.objects.filter(
                student=student,
                semester=semester,
                status=Result.Status.APPROVED,
                subject__is_active=True,
            ).values_list("subject_id", flat=True).distinct()
        )
        if required and required.issubset(approved):
            eligible.append(student)
    return eligible


def _geez_number(n):
    """Convert an integer to a simple Ge'ez numeral representation."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)

    if n == 0:
        return "0"

    ones = {1: "፩", 2: "፪", 3: "፫", 4: "፬", 5: "፭", 6: "፮", 7: "፯", 8: "፰", 9: "፱"}
    tens = {10: "፲", 20: "፳", 30: "፴", 40: "፵", 50: "፶", 60: "፷", 70: "፸", 80: "፹", 90: "፺"}

    def under100(x):
        if x < 10:
            return ones.get(x, "")
        return tens.get((x // 10) * 10, "") + (ones.get(x % 10, "") if x % 10 else "")

    parts = []
    if n >= 10000:
        q, n = divmod(n, 10000)
        parts.append(_geez_number(q) + "፼")
    if n >= 100:
        q, n = divmod(n, 100)
        parts.append("፻" if q == 1 else _geez_number(q) + "፻")
    if n:
        parts.append(under100(n))
    return "".join(parts) or "0"


def _academic_year_display(name):
    match = re.search(r"(\d{4})", str(name))
    if not match:
        return str(name)
    year = match.group(1)
    return f"{_geez_number(year)} ({year})"


def _student_age(student, on_date):
    if not student.birth_date:
        return "—"
    age = on_date.year - student.birth_date.year
    if (on_date.month, on_date.day) < (student.birth_date.month, student.birth_date.day):
        age -= 1
    return str(max(age, 0))


def _gender_amharic(student):
    if student.gender == Student.Gender.FEMALE:
        return "ሴት"
    if student.gender == Student.Gender.MALE:
        return "ወንድ"
    return "—"


def _next_grade(student):
    try:
        grade = int(str(student.school_class.grade).strip())
        return str(grade + 1)
    except (TypeError, ValueError):
        return "—"


def _fmt_decimal(value):
    value = Decimal(value)
    return f"{value:.2f}"


def _draw_page_border(c):
    c.saveState()
    c.setStrokeColor(colors.HexColor("#155e63"))
    c.setLineWidth(1.5)
    c.rect(7 * mm, 7 * mm, PAGE_W - 14 * mm, PAGE_H - 14 * mm)
    c.setStrokeColor(colors.HexColor("#d4af37"))
    c.setLineWidth(0.7)
    c.rect(10 * mm, 10 * mm, PAGE_W - 20 * mm, PAGE_H - 20 * mm)
    c.restoreState()


def _draw_centered(c, text, y, size=10, bold=False):
    c.setFont(PDF_BOLD if bold else PDF_REGULAR, size)
    c.drawCentredString(PAGE_W / 2, y, str(text))


def _paragraph(text, width, font_size=8.5, leading=None, bold=False, alignment=TA_LEFT):
    style = ParagraphStyle(
        name="pdf_dynamic",
        fontName=PDF_BOLD if bold else PDF_REGULAR,
        fontSize=font_size,
        leading=leading or (font_size + 2.5),
        alignment=alignment,
        spaceAfter=0,
        spaceBefore=0,
    )
    safe = escape(str(text)).replace("\n", "<br/>")
    return Paragraph(safe, style)


def _draw_box(c, x, y, w, h, title=None, fill=None):
    c.saveState()
    c.setStrokeColor(colors.HexColor("#155e63"))
    c.setLineWidth(0.8)
    c.rect(x, y, w, h, stroke=1, fill=0)
    if fill:
        c.setFillColor(fill)
        c.rect(x, y + h - 28, w, 28, stroke=0, fill=1)
    if title:
        c.setFillColor(colors.black)
        c.setFont(PDF_BOLD, 10)
        c.drawCentredString(x + w / 2, y + h - 18, title)
    c.restoreState()


def _draw_paragraph(c, text, x, y_top, width, height, font_size=8.5, leading=None, bold=False, alignment=TA_LEFT):
    para = _paragraph(text, width, font_size, leading, bold, alignment)
    pw, ph = para.wrap(width, height)
    para.drawOn(c, x, y_top - ph)
    return ph


def _draw_labeled_value(c, label, value, x, y, label_w, value_w, row_h=25):
    c.setStrokeColor(colors.HexColor("#888888"))
    c.setLineWidth(0.4)
    c.rect(x, y - row_h, label_w, row_h, stroke=1, fill=0)
    c.rect(x + label_w, y - row_h, value_w, row_h, stroke=1, fill=0)
    c.setFillColor(colors.HexColor("#f1f1f1"))
    c.rect(x, y - row_h, label_w, row_h, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont(PDF_BOLD, 7.5)
    c.drawString(x + 5, y - row_h / 2 - 3, label)
    _draw_paragraph(c, value, x + label_w + 5, y - 5, value_w - 10, row_h - 8, 7.8, 10)


# -----------------------------------------------------------------------------
# Web views
# -----------------------------------------------------------------------------
@login_required
def certificate_home(request):
    if request.user.role == "ADMIN":
        semesters = Semester.objects.select_related("academic_year").order_by("-academic_year_id", "name")
        selected_id = request.GET.get("semester")
        selected = (
            get_object_or_404(Semester, pk=selected_id)
            if selected_id
            else semesters.filter(is_active=True, academic_year__is_active=True).first()
        )
        eligible = _eligible_students(selected)
        certificates = (
            Certificate.objects.filter(semester=selected).select_related("student")
            if selected
            else Certificate.objects.none()
        )
        return render(request, "certificates/admin_home.html", {
            "semesters": semesters,
            "selected": selected,
            "eligible": eligible,
            "certificates": certificates,
        })

    if request.user.role == "STUDENT":
        student = get_object_or_404(Student, user=request.user)
        certificates = Certificate.objects.filter(student=student).select_related(
            "semester", "semester__academic_year"
        )
        return render(request, "certificates/student_home.html", {
            "certificates": certificates,
            "student": student,
        })

    raise PermissionDenied


@login_required
def save_certificate_comment(request, pk):
    if request.user.role != "ADMIN":
        raise PermissionDenied
    if request.method != "POST":
        return redirect("certificate_home")

    cert = get_object_or_404(Certificate, pk=pk)
    cert.grading_rule = request.POST.get("grading_rule", "").strip()
    cert.admin_comment = request.POST.get("admin_comment", "").strip()
    cert.save(update_fields=["grading_rule", "admin_comment"])
    messages.success(request, "የምስክር ወረቀቱ መመሪያና አስተያየት ተቀምጧል።")
    return redirect(request.POST.get("next") or "certificate_home")


@login_required
def download_certificate(request, pk):
    """
    Generate the certificate directly with ReportLab canvas.

    This intentionally avoids a large nested Platypus Table. The previous
    implementation placed both full pages inside one unsplittable Table row,
    which could cause LayoutError and produce a third page. This version draws
    exactly two landscape A4 pages at fixed coordinates.
    """
    cert = get_object_or_404(
        Certificate.objects.select_related(
            "student", "student__school_class", "semester", "semester__academic_year"
        ),
        pk=pk,
    )

    if request.user.role == "STUDENT" and cert.student.user_id != request.user.id:
        raise PermissionDenied
    if request.user.role not in ("ADMIN", "STUDENT"):
        raise PermissionDenied

    results = list(Result.objects.filter(
        student=cert.student,
        semester=cert.semester,
        status=Result.Status.APPROVED,
    ).select_related("subject").order_by("subject__name"))

    total = sum((r.mark for r in results), Decimal("0"))
    maximum = sum((r.subject.max_mark for r in results), Decimal("0"))
    average = total / len(results) if results else Decimal("0")
    percentage = (total / maximum * Decimal("100")) if maximum else Decimal("0")

    peers = Student.objects.filter(
        school_class=cert.student.school_class,
        status=Student.Status.ACTIVE,
    )
    peer_totals = []
    for peer in peers:
        peer_results = Result.objects.filter(
            student=peer,
            semester=cert.semester,
            status=Result.Status.APPROVED,
        )
        if peer_results.exists():
            peer_totals.append(sum((r.mark for r in peer_results), Decimal("0")))

    rank = 1 + sum(1 for value in peer_totals if value > total)
    rank_count = len(peer_totals)

    issued_date = timezone.localtime(cert.issued_at).date()
    age = _student_age(cert.student, issued_date)
    gender = _gender_amharic(cert.student)
    academic_year = _academic_year_display(cert.semester.academic_year.name)
    grade = str(cert.student.school_class.grade)
    section = str(cert.student.school_class.section)
    next_grade = _next_grade(cert.student)
    promotion = "ተዘዋውራለች" if cert.student.gender == Student.Gender.FEMALE else "ተዛውሯል"
    pass_fail = "አልፏል" if results and all(r.is_passed for r in results) else "አላለፈም"

    # QR code
    verify_url = request.build_absolute_uri(
        reverse("verify_certificate", args=[cert.verification_token])
    )
    qr = qrcode.make(verify_url)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_image = Image(qr_buffer, width=25 * mm, height=25 * mm)

    output = BytesIO()
    c = canvas.Canvas(
        output,
        pagesize=landscape(A4),
        pageCompression=1,
    )
    c.setTitle(f"የተማሪዎች ውጤት መግለጫ - {cert.student.full_name}")

    left_x = MARGIN
    right_x = MARGIN + COL_W + GAP
    content_top = PAGE_H - MARGIN

    # ======================================================================
    # PAGE 1 — TWO COLUMNS
    # ======================================================================
    _draw_page_border(c)

    # Left: grading rule + large admin-entered box
    _draw_box(c, left_x, 60, COL_W, PAGE_H - 85, "የውጤት አሰጣጥ ደንብ", colors.HexColor("#e9f4f3"))
    grading_rule = getattr(cert, "grading_rule", "") or (
        "100 – 90  →  በጣም ጥሩ\n"
        "89 – 80   →  ጥሩ\n"
        "79 – 60   →  መካከለኛ\n"
        "59 – 50   →  ደካማ / አልፏል\n"
        "ከ 50 በታች →  አላለፈም"
    )
    _draw_paragraph(
        c,
        grading_rule,
        left_x + 10,
        content_top - 43,
        COL_W - 20,
        PAGE_H - 145,
        font_size=9,
        leading=13,
    )

    # Right: church header, logo, student information
    y = content_top - 18
    _draw_centered(c, "በኢትዮጵያ ኦርቶዶክስ ተዋህዶ ቤተክርስቲያን", y, 10.5, True)
    y -= 19
    _draw_centered(c, "በአዲስ አበባ ሀገረ ስብከት", y, 10, True)
    y -= 19
    _draw_centered(c, "የላፍቶ ደብረ ትጉሃን ቅዱስ ሚካኤል ቤተክርስቲያን", y, 9.5, True)
    y -= 75

    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH), width=42 * mm, height=42 * mm)
        logo.drawOn(c, right_x + (COL_W - 42 * mm) / 2, y - 42 * mm)
    else:
        c.setFont(PDF_BOLD, 12)
        c.drawCentredString(right_x + COL_W / 2, y - 20, "LOGO")
    y -= 49 * mm

    _draw_centered(c, "ህፃናት ክፍል", y, 11, True)
    y -= 25
    _draw_centered(c, "የተማሪዎች ውጤት መግለጫ", y, 14, True)
    y -= 31

    info_x = right_x + 2
    info_w = COL_W - 4
    label_w = 38 * mm
    value_w = info_w - label_w
    row_h = 25
    _draw_labeled_value(c, "የተማሪ ሙሉ ስም", cert.student.full_name, info_x, y, label_w, value_w, row_h)
    y -= row_h
    _draw_labeled_value(c, "ፆታ", gender, info_x, y, label_w, value_w, row_h)
    y -= row_h
    _draw_labeled_value(c, "እድሜ", age, info_x, y, label_w, value_w, row_h)
    y -= row_h
    _draw_labeled_value(c, "ክፍል", f"{grade} / {section}", info_x, y, label_w, value_w, row_h)
    y -= row_h
    _draw_labeled_value(c, "የትምህርት ዘመን", academic_year, info_x, y, label_w, value_w, row_h)
    y -= row_h + 18

    _draw_paragraph(
        c,
        f"ወደ {next_grade}ኛ ቀጣይ ክፍል {promotion}",
        right_x + 5,
        y,
        COL_W - 10,
        30,
        font_size=10,
        leading=13,
        bold=True,
        alignment=TA_CENTER,
    )

    c.showPage()

    # ======================================================================
    # PAGE 2 — TWO COLUMNS
    # ======================================================================
    _draw_page_border(c)

    # Left column: Semester + total-only result table + automatic summary
    _draw_paragraph(
        c,
        f"ሴሚስተር፦ {cert.semester.get_name_display()}",
        left_x,
        content_top - 4,
        COL_W,
        24,
        font_size=12,
        leading=15,
        bold=True,
        alignment=TA_CENTER,
    )
    _draw_paragraph(
        c,
        "የውጤት መግለጫ",
        left_x,
        content_top - 28,
        COL_W,
        24,
        font_size=12,
        leading=15,
        bold=True,
        alignment=TA_CENTER,
    )

    # ONLY final subject total is printed here.
    table_data = [
        [
            _paragraph("ተ.ቁ", 30, 7.5, 9, True, TA_CENTER),
            _paragraph("የትምህርት አይነት", 205, 7.5, 9, True, TA_CENTER),
            _paragraph("ውጤት", 70, 7.5, 9, True, TA_CENTER),
        ]
    ]
    for i, result in enumerate(results, 1):
        table_data.append([
            _paragraph(str(i), 30, 7.5, 9, False, TA_CENTER),
            _paragraph(result.subject.name, 205, 7.5, 9, False, TA_LEFT),
            _paragraph(f"{result.mark:.2f}", 70, 7.5, 9, False, TA_CENTER),
        ])
    table_data.append([
        "",
        _paragraph("ጠቅላላ ውጤት", 205, 8, 10, True, TA_RIGHT),
        _paragraph(f"{total:.2f}", 70, 8, 10, True, TA_CENTER),
    ])

    result_table = Table(
        table_data,
        colWidths=[14 * mm, COL_W - 14 * mm - 34 * mm, 34 * mm],
        rowHeights=[21] + [23] * (len(table_data) - 2) + [25],
        hAlign="LEFT",
    )
    result_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcefed")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eef7f6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    tw, th = result_table.wrapOn(c, COL_W, 250)
    result_table.drawOn(c, left_x, content_top - 58 - th)

    summary_y = content_top - 66 - th
    summary_data = [
        [
            _paragraph("አማካይ", 80, 7.5, 9, True, TA_CENTER),
            _paragraph("መቶኛ", 80, 7.5, 9, True, TA_CENTER),
            _paragraph("የክፍል ደረጃ", 80, 7.5, 9, True, TA_CENTER),
            _paragraph("ሁኔታ", 80, 7.5, 9, True, TA_CENTER),
        ],
        [
            _paragraph(_fmt_decimal(average), 80, 8, 10, False, TA_CENTER),
            _paragraph(f"{percentage:.2f}%", 80, 8, 10, False, TA_CENTER),
            _paragraph(f"{rank} / {rank_count}", 80, 8, 10, False, TA_CENTER),
            _paragraph(pass_fail, 80, 8, 10, False, TA_CENTER),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[COL_W / 4] * 4, rowHeights=[20, 24])
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f1f1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    sw, sh = summary_table.wrapOn(c, COL_W, 100)
    summary_table.drawOn(c, left_x, summary_y - sh) 

    # Right column: admin comment + handwritten spaces + signature/date/QR
    current_y = content_top - 4
    _draw_box(c, right_x, current_y - 120, COL_W, 120, "የህፃናት ክፍል አስተያየት", colors.HexColor("#e9f4f3"))
    admin_comment = getattr(cert, "admin_comment", "") or ""
    if admin_comment:
        _draw_paragraph(c, admin_comment, right_x + 9, current_y - 38, COL_W - 18, 75, 8.5, 12)
    else:
        _draw_paragraph(c, "", right_x + 9, current_y - 38, COL_W - 18, 75, 8.5, 12)
    current_y -= 132

    # Class head comment — intentionally blank for handwriting.
    _draw_box(c, right_x, current_y - 105, COL_W, 105, "የክፍል ኃላፊ አስተያየት")
    c.setFont(PDF_REGULAR, 8)
    line_x1 = right_x + 10
    line_x2 = right_x + COL_W - 10
    for line_y in [current_y - 38, current_y - 58, current_y - 78]:
        c.line(line_x1, line_y, line_x2, line_y)
    current_y -= 117

    # Parent comment — intentionally blank for handwriting.
    _draw_box(c, right_x, current_y - 105, COL_W, 105, "የወላጅ አስተያየት")
    for line_y in [current_y - 38, current_y - 58, current_y - 78]:
        c.line(line_x1, line_y, line_x2, line_y)
    current_y -= 117

    # Signature + certificate number + date + QR.
    footer_h = 125
    footer_y = 34
    _draw_box(c, right_x, footer_y, COL_W, footer_h, None)

    c.setFont(PDF_REGULAR, 8)
    c.drawString(right_x + 9, footer_y + footer_h - 25, "የክፍል ሀላፊ ፊርማ፦ __________________________")
    c.drawString(right_x + 9, footer_y + footer_h - 47, f"Certificate No፦ {cert.certificate_number}")
    c.drawString(right_x + 9, footer_y + footer_h - 69, f"ቀን፦ {issued_date}")

    qr_image.drawOn(c, right_x + COL_W - 33 * mm, footer_y + 8)
    c.setFont(PDF_REGULAR, 6.5)
    c.drawCentredString(right_x + COL_W - 20 * mm, footer_y + 4, "QR Code")

    c.showPage()
    c.save()

    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{cert.certificate_number}.pdf"'
    return response


def verify_certificate(request, token):
    cert = get_object_or_404(
        Certificate.objects.select_related(
            "student", "semester", "semester__academic_year"
        ),
        verification_token=token,
    )
    results = Result.objects.filter(
        student=cert.student,
        semester=cert.semester,
        status=Result.Status.APPROVED,
    ).select_related("subject")
    total = sum((r.mark for r in results), Decimal("0"))
    average = total / results.count() if results.exists() else Decimal("0")
    return render(request, "certificates/verify.html", {
        "certificate": cert,
        "results": results,
        "total": total,
        "average": average,
    })
