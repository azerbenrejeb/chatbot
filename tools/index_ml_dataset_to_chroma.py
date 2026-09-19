"""
Indexe le dataset ML annote dans ChromaDB pour le RAG.

Le CSV attendu est:
data/ml_dataset/classification/ml_dataset.csv

Chaque ligne devient un document vectoriel avec metadonnees:
rapport, page, label.
"""
import argparse
import hashlib
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import ML_DATASET_DIR
from modules.module3_llm_rag.vector_store import get_collection


def stable_id(row):
    raw = f"{row['rapport']}|{row['page']}|{row['label']}|{row['texte']}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"ml_{digest}"


def main():
    parser = argparse.ArgumentParser(description="Indexe ml_dataset.csv dans ChromaDB.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=ML_DATASET_DIR / "classification" / "ml_dataset.csv",
        help="Chemin vers le CSV annote.",
    )
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(f"CSV introuvable: {args.csv}")

    df = pd.read_csv(args.csv).dropna(subset=["texte", "label", "rapport", "page"])
    df = df.drop_duplicates(subset=["texte", "label", "rapport", "page"]).reset_index(drop=True)

    collection = get_collection()
    before = collection.count()

    ids = [stable_id(row) for _, row in df.iterrows()]
    documents = df["texte"].astype(str).tolist()
    metadatas = [
        {
            "label": str(row["label"]),
            "page": str(row["page"]),
            "rapport": str(row["rapport"]),
            "annee": "N/A",
        }
        for _, row in df.iterrows()
    ]

    for start in range(0, len(documents), args.batch_size):
        end = start + args.batch_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"[INFO] Indexation Chroma: {min(end, len(documents))}/{len(documents)}")

    after = collection.count()
    print(f"[OK] ChromaDB documents avant: {before}")
    print(f"[OK] ChromaDB documents apres: {after}")
    print(f"[OK] Documents CSV traites: {len(documents)}")


if __name__ == "__main__":
    main()
