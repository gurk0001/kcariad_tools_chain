import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_and_save_jira_pdf(target_path: str, ticket_id: str, project_info: str, tool_info: str, usecase_info: str, creation_date: str = "2026-08-16") -> None:
    """
    Compiles a corporate-styled CARIAD report and writes it directly to disk.
    """
    # Safeguard: Ensure destination directory branches exist on disk space
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Build the document canvas blueprint at the target path
    doc = SimpleDocTemplate(
        target_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
        title=f"JIRA Report Specification - {ticket_id}"
    )
    
    styles = getSampleStyleSheet()
    story = []

    # Typography Styling Rules
    title_style = ParagraphStyle(
        'CorporateTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=colors.HexColor("#0F2042"), spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'CorporateSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=colors.HexColor("#666666"), spaceAfter=20
    )
    label_style = ParagraphStyle(
        'TableLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=colors.HexColor("#1A1A1A")
    )
    value_style = ParagraphStyle(
        'TableValue', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, leading=15,
        textColor=colors.HexColor("#333333")
    )

    # Populate Structural Visual Flow Nodes
    story.append(Paragraph("CARIAD TOOLCHAIN WORKSPACE REPORT", subtitle_style))
    story.append(Paragraph(f"JIRA Ticket Verification Log: {ticket_id}", title_style))
    
    # Visual accent divider line bar 
    divider_table = Table([[""]], colWidths=[522])
    divider_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#0F2042")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider_table)
    story.append(Spacer(1, 15))

    # Construct clean scannable data layouts
    table_data = [
        [Paragraph("Ticket Identifier Key", label_style), Paragraph(ticket_id, value_style)],
        [Paragraph("Target Project Area", label_style), Paragraph(project_info, value_style)],
        [Paragraph("Registered Platform Tool", label_style), Paragraph(tool_info, value_style)],
        [Paragraph("Configured Operational Use-Case", label_style), Paragraph(usecase_info, value_style)],
        [Paragraph("System Generation Date", label_style), Paragraph(creation_date, value_style)],
        [Paragraph("Verification Status", label_style), Paragraph("<b>PENDING REVIEW</b>", value_style)]
    ]

    summary_table = Table(table_data, colWidths=[150, 372])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F4F6F9")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, textColor=colors.HexColor("#94A3B8"), alignment=1)
    story.append(Paragraph("This document represents an automated core platform state trace snapshot. Generated securely by CARIAD AI Middleware Architecture Layer.", footer_style))

    # Compile flowable elements straight down into the file destination
    doc.build(story)
