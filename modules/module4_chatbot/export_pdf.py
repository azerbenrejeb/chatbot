"""
MODULE 4 — Export de la conversation en format PDF pour archivage.
Génère un document PDF propre de l'échange entre l'utilisateur et le chatbot ESG
avec les sources citées, pour utilisation dans des rapports internes.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAPPORTS_DIR


def exporter_conversation_pdf(messages, rapport_name="", output_path=None):
    """
    Exporte une conversation complète en fichier PDF.

    :param messages: Liste de dictionnaires [{'role': str, 'content': str}]
    :param rapport_name: Nom du rapport ESG analysé.
    :param output_path: Chemin de sortie du PDF (optionnel).
    :return: Chemin du fichier PDF généré.
    """
    RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = RAPPORTS_DIR / f"Conversation_ESG_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Styles personnalisés
    title_style = ParagraphStyle(
        'ConvTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=18,
        textColor=colors.HexColor('#1e1b4b'), spaceAfter=10
    )
    user_style = ParagraphStyle(
        'UserMsg', parent=styles['BodyText'],
        fontSize=10, leading=14, spaceAfter=6,
        leftIndent=20, textColor=colors.HexColor('#1e40af'),
        backColor=colors.HexColor('#eff6ff'), borderPadding=8
    )
    assistant_style = ParagraphStyle(
        'AssistantMsg', parent=styles['BodyText'],
        fontSize=10, leading=14, spaceAfter=6,
        leftIndent=20, textColor=colors.HexColor('#166534'),
        backColor=colors.HexColor('#f0fdf4'), borderPadding=8
    )
    meta_style = ParagraphStyle(
        'MetaInfo', parent=styles['BodyText'],
        fontSize=9, textColor=colors.grey, spaceAfter=4
    )

    elements = []

    # En-tête du document
    elements.append(Paragraph("💬 Export de Conversation — Chatbot ESG", title_style))
    elements.append(Paragraph(
        f"Rapport analysé : <strong>{rapport_name or 'Non spécifié'}</strong> | "
        f"Date d'export : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        meta_style
    ))
    elements.append(Spacer(1, 15))

    # --- NOUVEAU : Section de Conformité ESG (GRI & ESRS) ---
    if rapport_name and rapport_name != "Recherche RAG Globale":
        try:
            from app.compliance_checker import extraire_references_uniques, calculer_score_conformite
            from reportlab.platypus import Table, TableStyle, HRFlowable

            references = extraire_references_uniques(session_id=None, rapport_name=rapport_name)
            conf_data = calculer_score_conformite(references)
            
            elements.append(Paragraph("📊 Synthèse de Conformité ESG (Multi-Standards)", ParagraphStyle(
                'ConfSectionHeader', parent=styles['Heading2'],
                fontName='Helvetica-Bold', fontSize=13,
                textColor=colors.HexColor('#1e1b4b'), spaceAfter=8, spaceBefore=5
            )))
            
            # Table des scores
            table_data = [["Dimension RSE", "Score GRI 2021", "Score ESRS (CSRD)"]]
            for dim, dim_data in conf_data["dimensions"].items():
                table_data.append([
                    dim, 
                    f"{dim_data['gri']['score']:.1f}%", 
                    f"{dim_data['esrs']['score']:.1f}%"
                ])
            table_data.append([
                "GLOBAL COMBINÉ", 
                f"{conf_data['score_global_gri']:.1f}%", 
                f"{conf_data['score_global_esrs']:.1f}%"
            ])
            
            t = Table(table_data, colWidths=[200, 150, 150])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('TOPPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-2), colors.HexColor('#f8fafc')),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e2e8f0')),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,1), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
                ('TOPPADDING', (0,1), (-1,-1), 5),
            ]))
            
            elements.append(t)
            elements.append(Spacer(1, 10))
            
            # Liste des indicateurs manquants
            elements.append(Paragraph("⚠️ Indicateurs Manquants par Standard :", ParagraphStyle(
                'ConfSubHeader', parent=styles['Heading3'],
                fontName='Helvetica-Bold', fontSize=10,
                textColor=colors.HexColor('#1e1b4b'), spaceAfter=5
            )))
            
            missing_style = ParagraphStyle(
                'MissingText', parent=styles['BodyText'],
                fontSize=8.5, leading=12, spaceAfter=3,
                textColor=colors.HexColor('#334155')
            )
            
            has_missing = False
            for dim, dim_data in conf_data["dimensions"].items():
                gri_missing = dim_data["gri"]["manquants"]
                esrs_missing = dim_data["esrs"]["manquants"]
                
                if gri_missing or esrs_missing:
                    elements.append(Paragraph(f"<strong>Dimension {dim} :</strong>", missing_style))
                    
                    if gri_missing:
                        gri_text = ", ".join([f"{m['code']} ({m['description']})" for m in gri_missing])
                        elements.append(Paragraph(f"  • 🇬 GRI manquants : {gri_text}", missing_style))
                        has_missing = True
                        
                    if esrs_missing:
                        esrs_text = ", ".join([f"{m['code']} ({m['description']})" for m in esrs_missing])
                        elements.append(Paragraph(f"  • 🇪🇺 ESRS manquants : {esrs_text}", missing_style))
                        has_missing = True
                        
            if not has_missing:
                elements.append(Paragraph("✅ Aucun indicateur manquant. Le rapport est 100% conforme aux exigences GRI et ESRS !", missing_style))
                
            elements.append(Spacer(1, 10))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceBefore=5, spaceAfter=10))
            
            # --- Section Recommandations Prioritaires ---
            try:
                # Retrouver le session_id à partir du rapport_name
                import sqlite3
                _db_path = Path(__file__).resolve().parent.parent.parent / "data" / "chatbot_history.db"
                _conn = sqlite3.connect(str(_db_path))
                _cur = _conn.cursor()
                _cur.execute("SELECT id FROM sessions WHERE rapport_name = ? ORDER BY id DESC LIMIT 1", (rapport_name,))
                _row = _cur.fetchone()
                _conn.close()
                
                if _row:
                    _session_id = _row[0]
                    from app.recommandations_generator import generer_recommandations
                    recos = generer_recommandations(_session_id)
                    
                    if recos:
                        elements.append(Paragraph("💡 Recommandations Prioritaires :", ParagraphStyle(
                            'RecoHeader', parent=styles['Heading3'],
                            fontName='Helvetica-Bold', fontSize=10,
                            textColor=colors.HexColor('#1e1b4b'), spaceAfter=5, spaceBefore=5
                        )))
                        reco_style = ParagraphStyle(
                            'RecoText', parent=styles['BodyText'],
                            fontSize=8.5, leading=12, spaceAfter=4,
                            textColor=colors.HexColor('#0f172a'),
                            backColor=colors.HexColor('#fef9c3'), borderPadding=6
                        )
                        for i, r in enumerate(recos, 1):
                            r_safe = r.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                            elements.append(Paragraph(f"<strong>{i}.</strong> {r_safe}", reco_style))
                        elements.append(Spacer(1, 5))
            except Exception as e_reco:
                print(f"[WARN] Erreur lors de l'ajout des recommandations au PDF : {e_reco}")
            
        except Exception as e:
            print(f"[WARN] Erreur lors de l'ajout de la synthèse de conformité au PDF : {e}")

    # Corps de la conversation
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')

        # Échapper les caractères HTML dans le contenu
        content_safe = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        if role == 'user':
            elements.append(Paragraph(f"👤 <strong>Utilisateur :</strong><br/>{content_safe}", user_style))
        elif role == 'assistant':
            elements.append(Paragraph(f"🤖 <strong>Assistant ESG :</strong><br/>{content_safe}", assistant_style))

        elements.append(Spacer(1, 6))

    # Pied de page
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Ce document a été généré automatiquement par le Chatbot ESG Intelligent. "
        "Les réponses sont basées exclusivement sur les rapports RSE chargés.",
        meta_style
    ))

    doc.build(elements)
    print(f"[OK] Conversation exportée en PDF : {output_path}")
    return str(output_path)


if __name__ == "__main__":
    # Test d'export
    test_messages = [
        {"role": "user", "content": "Quelles sont les émissions de CO2 du groupe en 2023 ?"},
        {"role": "assistant", "content": "Selon le rapport, les émissions CO2 s'élèvent à 45 200 tCO2e en 2023, soit une réduction de 15% par rapport à 2022. (Source: page 23)"},
        {"role": "user", "content": "Et pour le scope 3 ?"},
        {"role": "assistant", "content": "Les émissions de scope 3 ne sont pas détaillées dans le rapport chargé. Information non disponible."},
    ]
    exporter_conversation_pdf(test_messages, rapport_name="Rapport_ESG_Test_2023.pdf")
