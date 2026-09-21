from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from pathlib import Path
from datetime import datetime
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAPPORTS_DIR as REPORTS_DIR


def generate_conformity_pdf(session_id: str, results: dict, rapport_name: str = "") -> str:
    """
    Génère un rapport PDF professionnel d'audit de conformité ESG (GRI & ESRS).
    Inclut la note globale /100, les scores par dimension, le détail de chaque
    indicateur avec ses numéros de page exacts et les recommandations prioritaires.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    clean_sid = str(session_id).replace(" ", "_")
    output_path = REPORTS_DIR / f"Rapport_Conformite_ESG_{clean_sid}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=20, leading=24,
        textColor=colors.HexColor('#0f172a'), spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, leading=15,
        textColor=colors.HexColor('#475569'), spaceAfter=14
    )
    section_heading = ParagraphStyle(
        'SecHeading', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=13, leading=17,
        textColor=colors.HexColor('#1e293b'), spaceBefore=14, spaceAfter=8
    )
    body_bold = ParagraphStyle(
        'BodyBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=12
    )
    cell_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.5, leading=11
    )
    cell_style_bold = ParagraphStyle(
        'TableCellBold', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=11
    )

    story = []

    # 1. En-tête officiel
    story.append(Paragraph("AUDIT DE CONFORMITÉ ESG & RSE", title_style))
    nom_affiche = rapport_name or results.get("rapport_name") or f"Session {session_id}"
    date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
    story.append(Paragraph(
        f"<b>Rapport analysé :</b> {nom_affiche} &nbsp;|&nbsp; <b>Date :</b> {date_str} &nbsp;|&nbsp; <b>Référentiel :</b> GRI Standards 2021 & ESRS/CSRD",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

    # 2. Synthèse des Scores
    global_data = results.get("Global", {})
    score_gri = results.get("score_global_gri", global_data.get("score", 0.0))
    score_esrs = results.get("score_global_esrs", score_gri)
    score_100 = results.get("score_esg_100", {}).get("score_global_100", round(score_gri, 1))

    status_info = global_data.get("status", {})
    status_label = status_info.get("label", "CONFORME" if score_gri >= 80 else ("PARTIELLEMENT CONFORME" if score_gri >= 50 else "NON CONFORME"))

    score_cards_data = [
        [
            Paragraph("<b>🎯 Score ESG Global</b>", body_bold),
            Paragraph("<b>🇬 Score GRI 2021</b>", body_bold),
            Paragraph("<b>🇪🇺 Score ESRS (CSRD)</b>", body_bold),
            Paragraph("<b>📋 Statut d'Audit</b>", body_bold)
        ],
        [
            Paragraph(f"<font size=16 color='#0284c7'><b>{score_100}/100</b></font>", cell_style_bold),
            Paragraph(f"<font size=16 color='#16a34a'><b>{score_gri}%</b></font>", cell_style_bold),
            Paragraph(f"<font size=16 color='#0ea5e9'><b>{score_esrs}%</b></font>", cell_style_bold),
            Paragraph(f"<font size=11 color='#334155'><b>{status_label}</b></font>", cell_style_bold)
        ]
    ]
    card_table = Table(score_cards_data, colWidths=[130, 130, 130, 133])
    card_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(card_table)
    story.append(Spacer(1, 12))

    # 3. Tableau par dimension ESG
    story.append(Paragraph("1. Scores par Dimension ESG", section_heading))
    dim_table_data = [
        ["Dimension", "Score GRI", "Indicateurs Présents", "Indicateurs Manquants", "Évaluation"]
    ]
    for dim_name in ["Environnemental", "Social", "Gouvernance"]:
        dim_info = results.get(dim_name, {})
        sc = dim_info.get("score", 0.0)
        p_len = len(dim_info.get("presents", []))
        m_len = len(dim_info.get("manquants", []))
        tot = dim_info.get("total", p_len + m_len) or 4
        st_lbl = dim_info.get("status", {}).get("label", "CONFORME" if sc >= 80 else ("PARTIEL" if sc >= 50 else "NON CONFORME"))
        dim_table_data.append([
            dim_name,
            f"{sc:.1f}%",
            f"{p_len} / {tot}",
            f"{m_len} / {tot}",
            st_lbl
        ])

    table_dim = Table(dim_table_data, colWidths=[140, 75, 110, 110, 88])
    table_dim.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f1f5f9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table_dim)
    story.append(Spacer(1, 14))

    # 4. Tableau d'audit détaillé de chaque indicateur avec ses pages
    story.append(Paragraph("2. Détail des Indicateurs GRI et Localisation dans le Document", section_heading))

    detail_headers = ["Code", "Indicateur", "Dimension", "Statut", "Pages / Localisation"]
    detail_data = [detail_headers]

    for dim_name in ["Environnemental", "Social", "Gouvernance"]:
        dim_info = results.get(dim_name, {})
        # Indicateurs présents
        for p in dim_info.get("presents", []):
            pages_str = p.get("pages_str", "")
            if not pages_str and p.get("pages"):
                pages_str = "Pages " + ", ".join(str(n) for n in p["pages"][:4])
            if not pages_str:
                pages_str = "Document"
            detail_data.append([
                Paragraph(f"<b>{p['code']}</b>", cell_style_bold),
                Paragraph(p.get("nom", ""), cell_style),
                Paragraph(dim_name, cell_style),
                Paragraph("<font color='#16a34a'><b>Présent</b></font>", cell_style_bold),
                Paragraph(f"<font color='#0369a1'><b>{pages_str}</b></font>", cell_style)
            ])
        # Indicateurs manquants
        for m in dim_info.get("manquants", []):
            detail_data.append([
                Paragraph(f"<b>{m['code']}</b>", cell_style_bold),
                Paragraph(m.get("nom", ""), cell_style),
                Paragraph(dim_name, cell_style),
                Paragraph("<font color='#dc2626'><b>Manquant</b></font>", cell_style_bold),
                Paragraph("<font color='#64748b'>Non identifié</font>", cell_style)
            ])

    detail_table = Table(detail_data, colWidths=[65, 145, 95, 75, 143])
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4.5),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 14))

    # 5. Recommandations d'Amélioration
    recos = results.get("recommandations", [])
    if recos:
        story.append(Paragraph("3. Recommandations Prioritaires d'Amélioration RSE", section_heading))
        for rec in recos[:6]:
            story.append(Paragraph(
                f"• <b>{rec.get('indicateur', '')} ({rec.get('dimension', '')})</b> — {rec.get('action', '')}",
                cell_style
            ))
            story.append(Spacer(1, 3))

    doc.build(story)
    print(f"[OK] Rapport PDF de conformité généré avec succès : {output_path}")
    return str(output_path)
