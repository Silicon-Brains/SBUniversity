from datetime import datetime, timezone
from app.services.pdf_service import PDFService


def test_certificate_pdf_generation():
    now = datetime.now(timezone.utc)
    pdf_bytes = PDFService.render_certificate_pdf(
        student_name="Aarav Sharma",
        student_code="SBU-2026-0001",
        course_title="Data Structures & Algorithms",
        certificate_code="SBU-CERT-7F3K9Q2M",
        final_percentage=94.5,
        issued_at=now,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic bytes
    assert pdf_bytes.startswith(b"%PDF")


def test_result_pdf_generation():
    now = datetime.now(timezone.utc)
    pdf_bytes = PDFService.render_result_pdf(
        student_name="Aarav Sharma",
        student_code="SBU-2026-0001",
        exam_title="Data Structures Midterm",
        course_title="Data Structures & Algorithms",
        score=18.0,
        total_marks=20.0,
        percentage=90.0,
        grade="A+",
        passed=True,
        time_taken_sec=1800,
        rank_in_exam=1,
        submitted_at=now,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
