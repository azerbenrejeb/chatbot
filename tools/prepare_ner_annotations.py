"""
Script de préparation automatique du dataset NER au format IOB2.
Analyse les paragraphes de ml_dataset.csv et en extrait les entités ESG clés :
ANNEE, VALEUR, UNITE, TENDANCE, REFERENCE_GRI.
"""
import re
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import NER_DATASET_DIR, ML_DATASET_DIR, create_directories

# Dictionnaires et listes de mots-clés pour les heuristiques du NER
TENDANCE_KEYWORDS = {
    "reduit", "reduire", "reduction", "reduisons", "reduite", "reduites",
    "baisse", "baisser", "baisse", "baisses", "baisses", "diminue", "diminuer",
    "diminution", "diminuee", "diminuees", "augmente", "augmenter", "augmentation",
    "augmentee", "augmentees", "hausse", "hausses", "croissance", "accru", "accrue",
    "accrus", "accrues", "stable", "stabilite", "progression", "ameliore", "ameliorer",
    "amelioration", "prevenir", "eviter"
}

UNITE_KEYWORDS = {
    "%", "tco2e", "tco2", "tonnes", "tonne", "m3", "litres", "litre", "employes",
    "employe", "employees", "employee", "collaborateurs", "collaborateur",
    "collaboratrices", "collaboratrice", "femmes", "femme", "hommes", "homme",
    "salaries", "salarie", "salariees", "salariee", "mw", "mwh", "gwh", "kwh",
    "heures", "heure", "jours", "jour", "euros", "euro", "k€", "m€", "t", "kg", "g",
    "points", "point", "pourcent", "pourcents"
}

def clean_word(word):
    """Nettoie le mot des ponctuations superflues pour le matching de mots-clés."""
    return re.sub(r"[^\w%€-]", "", word).lower()

def is_year(word):
    """Détecte si le mot correspond à une année."""
    cleaned = clean_word(word)
    if cleaned.isdigit() and len(cleaned) == 4:
        year = int(cleaned)
        return 1980 <= year <= 2030
    return False

def is_value(word):
    """Détecte si le mot correspond à une valeur numérique RSE (sans être une année)."""
    cleaned = clean_word(word)
    # Supprimer les signes %, €, + ou - à la fin ou au début pour le test numérique
    cleaned_num = re.sub(r"^[+-]|[%%€]$", "", cleaned)
    # Remplacer les séparateurs de milliers ou décimaux (espace, virgule, point)
    cleaned_num = cleaned_num.replace(" ", "").replace(",", "").replace(".", "")
    if cleaned_num.isdigit() and not is_year(word):
        return True
    return False

def is_gri(word):
    """Détecte si le mot fait référence à une norme GRI."""
    cleaned = word.upper()
    if "GRI" in cleaned:
        return True
    # Format standard type 305-1 ou 401-2
    if re.match(r"^\d{3}-\d{1,2}$", word):
        return True
    return False

def tokenize_sentence(sentence):
    """Découpe une phrase en tokens en préservant la ponctuation."""
    # Sépare les mots des signes de ponctuation courants
    tokens = re.findall(r"[\w%€]+|[^\w\s]", sentence)
    return [t.strip() for t in tokens if t.strip()]

def split_into_sentences(text):
    """Découpe un paragraphe en phrases simples."""
    # Sépare grossièrement sur les points suivis d'espaces et majuscules
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def tag_sentence(sentence):
    """Annote une phrase au format IOB2 (sans I pour garder la config simple)."""
    tokens = tokenize_sentence(sentence)
    tagged = []
    
    for i, token in enumerate(tokens):
        word_lower = clean_word(token)
        
        # Par défaut
        label = "O"
        
        if is_year(token):
            label = "B-ANNEE"
        elif is_gri(token):
            label = "B-REFERENCE_GRI"
        elif word_lower in TENDANCE_KEYWORDS:
            label = "B-TENDANCE"
        elif is_value(token):
            label = "B-VALEUR"
        elif word_lower in UNITE_KEYWORDS:
            label = "B-UNITE"
        # Règle contextuelle : si le mot précédent ou suivant immédiat est une valeur,
        # et que ce mot ressemble à une unité RSE (ex: tCO2e, salariés, etc.)
        elif i > 0 and tagged[i-1][1] == "B-VALEUR" and (len(word_lower) > 1 or word_lower in UNITE_KEYWORDS):
            # Si le mot n'est pas une préposition courante
            if word_lower not in {"et", "ou", "de", "la", "le", "les", "des", "en", "pour", "dans", "par", "sur", "avec"}:
                label = "B-UNITE"
                
        tagged.append((token, label))
    return tagged

def generate_ner_dataset():
    """Génère le fichier ner_dataset.txt à partir de ml_dataset.csv."""
    csv_path = ML_DATASET_DIR / "classification" / "ml_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Le dataset de classification est manquant : {csv_path}")
        
    output_file = NER_DATASET_DIR / "ner_dataset.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[STAT] Lecture du CSV d'annotations classification : {csv_path}")
    sentences_count = 0
    annotated_tokens_count = 0
    
    with open(csv_path, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        for row in reader:
            paragraph = row.get("texte", "")
            if not paragraph:
                continue
                
            # Découper en phrases
            sentences = split_into_sentences(paragraph)
            for sentence in sentences:
                # Éviter les phrases trop courtes et sans intérêt informatif
                if len(sentence) < 25:
                    continue
                    
                tagged = tag_sentence(sentence)
                
                # On ne garde la phrase que s'il y a au moins une entité intéressante (pas que des 'O')
                labels = [label for _, label in tagged if label != "O"]
                if len(labels) >= 2: # Au moins deux entités (ex: une valeur et une année ou tendance)
                    sentences_count += 1
                    for token, label in tagged:
                        f_out.write(f"{token}\t{label}\n")
                        if label != "O":
                            annotated_tokens_count += 1
                    f_out.write("\n") # Séparateur de phrases
                    
    print(f"[OK] Fichier de dataset NER généré : {output_file}")
    print(f"[OK] Nombre de phrases annotées : {sentences_count}")
    print(f"[OK] Nombre de tokens d'entités annotés : {annotated_tokens_count}")

if __name__ == "__main__":
    create_directories()
    generate_ner_dataset()
