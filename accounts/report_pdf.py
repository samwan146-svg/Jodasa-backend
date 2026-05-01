from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
import io


def generate_report_card_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)

    styles = getSampleStyleSheet()
    elements = []

    # --- HEADER ---
    school_name = data['student']['school']
    elements.append(Paragraph(f"<b>{school_name}</b>", ParagraphStyle('school', fontSize=16, alignment=1, spaceAfter=4)))
    elements.append(Paragraph("STUDENT REPORT CARD", ParagraphStyle('title', fontSize=11, alignment=1, spaceAfter=4)))
    elements.append(Spacer(1, 0.3*cm))

    # --- STUDENT INFO ---
    student = data['student']
    elements.append(Paragraph(f"<b>{student['name']}</b>", ParagraphStyle('name', fontSize=13, alignment=1)))
    elements.append(Paragraph(
        f"{student['grade']} | Stream: {student['stream']} | Adm No: {student['admission_number']} | Term: {data['term']}",
        ParagraphStyle('info', fontSize=9, alignment=1, spaceAfter=8)
    ))
    elements.append(Spacer(1, 0.3*cm))

    # --- SUBJECTS TABLE ---
    table_data = [['Subject', 'Marks', 'Percentage', 'Competency Level', 'Remarks']]

    for subject in data['subjects']:
        table_data.append([
            subject['subject'],
            subject['marks'],
            f"{subject['percentage']}%",
            subject['competency_level'],
            subject['teacher_remarks'],
        ])

    table = Table(table_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 4.5*cm, 5.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f8e9')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWHEIGHT', (0, 0), (-1, -1), 18),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))

    # --- SUMMARY ---
    summary = data['summary']
    competency = summary['competency_summary']
    elements.append(Paragraph(
        f"<b>Total Marks:</b> {summary['total_marks']} &nbsp;&nbsp; "
        f"<b>Average:</b> {summary['average_percentage']}% &nbsp;&nbsp; "
        f"<b>EE:</b> {competency['EE']} &nbsp; <b>ME:</b> {competency['ME']} &nbsp; "
        f"<b>AE:</b> {competency['AE']} &nbsp; <b>BE:</b> {competency['BE']}",
        ParagraphStyle('summary', fontSize=9, spaceAfter=8)
    ))
    elements.append(Spacer(1, 0.5*cm))

    # --- FOOTER ---
    elements.append(Paragraph(
        "\"The joy of learning is the greatest gift.\"",
        ParagraphStyle('footer', fontSize=8, alignment=1, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer