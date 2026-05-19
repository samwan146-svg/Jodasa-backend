from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
import io
import cloudinary
import cloudinary.api
import requests
from reportlab.platypus import Image as RLImage


def get_school_logo(logo_field):
    """Fetch logo from Cloudinary and return a ReportLab Image or None."""
    try:
        if not logo_field:
            return None
        url = logo_field.url
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            img_buffer = io.BytesIO(response.content)
            img = RLImage(img_buffer, width=1.5*cm, height=1.5*cm)
            return img
    except Exception:
        return None


def generate_report_card_pdf(data, school_logo=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
          rightMargin=1*cm, leftMargin=1*cm, 
          topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    elements = []

    # --- HEADER with logo ---
    school_name = data['student']['school']

    if school_logo:
        logo_img = get_school_logo(school_logo)
        if logo_img:
            # Side by side: logo left, school name center
            header_table = Table(
                [[logo_img, 
                  Paragraph(f"<b>{school_name}</b>", 
                    ParagraphStyle('school', fontSize=16, alignment=1, spaceAfter=4)),
                  '']],
                colWidths=[2*cm, 14*cm, 2*cm]
            )
            header_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            elements.append(header_table)
        else:
            elements.append(Paragraph(f"<b>{school_name}</b>", 
                ParagraphStyle('school', fontSize=16, alignment=1, spaceAfter=4)))
    else:
        elements.append(Paragraph(f"<b>{school_name}</b>", 
            ParagraphStyle('school', fontSize=16, alignment=1, spaceAfter=4)))

    # rest stays the same from STUDENT REPORT CARD title onwards...
    elements.append(Paragraph("STUDENT REPORT CARD", 
        ParagraphStyle('title', fontSize=11, alignment=1, spaceAfter=4)))
    elements.append(Spacer(1, 0.3*cm))

    # --- STUDENT INFO ---
    student = data['student']
    elements.append(Paragraph(f"<b>{student['name']}</b>", 
        ParagraphStyle('name', fontSize=13, alignment=1)))
    elements.append(Paragraph(
        f"{student['grade']} | Stream: {student['stream']} | "
        f"Adm No: {student['admission_number']} | Term: {data['term']}",
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
            subject['teacher_remarks'] or '—',
        ])

    table = Table(table_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 4.5*cm, 5.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a6b3c')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f8e9')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWHEIGHT', (0,0), (-1,-1), 18),
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
        "Powered by Akili — CBC School Management System",
        ParagraphStyle('footer', fontSize=8, alignment=1, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer