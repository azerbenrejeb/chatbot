"""
Génère tous les schémas d'ingénierie, diagrammes d'architecture et visuels
d'entreprise pour le rapport de PFE dans rapports/latex/figures/.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

DEST = Path("rapports/latex/figures")
DEST.mkdir(parents=True, exist_ok=True)

def sauver(fig, nom):
    p = DEST / nom
    fig.tight_layout()
    fig.savefig(p, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Schéma généré : {nom}")

# ─────────────────────────────────────────────────────────────────────
# 1. LOGO & BANDEAU RSE TIME
# ─────────────────────────────────────────────────────────────────────
def generer_logo_rse_time():
    fig, ax = plt.subplots(figsize=(6, 2.5), facecolor='white')
    ax.axis('off')
    
    # Cercle graphique transition écologique
    c1 = patches.Circle((0.2, 0.5), 0.25, color='#2E7D32', alpha=0.9)
    c2 = patches.Circle((0.28, 0.5), 0.22, color='#1565C0', alpha=0.7)
    c3 = patches.Circle((0.24, 0.65), 0.15, color='#F9A825', alpha=0.85)
    ax.add_patch(c1); ax.add_patch(c2); ax.add_patch(c3)
    
    # Texte RSE Time
    ax.text(0.48, 0.55, "RSE TIME", fontsize=28, fontweight='bold', color='#1B5E20', fontfamily='sans-serif')
    ax.text(0.48, 0.35, "Sustainability & ESG Intelligence", fontsize=11, fontweight='semibold', color='#37474F', fontfamily='sans-serif')
    ax.text(0.48, 0.22, "Audit • Compliance • Decarbonization", fontsize=9, color='#78909C', fontfamily='sans-serif')
    
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0.1, 0.9)
    sauver(fig, "fig_rse_time_logo.png")

# ─────────────────────────────────────────────────────────────────────
# 2. ORGANIGRAMME RSE TIME
# ─────────────────────────────────────────────────────────────────────
def generer_organigramme():
    fig, ax = plt.subplots(figsize=(8.5, 4.5), facecolor='white')
    ax.axis('off')

    def box(x, y, w, h, titre, sous, col):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03",
                                     edgecolor=col, facecolor=col, alpha=0.15, lw=2)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.62, titre, ha='center', va='center', fontsize=10, fontweight='bold', color='#1A237E')
        ax.text(x + w/2, y + h*0.32, sous, ha='center', va='center', fontsize=8, color='#37474F')

    # Direction
    box(0.35, 0.75, 0.3, 0.18, "Direction Générale", "Stratégie & Partenariats", "#1565C0")

    # Lignes
    ax.plot([0.5, 0.5], [0.75, 0.62], color='#90A4AE', lw=2)
    ax.plot([0.17, 0.83], [0.62, 0.62], color='#90A4AE', lw=2)
    ax.plot([0.17, 0.17], [0.62, 0.50], color='#90A4AE', lw=2)
    ax.plot([0.5, 0.5], [0.62, 0.50], color='#90A4AE', lw=2)
    ax.plot([0.83, 0.83], [0.62, 0.50], color='#90A4AE', lw=2)

    # 3 Pôles
    box(0.04, 0.32, 0.26, 0.18, "Pôle Conseil RSE", "Audit & Reporting ESG", "#2E7D32")
    box(0.37, 0.32, 0.26, 0.18, "Pôle IA & Data", "R&D • NLP • LLM • Vision", "#6A1B9A")
    box(0.70, 0.32, 0.26, 0.18, "Pôle Opérations", "Relation Clients & Déploiement", "#EF6C00")

    # Projet PFE
    rect_pfe = patches.FancyBboxPatch((0.37, 0.05), 0.26, 0.15, boxstyle="round,pad=0.03",
                                      edgecolor='#D81B60', facecolor='#FCE4EC', lw=2, ls='--')
    ax.add_patch(rect_pfe)
    ax.plot([0.5, 0.5], [0.32, 0.20], color='#D81B60', lw=2, ls=':')
    ax.text(0.5, 0.14, "Projet PFE (Ce travail)", ha='center', va='center', fontsize=9, fontweight='bold', color='#AD1457')
    ax.text(0.5, 0.08, "Chatbot ESG Intelligent", ha='center', va='center', fontsize=8, color='#37474F')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    sauver(fig, "fig_organigramme_rse_time.png")

# ─────────────────────────────────────────────────────────────────────
# 3. MÉTHODOLOGIE CRISP-DM ADAPTÉE À L'IA ESG
# ─────────────────────────────────────────────────────────────────────
def generer_crisp_dm():
    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor='white')
    ax.axis('off')

    etapes = [
        (0.25, 0.80, "1. Compréhension Métier", "Exigences GRI, CSRD/ESRS\net besoins des analystes", "#1565C0"),
        (0.75, 0.80, "2. Compréhension Données", "Corpus de 33 rapports RSE\net extraction multimodale", "#00838F"),
        (0.85, 0.40, "3. Préparation Données", "Segmentation et annotation\nmanuelle de 3 872 paragraphes", "#2E7D32"),
        (0.65, 0.10, "4. Modélisation Multi-Modèles", "CNN Léger, CamemBERT,\nspaCy NER et RAG ChromaDB", "#6A1B9A"),
        (0.35, 0.10, "5. Évaluation Expérimentale", "Benchmark, matrices de confusion\net gain filet sémantique (+25%)", "#C2185B"),
        (0.15, 0.40, "6. Déploiement Applicatif", "FastAPI, Streamlit\net tableau de bord décisionnel", "#EF6C00")
    ]

    for x, y, t, s, col in etapes:
        rect = patches.FancyBboxPatch((x-0.16, y-0.08), 0.32, 0.16, boxstyle="round,pad=0.03",
                                      facecolor=col, edgecolor=col, alpha=0.15, lw=2)
        ax.add_patch(rect)
        ax.text(x, y+0.02, t, ha='center', va='center', fontsize=9, fontweight='bold', color=col)
        ax.text(x, y-0.04, s, ha='center', va='center', fontsize=7.5, color='#263238')

    # Flèches du cycle
    coords = [(0.41, 0.80, 0.59, 0.80), (0.75, 0.72, 0.80, 0.48), (0.80, 0.32, 0.70, 0.18),
              (0.51, 0.10, 0.49, 0.10), (0.23, 0.18, 0.18, 0.32), (0.18, 0.48, 0.23, 0.72)]
    for x1, y1, x2, y2 in coords:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=2, color='#78909C'))

    ax.text(0.5, 0.5, "Démarche\nCRISP-DM\nItérative ESG", ha='center', va='center',
            fontsize=12, fontweight='bold', color='#37474F')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.95)
    sauver(fig, "fig_crisp_dm.png")

# ─────────────────────────────────────────────────────────────────────
# 4. ARCHITECTURE DU CNN LÉGER CUSTOM (ESG_CNN_Light)
# ─────────────────────────────────────────────────────────────────────
def generer_cnn_light():
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='white')
    ax.axis('off')

    couches = [
        ("Entrée Image", "Page PDF\n224×224×3", "#455A64", 0.08),
        ("Bloc Conv 1", "Conv2d(3→16)\nBatchNorm + ReLU\nMaxPool2d(2×2)\n[112×112×16]", "#1565C0", 0.26),
        ("Bloc Conv 2", "Conv2d(16→32)\nBatchNorm + ReLU\nMaxPool2d(2×2)\n[56×56×32]", "#2E7D32", 0.46),
        ("Bloc Conv 3", "Conv2d(32→64)\nBatchNorm + ReLU\nMaxPool2d(2×2)\n[28×28×64]", "#6A1B9A", 0.66),
        ("Tête de Décision", "AdaptiveAvgPool(1×1)\nDropout(30%)\nDense(64 → 2)\nSoftmax Scoring", "#EF6C00", 0.86)
    ]

    for t, s, col, x in couches:
        rect = patches.FancyBboxPatch((x-0.08, 0.2), 0.16, 0.6, boxstyle="round,pad=0.03",
                                      facecolor=col, edgecolor=col, alpha=0.18, lw=2)
        ax.add_patch(rect)
        ax.text(x, 0.72, t, ha='center', va='center', fontsize=9.5, fontweight='bold', color=col)
        ax.text(x, 0.45, s, ha='center', va='center', fontsize=8, color='#263238', linespacing=1.3)

    # Flèches
    for i in range(len(couches)-1):
        x1 = couches[i][3] + 0.08
        x2 = couches[i+1][3] - 0.08
        ax.annotate("", xy=(x2, 0.5), xytext=(x1, 0.5),
                    arrowprops=dict(arrowstyle="->", lw=2.5, color='#455A64'))

    ax.set_title("Architecture du Réseau Convolutif Léger Personnalisé (ESG_CNN_Light) conçu pour CPU",
                 fontsize=11, fontweight='bold', pad=15)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.1, 0.9)
    sauver(fig, "fig_cnn_light_architecture.png")

# ─────────────────────────────────────────────────────────────────────
# 5. SCHÉMA DU PIPELINE RAG (ChromaDB + Mistral 7B)
# ─────────────────────────────────────────────────────────────────────
def generer_schema_rag():
    fig, ax = plt.subplots(figsize=(9, 5), facecolor='white')
    ax.axis('off')

    # Boîtes
    def b(x, y, w, h, t, s, col):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                      facecolor=col, edgecolor=col, alpha=0.15, lw=2)
        ax.add_patch(rect)
        ax.text(x+w/2, y+h*0.65, t, ha='center', va='center', fontsize=9.5, fontweight='bold', color=col)
        ax.text(x+w/2, y+h*0.35, s, ha='center', va='center', fontsize=8, color='#263238')

    b(0.05, 0.70, 0.25, 0.22, "1. Question Utilisateur", "Langage Naturel\n(ex: 'Émissions Scope 1?')", "#1565C0")
    b(0.38, 0.70, 0.25, 0.22, "2. Modèle d'Embedding", "Sentence-Transformers\nMiniLM (384D)", "#00838F")
    b(0.70, 0.70, 0.25, 0.22, "3. Base Vectorielle", "ChromaDB\nRecherche k-NN (cosinus)", "#2E7D32")

    b(0.70, 0.20, 0.25, 0.22, "4. Passages Pertinents", "Top-k paragraphes\n+ Pages & Score CNN", "#F9A825")
    b(0.38, 0.20, 0.25, 0.22, "5. LLM Local", "Mistral 7B (Ollama)\nPrompt Anti-Hallucination", "#6A1B9A")
    b(0.05, 0.20, 0.25, 0.22, "6. Réponse Sourcée", "Texte clair + citations\ndes pages exactes", "#2E7D32")

    # Flèches
    ax.annotate("", xy=(0.38, 0.81), xytext=(0.30, 0.81), arrowprops=dict(arrowstyle="->", lw=2, color='#455A64'))
    ax.annotate("", xy=(0.70, 0.81), xytext=(0.63, 0.81), arrowprops=dict(arrowstyle="->", lw=2, color='#455A64'))
    ax.annotate("", xy=(0.82, 0.42), xytext=(0.82, 0.70), arrowprops=dict(arrowstyle="->", lw=2, color='#455A64'))
    ax.annotate("", xy=(0.63, 0.31), xytext=(0.70, 0.31), arrowprops=dict(arrowstyle="->", lw=2, color='#455A64'))
    ax.annotate("", xy=(0.30, 0.31), xytext=(0.38, 0.31), arrowprops=dict(arrowstyle="->", lw=2, color='#455A64'))

    ax.set_title("Architecture RAG (Retrieval-Augmented Generation) du Chatbot ESG", fontsize=11, fontweight='bold', pad=15)
    ax.set_xlim(0, 1)
    ax.set_ylim(0.1, 0.98)
    sauver(fig, "fig_rag_architecture.png")

# ─────────────────────────────────────────────────────────────────────
# 6. ARCHITECTURE GLOBALE MULTI-MODÈLES DU SYSTÈME
# ─────────────────────────────────────────────────────────────────────
def generer_architecture_globale():
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    ax.axis('off')

    # 4 Grandes colonnes
    etapes = [
        (0.08, "Ingestion & Vision", ["Rapport PDF", "pdf2image (Poppler)", "ESG_CNN_Light", "Scoring softmax"], "#37474F"),
        (0.33, "Extraction & NLP", ["pdfplumber / EasyOCR", "Segmentation textes", "CamemBERT (E/S/G)", "spaCy NER Custom"], "#1565C0"),
        (0.58, "Indexation & Audit", ["ChromaDB (384D)", "Métadonnées CNN", "Moteur GRI Hybride", "Filet Sémantique"], "#2E7D32"),
        (0.83, "Interaction & RAG", ["Mistral 7B (Ollama)", "Prompt Guardrail", "FastAPI Backend", "Dashboard Streamlit"], "#6A1B9A")
    ]

    for x, titre, items, col in etapes:
        rect = patches.FancyBboxPatch((x-0.10, 0.15), 0.20, 0.75, boxstyle="round,pad=0.03",
                                      facecolor=col, edgecolor=col, alpha=0.10, lw=2)
        ax.add_patch(rect)
        ax.text(x, 0.85, titre, ha='center', va='center', fontsize=10, fontweight='bold', color=col)
        for idx, it in enumerate(items):
            y_it = 0.70 - idx * 0.15
            rect_it = patches.FancyBboxPatch((x-0.08, y_it-0.05), 0.16, 0.10, boxstyle="round,pad=0.02",
                                             facecolor='white', edgecolor=col, lw=1.5)
            ax.add_patch(rect_it)
            ax.text(x, y_it, it, ha='center', va='center', fontsize=8, color='#263238')

    # Flèches inter-modules
    for i in range(len(etapes)-1):
        x1 = etapes[i][0] + 0.10
        x2 = etapes[i+1][0] - 0.10
        ax.annotate("", xy=(x2, 0.52), xytext=(x1, 0.52),
                    arrowprops=dict(arrowstyle="->", lw=2.5, color='#455A64'))

    ax.set_title("Architecture Multi-Modèles Intégrée de la Solution ESG Chatbot", fontsize=12, fontweight='bold', pad=15)
    ax.set_xlim(-0.04, 1.0)
    ax.set_ylim(0.1, 0.95)
    sauver(fig, "fig_architecture_globale.png")

# ─────────────────────────────────────────────────────────────────────
# 7. DIAGRAMME DE CAS D'UTILISATION (UML)
# ─────────────────────────────────────────────────────────────────────
def generer_cas_utilisation():
    fig, ax = plt.subplots(figsize=(8.5, 5), facecolor='white')
    ax.axis('off')

    # Cadre Système
    rect_sys = patches.FancyBboxPatch((0.28, 0.08), 0.68, 0.84, boxstyle="square,pad=0.02",
                                      facecolor='#F8FAFC', edgecolor='#64748B', lw=2)
    ax.add_patch(rect_sys)
    ax.text(0.62, 0.88, "Système Chatbot ESG Intelligent", ha='center', fontsize=11, fontweight='bold', color='#1E293B')

    # Acteur : Analyste RSE / Auditeur
    ax.plot([0.10, 0.10], [0.55, 0.40], color='#1E293B', lw=2) # corps
    c = patches.Circle((0.10, 0.62), 0.05, color='#1E293B') # tête
    ax.add_patch(c)
    ax.plot([0.05, 0.15], [0.50, 0.50], color='#1E293B', lw=2) # bras
    ax.plot([0.10, 0.05], [0.40, 0.28], color='#1E293B', lw=2) # jambe G
    ax.plot([0.10, 0.15], [0.40, 0.28], color='#1E293B', lw=2) # jambe D
    ax.text(0.10, 0.20, "Analyste RSE /\nAuditeur ESG", ha='center', fontsize=9, fontweight='bold', color='#1E293B')

    cas = [
        (0.62, 0.75, "Importer et analyser un rapport RSE (PDF)"),
        (0.62, 0.60, "Poser des questions en langage naturel"),
        (0.62, 0.45, "Consulter les réponses avec citations de pages et score CNN"),
        (0.62, 0.30, "Vérifier la conformité réglementaire (GRI / ESRS)"),
        (0.62, 0.15, "Exporter le rapport d'audit et la conversation en PDF")
    ]

    for x, y, texte in cas:
        ellipse = patches.FancyBboxPatch((x-0.28, y-0.05), 0.56, 0.10, boxstyle="round,pad=0.03",
                                        facecolor='#FFFFFF', edgecolor='#0284C7', lw=1.5)
        ax.add_patch(ellipse)
        ax.text(x, y, texte, ha='center', va='center', fontsize=8.5, color='#0F172A')
        ax.plot([0.15, x-0.28], [0.50, y], color='#94A3B8', lw=1.2, ls='--')

    ax.set_xlim(0, 1)
    ax.set_ylim(0.05, 0.95)
    sauver(fig, "fig_cas_utilisation.png")

if __name__ == "__main__":
    generer_logo_rse_time()
    generer_organigramme()
    generer_crisp_dm()
    generer_cnn_light()
    generer_schema_rag()
    generer_architecture_globale()
    generer_cas_utilisation()
    print("[TERMINE] Tous les schémas professionnels ont été générés avec succès !")
