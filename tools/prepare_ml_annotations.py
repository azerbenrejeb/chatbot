"""
Prepare le dataset texte pour les modeles ML/NLP.

Objectif:
1. Lire les fichiers data/processed/*_extracted.json.
2. Ignorer les rapports qui ne sont pas assez ESG.
3. Decouper les textes en paragraphes.
4. Annoter automatiquement les paragraphes en:
   - Environnemental
   - Social
   - Gouvernance

Le script reste volontairement strict: un paragraphe ambigu est ignore.
Cela donne moins de lignes, mais des annotations plus propres pour viser
une meilleure accuracy.
"""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import ML_DATASET_DIR, PROCESSED_DIR, create_directories
from extraction.text_preprocessor import segmenter_paragraphes


LABEL_KEYWORDS = {
    "Environnemental": [
        "co2", "carbone", "climat", "scope 1", "scope 2", "scope 3", "ges",
        "emission", "emissions", "energie", "eau", "dechet", "dechets",
        "biodiversite", "pollution", "recyclage", "renouvelable",
        "environnement", "environnemental", "empreinte", "transition",
    ],
    "Social": [
        "social", "salarie", "salaries", "collaborateur", "collaborateurs",
        "employe", "employes", "formation", "sante", "securite", "accident",
        "diversite", "inclusion", "femme", "femmes", "parite", "handicap",
        "dialogue social", "droits humains", "droits de l'homme",
    ],
    "Gouvernance": [
        "gouvernance", "conseil d'administration", "administrateur",
        "administrateurs", "comite", "audit", "ethique", "corruption",
        "conformite", "risque", "risques", "transparence", "actionnaire",
        "actionnaires", "remuneration", "controle interne", "rgpd",
    ],
}

REPORT_ESG_KEYWORDS = [
    "esg", "rse", "developpement durable", "durabilite", "sustainability",
    "sustainable", "extra-financier", "gri", "csrd", "odd",
]

PAGE_EXCLUSION_KEYWORDS = [
    "sommaire", "table des matieres", "disclaimer", "mentions legales",
    "copyright", "glossaire", "index",
]


def fix_mojibake(text):
    """
    Repare une partie des textes affiches comme 'Ã©' au lieu de 'e accent'.

    Les JSON du projet contiennent parfois du texte UTF-8 relu comme Latin-1.
    Cette correction rend les mots-cles plus fiables avant annotation.
    """
    if not isinstance(text, str) or "Ã" not in text:
        return text or ""
    for source_encoding in ("cp1252", "latin1"):
        try:
            return text.encode(source_encoding).decode("utf-8")
        except UnicodeError:
            continue
    return text


def normalize(text):
    """Normalise le texte pour comparer avec les mots-cles."""
    text = fix_mojibake(text).lower()
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a",
        "î": "i", "ï": "i",
        "ô": "o",
        "ù": "u", "û": "u",
        "ç": "c",
        "œ": "oe",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip()


def keyword_score(text, keywords):
    normalized = normalize(text)
    return sum(1 for keyword in keywords if keyword in normalized)


NON_ESG_NAME_HINTS = [
    "world-stats",
    "pocketbook",
    "table03",
]


def is_esg_report(data):
    """Decide si un rapport entier merite d'etre garde pour l'annotation ML."""
    metadata = data.get("metadata", {})
    filename = normalize(metadata.get("nom_fichier", ""))
    
    # Exclure explicitement si le nom du fichier indique un rapport non-ESG
    if any(hint in filename for hint in NON_ESG_NAME_HINTS):
        return False
        
    all_text = " ".join(page.get("text", "") for page in data.get("pages", [])[:20])
    report_score = keyword_score(filename + " " + all_text, REPORT_ESG_KEYWORDS)
    return report_score >= 2


