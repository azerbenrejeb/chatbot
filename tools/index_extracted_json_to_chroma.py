"""
Indexe tous les rapports extraits JSON dans ChromaDB pour le chatbot.

Difference avec tools/index_ml_dataset_to_chroma.py:
- index_ml_dataset_to_chroma.py sert a indexer le dataset annote E/S/G;
- ce script sert au RAG complet du chatbot et couvre tous les rapports lisibles,
  meme ceux qui ne sont pas utiles pour entrainer le modele ML.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import PROCESSED_DIR
from extraction.text_preprocessor import segmenter_paragraphes
from modules.module3_llm_rag.vector_store import get_collection
from tools.prepare_ml_annotations import classify_paragraph, fix_mojibake, normalize


GENERAL_REPORT_KEYWORDS = [
    "population", "gdp", "gross domestic", "imports", "exports", "unemployment",
    "inflation", "statistics", "statistical", "world", "country", "countries",
]


def stable_id(report, page, text):
    raw = f"{report}|{page}|{text}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:18]
    return f"rag_{digest}"


def split_units(text, min_length=80, max_length=900):
    """Decoupe une page en blocs assez courts pour une recherche RAG precise."""
    units = []
    for paragraph in segmenter_paragraphes(text, min_longueur=min_length):
        if len(paragraph) <= max_length:
            units.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        buffer = []
        buffer_len = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if buffer and buffer_len + len(sentence) > max_length:
                chunk = " ".join(buffer).strip()
                if len(chunk) >= min_length:
                    units.append(chunk)
                buffer = []
                buffer_len = 0
            buffer.append(sentence)
            buffer_len += len(sentence) + 1

        chunk = " ".join(buffer).strip()
        if len(chunk) >= min_length:
            units.append(chunk)

    return units


def classify_for_rag(text):
    """
    Donne un label de metadonnee pour filtrage.

    Les paragraphes ESG gardent Environnemental/Social/Gouvernance.
    Les autres paragraphes restent accessibles au chatbot avec label General.
    """
    label, _ = classify_paragraph(text, min_score=2)
    if label:
        return label

    normalized = normalize(text)
    if any(keyword in normalized for keyword in GENERAL_REPORT_KEYWORDS):
        return "General"
    return "Autre"


def load_documents(max_docs=None):
    ids = []
    documents = []
    metadatas = []
    reports = set()

    for json_path in sorted(PROCESSED_DIR.glob("*_extracted.json")):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        report = fix_mojibake(data.get("metadata", {}).get("nom_fichier", json_path.name))
        reports.add(report)

        for page in data.get("pages", []):
            page_text = fix_mojibake(page.get("text", ""))
            if page.get("char_count", len(page_text)) < 80:
                continue

            for unit in split_units(page_text):
                label = classify_for_rag(unit)
                page_number = str(page.get("page_number", ""))
                ids.append(stable_id(report, page_number, unit))
                documents.append(unit)
                metadatas.append({
                    "rapport": report,
                    "page": page_number,
                    "label": label,
                    "annee": "N/A",
                    "source": "json_extracted",
                })

                if max_docs and len(documents) >= max_docs:
                    return ids, documents, metadatas, reports

    return ids, documents, metadatas, reports


def main():
    parser = argparse.ArgumentParser(description="Indexe tous les JSON extraits dans ChromaDB.")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-docs", type=int, default=None, help="Limite utile pour test.")
    args = parser.parse_args()

    ids, documents, metadatas, reports = load_documents(max_docs=args.max_docs)
    collection = get_collection()
    before = collection.count()

    for start in range(0, len(documents), args.batch_size):
        end = start + args.batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"[INFO] Indexation RAG: {min(end, len(documents))}/{len(documents)}")

    after = collection.count()
    print(f"[OK] Rapports couverts: {len(reports)}")
    print(f"[OK] Documents RAG traites: {len(documents)}")
    print(f"[OK] Chroma avant: {before}")
    print(f"[OK] Chroma apres: {after}")


if __name__ == "__main__":
    main()
