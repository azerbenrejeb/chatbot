"""
Point d'entrée pour entraîner l'ensemble des modèles NLP du Module 2.
Permet d'entraîner soit les modèles rapides (TF-IDF, Random Forest, spaCy NER),
soit l'intégralité des modèles (y compris CamemBERT Classification et NER).

Utilisation :
    python -m modules.module2_nlp.train_ml --only-fast   (recommandé pour test rapide)
    python -m modules.module2_nlp.train_ml               (entraînement complet)
"""
import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import ML_DATASET_DIR, create_directories

# Importer les scripts d'entraînement
from modules.module2_nlp.ml1_baseline_tfidf import train_tfidf
from modules.module2_nlp.ml1_random_forest import train_random_forest
from modules.module2_nlp.ml2_ner_spacy import train_spacy_ner


def main():
    parser = argparse.ArgumentParser(description="Orchestrateur d'entraînement des modèles NLP ESG.")
    parser.add_argument(
        "--only-fast",
        action="store_true",
        help="Entraîne uniquement les modèles rapides (TF-IDF, Random Forest, spaCy NER) en quelques minutes."
    )
    args = parser.parse_args()

    # Création des dossiers du projet
    create_directories()

    # 1. Vérification de l'existence des datasets
    classification_csv = ML_DATASET_DIR / "classification" / "ml_dataset.csv"
    ner_txt = ML_DATASET_DIR / "ner" / "ner_dataset.txt"

    if not classification_csv.exists():
        raise FileNotFoundError(
            f"Dataset classification manquant : {classification_csv}. "
            "Veuillez d'abord lancer : python tools/prepare_ml_annotations.py"
        )
        
    if not ner_txt.exists():
        raise FileNotFoundError(
            f"Dataset NER manquant : {ner_txt}. "
            "Veuillez d'abord lancer : python tools/prepare_ner_annotations.py"
        )

    print("\n" + "="*50)
    print("🚀 DÉBUT DE L'ENTRAÎNEMENT DE LA SUITE NLP ESG")
    print("="*50)

    # 2. Entraînement des modèles classiques (toujours entraînés)
    print("\n--- [MODÈLES CLASSIQUES] ---")
    train_tfidf()
    print("-" * 30)
    train_random_forest()
    
    # 3. Entraînement du modèle NER rapide spaCy (toujours entraîné)
    print("\n--- [MODÈLE NER SPACY] ---")
    train_spacy_ner(epochs=5, limit_sentences=1500)

    # 4. Entraînement facultatif des modèles de Deep Learning CamemBERT
    if not args.only-fast:
        print("\n--- [MODÈLES DEEP LEARNING CAMEMBERT] ---")
        
        # Inclusions dynamiques pour éviter de charger PyTorch/Transformers si non demandés
        from modules.module2_nlp.ml1_camembert import train_camembert
        from modules.module2_nlp.ner_camembert import train_ner as train_camembert_ner
        
        print("\n>> Entraînement de CamemBERT Paragraph Classification...")
        try:
            train_camembert()
        except Exception as e:
            print(f"[ERREUR] Échec de l'entraînement CamemBERT Classification : {e}")

        print("\n>> Entraînement de CamemBERT Token Classification (NER)...")
        try:
            train_camembert_ner()
        except Exception as e:
            print(f"[ERREUR] Échec de l'entraînement CamemBERT NER : {e}")

    print("\n" + "="*50)
    print("🎉 PROCESSUS D'ENTRAÎNEMENT COMPLET TERMINÉ AVEC SUCCÈS !")
    print("="*50)
    print("Pour évaluer les modèles, lancez :")
    print("  python -m modules.module2_nlp.evaluate_ml\n")


if __name__ == "__main__":
    main()
