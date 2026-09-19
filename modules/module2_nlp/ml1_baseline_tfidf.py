"""
MODULE 3 (BASELINE) — Classification de paragraphes ESG avec TF-IDF et Régression Logistique.
Ce modèle sert de référence rapide et légère avant les modèles d'apprentissage profond.
"""
import pickle
import pandas as pd
from pathlib import Path
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import ML_CLASSES, ML_DATASET_DIR, MODELS_DIR


def charger_dataset():
    """
    Charge le dataset CSV annoté.
    Format attendu : texte,label
    """
    csv_path = ML_DATASET_DIR / "classification" / "ml_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset non trouvé : {csv_path}")

    df = pd.read_csv(csv_path)
    if 'texte' not in df.columns or 'label' not in df.columns:
        raise ValueError("Le CSV doit contenir les colonnes 'texte' et 'label'")

    # Nettoyage simple des lignes vides
    df = df.dropna(subset=['texte', 'label'])
    return df['texte'].tolist(), df['label'].tolist()


def train_tfidf():
    """
    Entraîne le classifieur baseline TF-IDF + Régression Logistique.
    """
    print("[STAT] Lancement de l'entraînement du baseline TF-IDF...")

    textes, labels = charger_dataset()

    # Découpage stratifié Train (70%), Val (15%), Test (15%) pour respecter le pipeline de validation
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        textes, labels, test_size=0.3, random_state=42, stratify=labels
    )
    val_texts, test_texts, val_labels, test_labels = train_test_split(
        test_texts, test_labels, test_size=0.5, random_state=42, stratify=test_labels
    )

    # 1. Vectorisation TF-IDF (Term Frequency - Inverse Document Frequency)
    # Convertit les paragraphes de texte brut en une matrice de caractéristiques numériques.
    # On utilise des n-grammes de mots (1 à 2) pour capturer les expressions composées (ex: 'scope 1').
    print("[STAT] Vectorisation des textes avec TF-IDF...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)
    X_test = vectorizer.transform(test_texts)

    # 2. Entraînement de la Régression Logistique
    # Modèle linéaire classique, extrêmement rapide et très robuste pour la classification de textes.
    print("[STAT] Entraînement de la Régression Logistique...")
    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        class_weight='balanced',
        random_state=42
    )
    
    model.fit(X_train, train_labels)

    # 3. Évaluation sur l'ensemble de validation
    val_preds = model.predict(X_val)
    val_acc = accuracy_score(val_labels, val_preds)
    print(f"[OK] Validation Accuracy: {val_acc*100:.2f}%")

    # 4. Sauvegarde des artefacts du modèle
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    vectorizer_path = MODELS_DIR / "tfidf_vectorizer.pkl"
    model_path = MODELS_DIR / "tfidf_baseline_model.pkl"

    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print(f"[OK] Modèle TF-IDF sauvegardé dans {MODELS_DIR}")
    return model, vectorizer


def predire(texte, model=None, vectorizer=None):
    """
    Prédit la classe ESG d'un paragraphe avec le baseline TF-IDF.
    """
    if model is None or vectorizer is None:
        vectorizer_path = MODELS_DIR / "tfidf_vectorizer.pkl"
        model_path = MODELS_DIR / "tfidf_baseline_model.pkl"
        
        if not vectorizer_path.exists() or not model_path.exists():
            raise FileNotFoundError("Les modèles TF-IDF entraînés sont introuvables. Lance d'abord l'entraînement.")
            
        with open(vectorizer_path, "rb") as f:
            vectorizer = pickle.load(f)
        with open(model_path, "rb") as f:
            model = pickle.load(f)

    # Transformer le texte et prédire
    features = vectorizer.transform([texte])
    pred = model.predict(features)[0]
    return pred


if __name__ == "__main__":
    train_tfidf()
