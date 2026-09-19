"""
MODULE 2 — Extraction de texte depuis les pages ESG.
Utilise pdfplumber pour extraire le texte et camelot pour les tableaux.
"""
import pdfplumber
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import MIN_TEXT_LENGTH


def extraire_texte(pdf_path, pages_esg=None):
    """
    Extrait le texte des pages identifiées comme ESG par le CNN.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        pages_esg: Liste des numéros de pages ESG (0-indexed).
                   Si None, extrait toutes les pages.
    
    Returns:
        Liste de dictionnaires {'page': num_page, 'texte': texte}
    """
    textes = []
    with pdfplumber.open(pdf_path) as pdf:
        pages_to_process = pages_esg if pages_esg is not None else range(len(pdf.pages))

        for num_page in pages_to_process:
            if num_page >= len(pdf.pages):
                continue
            page = pdf.pages[num_page]
            texte = page.extract_text()
            if texte and len(texte) > MIN_TEXT_LENGTH:
                textes.append({
                    'page': num_page + 1,  # 1-indexed pour l'affichage
                    'texte': texte.strip()
                })

    print(f"[OK] {len(textes)} pages extraites depuis {Path(pdf_path).name}")
    return textes


def extraire_tableaux(pdf_path, pages_esg=None):
    """
    Extrait les tableaux des pages ESG.
    Utilise camelot si disponible, sinon pdfplumber tables.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
        pages_esg: Liste des numéros de pages ESG (0-indexed)
    
    Returns:
        Liste de dictionnaires {'page': num_page, 'tableau': texte_tableau}
    """
    tableaux = []

    try:
        import camelot
        pages_str = ','.join(str(p + 1) for p in pages_esg) if pages_esg else 'all'
        tables = camelot.read_pdf(str(pdf_path), pages=pages_str, flavor='stream')
        for table in tables:
            texte_tableau = table.df.to_string(index=False)
            if len(texte_tableau.strip()) > MIN_TEXT_LENGTH:
                tableaux.append({
                    'page': table.page,
                    'tableau': texte_tableau
                })
        print(f"[OK] {len(tableaux)} tableaux extraits avec camelot")
    except ImportError:
        # Fallback : utiliser pdfplumber pour les tableaux
        print("[INFO] camelot non disponible, utilisation de pdfplumber pour les tableaux")
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_process = pages_esg if pages_esg is not None else range(len(pdf.pages))
            for num_page in pages_to_process:
                if num_page >= len(pdf.pages):
                    continue
                page = pdf.pages[num_page]
                tables = page.extract_tables()
                for table in tables:
                    rows = []
                    for row in table:
                        cells = [str(cell) if cell else '' for cell in row]
                        rows.append(' | '.join(cells))
                    texte_tableau = '\n'.join(rows)
                    if len(texte_tableau.strip()) > MIN_TEXT_LENGTH:
                        tableaux.append({
                            'page': num_page + 1,
                            'tableau': texte_tableau
                        })
        print(f"[OK] {len(tableaux)} tableaux extraits avec pdfplumber")
    except Exception as e:
        print(f"[ERR] Erreur extraction tableaux : {e}")

    return tableaux


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1:
        pdf = _sys.argv[1]
        textes = extraire_texte(pdf)
        for t in textes[:3]:
            print(f"\n--- Page {t['page']} ---")
            print(t['texte'][:200] + "...")