def is_page_noise(text):
    """Filtre les pages de sommaire/mentions quand elles sont pauvres en contenu ESG."""
    normalized = normalize(text)
    return any(keyword in normalized for keyword in PAGE_EXCLUSION_KEYWORDS)


def split_annotation_units(text):
    """
    Produit des morceaux de texte plus courts et plus propres.

    Les PDF extraient parfois toute une page comme un seul paragraphe. Pour le ML,
    un texte trop long melange souvent Environnemental, Social et Gouvernance.
    On decoupe donc les gros blocs en groupes de phrases.
    """
    units = []
    for paragraph in segmenter_paragraphes(text, min_longueur=80):
        if len(paragraph) <= 900:
            units.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        buffer = []
        buffer_len = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if buffer and buffer_len + len(sentence) > 900:
                chunk = " ".join(buffer).strip()
                if len(chunk) >= 80:
                    units.append(chunk)
                buffer = []
                buffer_len = 0

            buffer.append(sentence)
            buffer_len += len(sentence) + 1

        chunk = " ".join(buffer).strip()
        if len(chunk) >= 80:
            units.append(chunk)

    return units


def classify_paragraph(paragraph, min_score):
    """
    Retourne le label ESG le plus probable, ou None si le paragraphe est ambigu.

    La marge de 1 point evite d'annoter un paragraphe melange comme Gouvernance
    alors qu'il parle aussi fortement de Social ou Environnemental.
    """
    scores = {
        label: keyword_score(paragraph, keywords)
        for label, keywords in LABEL_KEYWORDS.items()
    }
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_label, best_score = ordered[0]
    second_score = ordered[1][1]

    if best_score < min_score:
        return None, scores
    if best_score == second_score:
        return None, scores
    return best_label, scores


def build_annotated_rows(min_score):
    rows = []
    skipped_reports = []
    kept_reports = []

    for json_path in sorted(PROCESSED_DIR.glob("*_extracted.json")):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = fix_mojibake(data.get("metadata", {}).get("nom_fichier", json_path.name))
        if not is_esg_report(data):
            skipped_reports.append(filename)
            continue

        kept_reports.append(filename)
        for page in data.get("pages", []):
            page_text = fix_mojibake(page.get("text", ""))
            if page.get("char_count", 0) < 80 or is_page_noise(page_text):
                continue

            for paragraph in split_annotation_units(page_text):
                label, scores = classify_paragraph(paragraph, min_score=min_score)
                if label is None:
                    continue

                rows.append({
                    "texte": paragraph,
                    "label": label,
                    "rapport": filename,
                    "page": page.get("page_number", ""),
                    "score_env": scores["Environnemental"],
                    "score_social": scores["Social"],
                    "score_gouv": scores["Gouvernance"],
                })

    return rows, kept_reports, skipped_reports


def write_dataset(output_path, min_score):
    rows, kept_reports, skipped_reports = build_annotated_rows(min_score=min_score)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["texte", "label", "rapport", "page", "score_env", "score_social", "score_gouv"],
        )
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["label"] for row in rows)
    print(f"[OK] Dataset ecrit: {output_path}")
    print(f"[OK] Paragraphes annotes: {len(rows)}")
    print("[OK] Repartition: " + ", ".join(f"{label}={counts[label]}" for label in LABEL_KEYWORDS))
    print("[INFO] Rapports gardes: " + ", ".join(sorted(set(kept_reports))))
    if skipped_reports:
        print("[INFO] Rapports ignores car non ESG: " + ", ".join(sorted(set(skipped_reports))))


def main():
    parser = argparse.ArgumentParser(description="Prepare le CSV d'annotation ML ESG.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ML_DATASET_DIR / "classification" / "ml_dataset.csv",
        help="Chemin du CSV genere.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=2,
        help="Score minimal de mots-cles pour garder un paragraphe.",
    )
    args = parser.parse_args()

    create_directories()
    write_dataset(args.output, min_score=args.min_score)


if __name__ == "__main__":
    main()
