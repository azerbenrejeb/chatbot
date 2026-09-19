"""
MODULE 2 — Prétraitement et segmentation du texte extrait.
Segmente le texte brut en paragraphes exploitables pour CamemBERT.
"""
import re
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import MIN_PARAGRAPH_LENGTH


def nettoyer_texte(texte):
    """
    Nettoie le texte brut extrait du PDF.
    - Supprime les espaces multiples
    - Normalise les sauts de ligne
    - Supprime les caractères de contrôle
    """
    # Supprimer les caractères de contrôle
    texte = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texte)
    # Normaliser les espaces
    texte = re.sub(r'[ \t]+', ' ', texte)
    # Normaliser les sauts de ligne multiples
    texte = re.sub(r'\n{3,}', '\n\n', texte)
    return texte.strip()


def segmenter_paragraphes(texte, min_longueur=None):
    """
    Segmente le texte en paragraphes individuels.
    
    Args:
        texte: Texte brut à segmenter
        min_longueur: Longueur minimale d'un paragraphe (défaut: config)
    
    Returns:
        Liste de paragraphes nettoyés
    """
    if min_longueur is None:
        min_longueur = MIN_PARAGRAPH_LENGTH

    # Nettoyer le texte
    texte = nettoyer_texte(texte)

    # Segmenter par double saut de ligne
    paragraphes = texte.split('\n\n')

    # Filtrer et nettoyer
    result = []
    for p in paragraphes:
        p = p.strip()
        # Fusionner les sauts de ligne simples (continuation de phrase)
        p = re.sub(r'\n', ' ', p)
        p = re.sub(r'\s+', ' ', p)
        if len(p) >= min_longueur:
            result.append(p)

    return result


def traiter_pages(pages_texte):
    """
    Traite une liste de pages extraites et retourne des paragraphes
    avec métadonnées de page.
    
    Args:
        pages_texte: Liste de {'page': num, 'texte': texte}
    
    Returns:
        Liste de {'page': num, 'paragraphe': texte}
    """
    tous_paragraphes = []

    for page_data in pages_texte:
        num_page = page_data['page']
        texte = page_data['texte']
        paragraphes = segmenter_paragraphes(texte)

        for para in paragraphes:
            tous_paragraphes.append({
                'page': num_page,
                'paragraphe': para
            })

    print(f"[OK] {len(tous_paragraphes)} paragraphes segmentes depuis {len(pages_texte)} pages")
    return tous_paragraphes


if __name__ == "__main__":
    # Test avec un exemple
    exemple = """
    Les émissions de CO2 de l'entreprise s'élèvent à 45 200 tCO2e en 2023, 
    soit une réduction de 15% par rapport à 2022.
    
    Le conseil d'administration compte 12 membres dont 4 femmes, 
    représentant 33% du total.
    
    Page courte.
    """
    paragraphes = segmenter_paragraphes(exemple)
    for i, p in enumerate(paragraphes):
        print(f"[{i+1}] {p}")
