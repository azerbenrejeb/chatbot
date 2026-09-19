"""
MODULE 3 & 4 — Script d'évaluation unifié des modèles NLP (Classification ESG & NER).
Calcule les métriques globales et par classe, compare les modèles et génère des graphiques.
"""
import pickle
import pandas as pd
import numpy as np
import torch
from pathlib import Path
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import (
    ML_CLASSES, ML_DATASET_DIR, MODELS_DIR, GRAPHIQUES_DIR,
    NER_LABELS, NER_DATASET_DIR, ML_MAX_LENGTH, ML_MODEL_NAME
)
# Importer les prédictions
from modules.module2_nlp import ml1_baseline_tfidf
from modules.module2_nlp import ml1_random_forest
from modules.module2_nlp import ml2_ner_spacy

# Pour CamemBERT
from transformers import CamembertTokenizer, CamembertForSequenceClassification


def charger_test_dataset():
    """Charge l'ensemble de test de classification RSE."""
    csv_path = ML_DATASET_DIR / "classification" / "ml_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset non trouvé : {csv_path}")

    df = pd.read_csv(csv_path).dropna(subset=['texte', 'label'])
    textes = df['texte'].tolist()
    labels = df['label'].tolist()

    # Conserver le même découpage train/val/test stratifié
    _, test_texts, _, test_labels = train_test_split(
        textes, labels, test_size=0.3, random_state=42, stratify=labels
    )
    _, test_texts, _, test_labels = train_test_split(
        test_texts, test_labels, test_size=0.5, random_state=42, stratify=test_labels
    )

    return test_texts, test_labels


def charger_test_ner_dataset():
    """Charge l'ensemble de test NER."""
    from modules.module2_nlp.ml2_ner_spacy import charger_dataset_iob2
    all_data = charger_dataset_iob2()
    # Conserver le même découpage de test (les derniers 20%)
    split = int(0.8 * len(all_data))
    test_data = all_data[split:]
    return test_data


def evaluer_classification():
    """Évalue et compare les 3 classifieurs ESG."""
    print("\n" + "="*50)
    print("ÉVALUATION DES CLASSIFIEURS ESG (E/S/G)")
    print("="*50)

    try:
        test_texts, test_labels = charger_test_dataset()
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le dataset : {e}")
        return {}

    scores = {}
    y_test = test_labels

    # 1. Évaluation Baseline TF-IDF
    tfidf_model_path = MODELS_DIR / "tfidf_baseline_model.pkl"
    if tfidf_model_path.exists():
        print("\n--- Évaluation baseline TF-IDF + Régression Logistique ---")
        preds = [ml1_baseline_tfidf.predire(t) for t in test_texts]
        acc = accuracy_score(y_test, preds)
        report = classification_report(y_test, preds, output_dict=True)
        print(f"Accuracy : {acc*100:.2f}%")
        print(f"F1-Score Macro : {report['macro avg']['f1-score']*100:.2f}%")
        scores["TF-IDF Baseline"] = {
            "accuracy": acc,
            "f1_macro": report["macro avg"]["f1-score"],
            "report": report,
            "preds": preds
        }
    else:
        print("[WARN] Modèle TF-IDF Baseline introuvable. Lancez l'entraînement d'abord.")

    # 2. Évaluation Random Forest
    rf_model_path = MODELS_DIR / "rf_model.pkl"
    if rf_model_path.exists():
        print("\n--- Évaluation Random Forest ---")
        preds = [ml1_random_forest.predire(t) for t in test_texts]
        acc = accuracy_score(y_test, preds)
        report = classification_report(y_test, preds, output_dict=True)
        print(f"Accuracy : {acc*100:.2f}%")
        print(f"F1-Score Macro : {report['macro avg']['f1-score']*100:.2f}%")
        scores["Random Forest"] = {
            "accuracy": acc,
            "f1_macro": report["macro avg"]["f1-score"],
            "report": report,
            "preds": preds
        }
    else:
        print("[WARN] Modèle Random Forest introuvable. Lancez l'entraînement d'abord.")

    # 3. Évaluation CamemBERT Sequence Classification
    camembert_path = MODELS_DIR / "camembert_ml.pth"
    if camembert_path.exists():
        print("\n--- Évaluation Deep Learning CamemBERT ---")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        tokenizer = CamembertTokenizer.from_pretrained(ML_MODEL_NAME)
        model = CamembertForSequenceClassification.from_pretrained(ML_MODEL_NAME, num_labels=3)
        model.load_state_dict(torch.load(str(camembert_path), map_location=device, weights_only=True))
        model = model.to(device)
        model.eval()

        preds = []
        # Parcourir les textes par petits paquets pour l'évaluation sur CPU/GPU
        for i in range(0, len(test_texts), 32):
            batch_texts = test_texts[i:i+32]
            encoding = tokenizer(batch_texts, max_length=ML_MAX_LENGTH, padding='max_length',
                                 truncation=True, return_tensors='pt').to(device)
            with torch.no_grad():
                outputs = model(**encoding)
                batch_preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                preds.extend([ML_CLASSES[p] for p in batch_preds])

        acc = accuracy_score(y_test, preds)
        report = classification_report(y_test, preds, output_dict=True)
        print(f"Accuracy : {acc*100:.2f}%")
        print(f"F1-Score Macro : {report['macro avg']['f1-score']*100:.2f}%")
        scores["CamemBERT"] = {
            "accuracy": acc,
            "f1_macro": report["macro avg"]["f1-score"],
            "report": report,
            "preds": preds
        }
    else:
        print("[WARN] Modèle CamemBERT classification introuvable.")

    # Génération du graphique de comparaison
    if scores:
        generer_graphique_classification(scores)

    return scores


