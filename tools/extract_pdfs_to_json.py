"""
Extraction batch des rapports PDF vers data/processed/*_extracted.json.

Ce script sert a enrichir le dataset texte. Il extrait le texte avec PyMuPDF,
plus rapide que pdfplumber pour traiter beaucoup de rapports.

Par defaut, il ignore volontairement:
- les PDF vides;
- les rapports clairement non ESG;
- les JSON deja presents, sauf avec --overwrite.

Avec --include-all, il extrait aussi les rapports non ESG pour que le chatbot
puisse repondre sur tout le corpus.
"""
import argparse
import json
import re
from pathlib import Path
import sys

import fitz

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import PROCESSED_DIR, RAW_PDF_DIR, create_directories


NON_ESG_NAME_HINTS = [
    "world-stats",
    "pocketbook",
    "table03",
]

ESG_NAME_HINTS = [
    "esg",
    "rse",
    "sustainable",
    "sustainability",
    "durable",
    "annuel-integre",
    "rapport-annuel-integre",
]

ESG_TEXT_HINTS = [
    "esg",
    "rse",
    "developpement durable",
    "développement durable",
    "responsabilite societale",
    "responsabilité sociétale",
    "environnement",
    "gouvernance",
    "emissions",
    "émissions",
    "co2",
    "scope 1",
    "scope 2",
    "gri",
    "csrd",
]


def slug_from_pdf(pdf_path):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", pdf_path.stem)


def looks_non_esg_by_name(pdf_path):
    name = pdf_path.name.lower()
    return any(hint in name for hint in NON_ESG_NAME_HINTS)


def looks_esg_by_name(pdf_path):
    name = pdf_path.name.lower()
    return any(hint in name for hint in ESG_NAME_HINTS)


def looks_esg_by_text(sample_text):
    lowered = sample_text.lower()
    score = sum(1 for hint in ESG_TEXT_HINTS if hint in lowered)
    return score >= 2


def extract_pdf(pdf_path, output_path, max_pages=None, include_all=False):
    doc = fitz.open(pdf_path)
    pages = []
    sample_parts = []

    total_pages = len(doc)
    pages_to_read = min(total_pages, max_pages) if max_pages else total_pages

    for page_index in range(pages_to_read):
        page = doc.load_page(page_index)
        text = page.get_text("text").strip()
        if page_index < 12:
            sample_parts.append(text)
        pages.append({
            "page_number": page_index + 1,
            "text": text,
            "tables": [],
            "has_text": bool(text),
            "char_count": len(text),
        })

    sample_text = "\n".join(sample_parts)
    if not include_all and not looks_esg_by_name(pdf_path) and not looks_esg_by_text(sample_text):
        doc.close()
        return "skipped_non_esg", total_pages, 0

    data = {
        "metadata": {
            "nom_fichier": pdf_path.name,
            "nombre_pages": total_pages,
            "chemin": str(pdf_path),
            "extracteur": "PyMuPDF",
        },
        "pages": pages,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    doc.close()
    return "extracted", total_pages, sum(1 for page in pages if page["has_text"])


def main():
    parser = argparse.ArgumentParser(description="Extrait les PDF ESG/RSE en JSON.")
    parser.add_argument("--overwrite", action="store_true", help="Recree aussi les JSON existants.")
    parser.add_argument("--include-all", action="store_true", help="Extrait aussi les rapports non ESG.")
    parser.add_argument("--max-pages", type=int, default=None, help="Limite de pages par PDF, utile pour test.")
    args = parser.parse_args()

    create_directories()
    pdf_paths = sorted(RAW_PDF_DIR.glob("*.pdf"))
    print(f"[INFO] PDF trouves: {len(pdf_paths)}")

    for pdf_path in pdf_paths:
        output_path = PROCESSED_DIR / f"{slug_from_pdf(pdf_path)}_extracted.json"

        if pdf_path.stat().st_size == 0:
            print(f"[SKIP] PDF vide: {pdf_path.name}")
            continue
        if looks_non_esg_by_name(pdf_path) and not args.include_all:
            print(f"[SKIP] Rapport non ESG par nom: {pdf_path.name}")
            continue
        if output_path.exists() and not args.overwrite:
            print(f"[SKIP] JSON deja present: {output_path.name}")
            continue

        try:
            status, total_pages, text_pages = extract_pdf(
                pdf_path,
                output_path,
                max_pages=args.max_pages,
                include_all=args.include_all,
            )
            if status == "extracted":
                print(f"[OK] {pdf_path.name}: {text_pages}/{total_pages} pages avec texte")
            else:
                print(f"[SKIP] Rapport non ESG par contenu: {pdf_path.name}")
        except Exception as exc:
            print(f"[ERR] {pdf_path.name}: {exc}")


if __name__ == "__main__":
    main()
