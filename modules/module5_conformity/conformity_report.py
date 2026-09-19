from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle)
from pathlib import Path
from datetime import datetime
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAPPORTS_DIR as REPORTS_DIR

def generate_conformity_pdf(session_id: str, results: dict) -> str:
    """
    Génère un rapport PDF professionnel de conformité GRI.
    Retourne le chemin du fichier PDF généré.
    """

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"Rapport_Conformite_GRI_{session_id}.pdf"

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # ── Page 1 : Titre ────────────────────────────────────────────────────
    story.append(Spacer(1, 50))
    story.append(Paragraph(
        "RAPPORT DE CONFORMITÉ GRI 2021",
        styles["Title"]
    ))
    story.append(Paragraph(
        f"Date d'analyse : {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 20))

    # Score global
    global_data = results["Global"]
    story.append(Paragraph(
        f"Score Global : {global_data['score']}% — "
        f"{global_data['status']['emoji']} {global_data['status']['label']}",
        styles["Heading1"]
    ))
    story.append(Spacer(1, 30))

    # ── Page 2 : Tableau des scores ───────────────────────────────────────
    story.append(Paragraph("Scores par Dimension ESG", styles["Heading2"]))
    story.append(Spacer(1, 10))

    table_data = [
        ["Dimension", "Score", "Présents", "Manquants", "Statut"]
    ]

    for dimension in ["Environnemental", "Social", "Gouvernance"]:
        dim = results[dimension]
        table_data.append([
            dimension,
            f"{dim['score']}%",
            f"{len(dim['presents'])}/4",
            f"{len(dim['manquants'])}/4",
            dim["status"]["label"]
        ])

    table = Table(table_data, colWidths=[120, 60, 70, 70, 140])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B3A6B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#F3F4F6"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 30))

    # ── Page 3 : Recommandations ──────────────────────────────────────────
    story.append(Paragraph(
        "Recommandations d'Amélioration",
        styles["Heading2"]
    ))
    story.append(Spacer(1, 10))

    for rec in results.get("recommandations", []):
        story.append(Paragraph(
            f"• <b>{rec['indicateur']}</b> ({rec['dimension']}) "
            f"— {rec['action']}",
            styles["Normal"]
        ))
        story.append(Spacer(1, 6))

    # Générer le PDF
    doc.build(story)
    return str(output_path)