def generer_graphique_classification(scores):
    """Génère un graphique de comparaison pour les classifieurs."""
    GRAPHIQUES_DIR.mkdir(parents=True, exist_ok=True)
    
    model_names = list(scores.keys())
    accuracies = [scores[m]["accuracy"] * 100 for m in model_names]
    f1_macros = [scores[m]["f1_macro"] * 100 for m in model_names]

    x = np.arange(len(model_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    rects1 = ax.bar(x - width/2, accuracies, width, label='Accuracy', color='#38bdf8')
    rects2 = ax.bar(x + width/2, f1_macros, width, label='F1-Score Macro', color='#818cf8')

    ax.set_ylabel('Scores (%)')
    ax.set_title('Comparaison de performance des Classifieurs ESG')
    ax.set_xticks(x)
    ax.set_xticklabels(model_names)
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Ajouter des labels sur les barres
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # offset vertical
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    graph_path = GRAPHIQUES_DIR / "ml_classification_comparison.png"
    plt.savefig(graph_path, dpi=150)
    plt.close()
    print(f"[OK] Graphique comparatif classification sauvegardé dans : {graph_path}")


def evaluer_ner():
    """Évalue et compare les modèles NER spaCy et CamemBERT."""
    print("\n" + "="*50)
    print("ÉVALUATION DU COMPOSANT NER (ENTITÉS ESG)")
    print("="*50)

    try:
        test_data = charger_test_ner_dataset()
    except Exception as e:
        print(f"[ERREUR] Impossible de charger le dataset NER : {e}")
        return {}

    scores_ner = {}

    # 1. Évaluation spaCy NER
    spacy_path = MODELS_DIR / "spacy_ner"
    if spacy_path.exists():
        print("\n--- Évaluation spaCy NER Customisé ---")
        import spacy
        nlp = spacy.load(spacy_path)
        
        true_entities = 0
        pred_entities = 0
        correct_entities = 0

        for text, annotations in test_data:
            doc = nlp(text)
            
            # Entités réelles
            gold_entities = set(annotations["entities"])
            true_entities += len(gold_entities)
            
            # Entités prédites
            found_entities = set((ent.start_char, ent.end_char, ent.label_) for ent in doc.ents)
            pred_entities += len(found_entities)
            
            # Intersection exacte (position et étiquette)
            correct_entities += len(gold_entities.intersection(found_entities))

        precision = correct_entities / pred_entities if pred_entities > 0 else 0
        recall = correct_entities / true_entities if true_entities > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print(f"Precision NER : {precision*100:.2f}%")
        print(f"Recall NER : {recall*100:.2f}%")
        print(f"F1-Score NER Global : {f1*100:.2f}%")

        scores_ner["spaCy NER"] = {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
    else:
        print("[WARN] Modèle spaCy NER introuvable.")

    return scores_ner


def main():
    evaluer_classification()
    evaluer_ner()


if __name__ == "__main__":
    main()
