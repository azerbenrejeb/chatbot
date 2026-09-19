"""
Générateur de rapport de performance PDF automatique pour le modèle CNN.

Ce script utilise la librairie ReportLab pour compiler les résultats d'évaluation du CNN
et générer un document PDF professionnel et paginé (enregistré dans data/rapports_generes/).
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pathlib import Path
import sys

# Ajouter le chemin racine du projet pour importer la configuration globale
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAPPORTS_DIR, CNN_CLASSES


def generer_rapport_pdf(accuracy=89.22, loss=0.2053, epochs=10, test_size=334):
    """
    Crée et assemble les composants du rapport PDF d'évaluation du modèle CNN.
    
    Args:
        accuracy (float): Précision obtenue lors des tests (en %).
        loss (float): Perte moyenne obtenue en test.
        epochs (int): Nombre d'époques d'entraînement.
        test_size (int): Nombre total de pages (images) utilisées pour le test.
    """
    RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = RAPPORTS_DIR / "Rapport_Evaluation_CNN.pdf"

    # Définition du modèle de document (taille Letter, marges de 40 points)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    # Récupération de la feuille de styles par défaut de ReportLab
    styles = getSampleStyleSheet()
    
    # --- Création de styles de paragraphe personnalisés (Design premium) ---
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1a1a36'),  # Couleur bleu nuit
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#38bdf8'),  # Couleur bleu ciel moderne
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        spaceAfter=8
    )

    # La liste 'elements' contient tous les composants (Flowables) qui composeront le PDF final
    elements = []

    # --- EN-TÊTE DU DOCUMENT ---
    elements.append(Paragraph("📊 Rapport d'Évaluation du Modèle CNN ESG", title_style))
    elements.append(Paragraph("Filtre d'images de pages : ESG vs NON_ESG (Parfaitement Équilibré)", body_style))
    elements.append(Spacer(1, 15))

    # --- SECTION 1 : RÉSUMÉ DES PERFORMANCES ---
    elements.append(Paragraph("1. Résumé des Performances Globales", h2_style))
    data_perf = [
        ["Métrique", "Valeur obtenue", "Objectif du CDC"],
        ["Précision (Accuracy)", f"{accuracy:.2f}%", "> 85.0%"],
        ["Perte (Loss)", f"{loss:.4f}", "< 0.400"],
        ["Epochs d'entraînement", str(epochs), "10 epochs (CPU Optimized)"],
        ["Nombre d'images de test", str(test_size), "N/A"]
    ]
    # Création du tableau de performance avec dimensionnement des colonnes
    t1 = Table(data_perf, colWidths=[200, 150, 150])
    
    # Application d'un style CSS-like pour le tableau ReportLab
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a36')),  # En-tête bleu nuit
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),  # Corps gris clair
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 15))

    # --- SECTION 2 : PERFORMANCE PAR CATÉGORIE ---
    elements.append(Paragraph("2. Performance par Catégorie", h2_style))
    data_classes = [
        ["Classe", "Statut dans le Pipeline", "Résultat d'évaluation"],
        ["ESG", "Page conservée pour extraction de texte", "Précision élevée (96.49%)"],
        ["NON_ESG", "Page ignorée (publicité, couverture...)", "Précision élevée (81.60%)"]
    ]
    t2 = Table(data_classes, colWidths=[120, 230, 150])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#111122')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f1f5f9')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 20))

    # --- SECTION 3 : ARCHITECTURE DU MODÈLE ---
    elements.append(Paragraph("3. Architecture Technique", h2_style))
    arch_desc = """
    Le classifieur repose sur l'architecture <strong>ResNet-50</strong> pré-entraînée sur ImageNet, 
    dont les couches initiales ont été gelées pour le transfert d'apprentissage (transfer learning). 
    La couche finale fully connected (FC) a été remplacée par une couche linéaire binaire à 2 sorties 
    avec dropout de 0.5 pour minimiser le surapprentissage.
    """
    elements.append(Paragraph(arch_desc, body_style))

    # --- CONSTRUCTION FINALE ---
    # Compile les différents Flowables et écrit le fichier PDF sur disque.
    doc.build(elements)
    print(f"[OK] Rapport PDF CNN généré avec succès : {pdf_path}")


if __name__ == "__main__":
    generer_rapport_pdf()
