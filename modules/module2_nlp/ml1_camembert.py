"""
MODULE 3 (CAMEMBERT) — Classification multiclasse de paragraphes ESG avec CamemBERT.
Ce script utilise l'apprentissage profond (Deep Learning) pour classifier des paragraphes
dans les 3 piliers de la RSE : Environnemental (0), Social (1), Gouvernance (2).

Le modèle utilisé est 'camembert-base' (modèle pré-entraîné de type BERT adapté au français).
"""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, CamembertForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import (
    ML_CLASSES, ML_MODEL_NAME, ML_BATCH_SIZE, ML_EPOCHS,
    ML_LEARNING_RATE, ML_MAX_LENGTH, ML_DATASET_DIR, MODELS_DIR
)


class ESGTextDataset(Dataset):
    """
    Dataset PyTorch sur-mesure pour encapsuler et tokeniser nos textes ESG.
    Hérite de la classe de base torch.utils.data.Dataset.
    """

    def __init__(self, textes, labels, tokenizer, max_length=512):
        """
        Initialise le Dataset.
        :param textes: Liste de paragraphes de texte brut
        :param labels: Liste d'indices de labels associés (0, 1 ou 2)
        :param tokenizer: Le tokenizer CamembertTokenizer
        :param max_length: Longueur maximale autorisée pour les tokens d'entrée (512 par défaut)
        """
        self.textes = textes
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        """Retourne le nombre total de paragraphes dans le dataset."""
        return len(self.textes)

    def __getitem__(self, idx):
        """
        Récupère un élément du dataset à l'index donné, le normalise,
        le tokenise et le formate pour CamemBERT.
        """
        # Nettoyage des espaces multiples et retours à la ligne inutiles
        texte = " ".join(str(self.textes[idx]).strip().split())
        label = self.labels[idx]

        # L'encodage convertit le texte en identifiants numériques (input_ids)
        # et génère un attention_mask pour ignorer les tokens de remplissage (padding).
        encoding = self.tokenizer(
            texte,
            max_length=self.max_length,
            padding='max_length',     # Remplissage par zéros pour harmoniser les tailles de batch
            truncation=True,          # Coupe le texte s'il dépasse max_length tokens
            return_tensors='pt'       # Retourne des tenseurs PyTorch ('pt')
        )

        return {
            'input_ids': encoding['input_ids'].squeeze(),      # Tenseur 1D d'identifiants de tokens
            'attention_mask': encoding['attention_mask'].squeeze(),  # Tenseur 1D de masques de zéros/uns
            'label': torch.tensor(label, dtype=torch.long)      # Label converti en tenseur d'entier long
        }


def charger_dataset():
    """
    Charge le dataset de classification CSV et convertit les étiquettes en index numériques.
    """
    csv_path = ML_DATASET_DIR / "classification" / "ml_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset non trouvé : {csv_path}")

    df = pd.read_csv(csv_path)
    if 'texte' not in df.columns or 'label' not in df.columns:
        raise ValueError("Le CSV doit contenir les colonnes 'texte' et 'label'")

    # Associe chaque classe textuelle (ex: 'Social') à un indice entier unique (ex: 1)
    label_map = {cls: i for i, cls in enumerate(ML_CLASSES)}
    df['label_idx'] = df['label'].map(label_map)

    # Nettoyage des valeurs manquantes ou des classes erronées
    df = df.dropna(subset=['label_idx'])
    df['label_idx'] = df['label_idx'].astype(int)

    return df['texte'].tolist(), df['label_idx'].tolist()


def get_dataloaders(batch_size=32, max_length=128):
    """
    Crée les instances DataLoader (Train/Val/Test) à l'aide du découpage stratifié.
    La stratification permet de conserver la proportion d'exemples E, S, G dans chaque partition.
    """
    textes, labels = charger_dataset()

    # Initialisation du Tokenizer CamemBERT (version rapide compatible Fast)
    tokenizer = AutoTokenizer.from_pretrained(ML_MODEL_NAME)

    # Découpage stratifié : Train = 70%, Test = 30%
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        textes, labels, test_size=0.3, random_state=42, stratify=labels
    )
    # Découpage du bloc Test en Validation (15%) et Test Final (15%)
    val_texts, test_texts, val_labels, test_labels = train_test_split(
        test_texts, test_labels, test_size=0.5, random_state=42, stratify=test_labels
    )

    # Instanciation de nos datasets PyTorch personnalisés
    train_dataset = ESGTextDataset(train_texts, train_labels, tokenizer, max_length)
    val_dataset = ESGTextDataset(val_texts, val_labels, tokenizer, max_length)
    test_dataset = ESGTextDataset(test_texts, test_labels, tokenizer, max_length)

    # Création des DataLoader qui gèrent le chargement par batchs (paquets de données),
    # et mélange (shuffle) les données d'entraînement pour éviter les biais d'apprentissage.
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    print(f"[OK] Dataloaders CamemBERT: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)} (max_len={max_length})")
    return train_loader, val_loader, test_loader, tokenizer, train_labels


def get_model():
    """
    Instancie le modèle de classification de séquence CamemBERT.
    Ajoute une couche de classification linéaire (Linear Head) au-dessus de l'encodeur de base.
    """
    model = CamembertForSequenceClassification.from_pretrained(
        ML_MODEL_NAME,
        num_labels=len(ML_CLASSES) # Nombre de classes de sortie = 3 (Environnemental, Social, Gouvernance)
    )
    return model


def train_camembert(epochs=2, batch_size=32, max_length=128, lr=3e-5):
    """
    Boucle d'entraînement optimale du modèle CamemBERT :
    - CrossEntropyLoss standard sans distorsion de poids de classes
    - Optimiseur AdamW avec weight_decay léger (0.01)
    - Gradient Clipping (1.0) pour stabilité
    - Sauvegarde automatique du checkpoint à la meilleure Accuracy de validation
    """
    print(f"[STAT] Lancement de l'entraînement CamemBERT (epochs={epochs}, batch={batch_size}, max_len={max_length}, lr={lr})...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Appareil cible pour l'entraînement : {device}")

    train_loader, val_loader, _, tokenizer, _ = get_dataloaders(batch_size=batch_size, max_length=max_length)
    model = get_model().to(device)

    # Fonction de perte standard (sans déséquilibre artificiel)
    criterion = nn.CrossEntropyLoss()

    # Optimiseur AdamW
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)

    best_val_acc = 0.0
    best_val_loss = float('inf')
    model_path = MODELS_DIR / "camembert_ml.pth"

    for epoch in range(epochs):
        # --- PHASE D'ENTRAÎNEMENT ---
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for step, batch in enumerate(train_loader):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)

            optimizer.zero_grad()

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = criterion(logits, labels)

            loss.backward()

            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item() * input_ids.size(0)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        train_loss = total_loss / total
        train_acc = 100 * correct / total

        # --- PHASE DE VALIDATION ---
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                loss = criterion(outputs.logits, labels)
                val_loss += loss.item() * input_ids.size(0)

                preds = torch.argmax(outputs.logits, dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        epoch_val_loss = val_loss / val_total
        val_acc = 100 * val_correct / val_total

        print(f"Epoch [{epoch+1}/{epochs}] - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | Val Loss: {epoch_val_loss:.4f}, Val Acc: {val_acc:.2f}%", flush=True)

        # Sauvegarder si meilleure accuracy de validation (ou si même accuracy mais meilleure perte)
        if val_acc > best_val_acc or (val_acc == best_val_acc and epoch_val_loss < best_val_loss):
            best_val_acc = val_acc
            best_val_loss = epoch_val_loss
            torch.save(model.state_dict(), str(model_path))
            print(f"   --> [BEST CHECKPOINT] Sauvegardé avec Val Acc: {best_val_acc:.2f}% (Loss: {best_val_loss:.4f})", flush=True)

    print(f"\n[OK] Entraînement complété ! Meilleure validation accuracy : {best_val_acc:.2f}%", flush=True)


def predire(texte, model=None, tokenizer=None, max_length=128):
    """
    Effectue l'inférence (prédiction en temps réel) sur un paragraphe ESG unique.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(ML_MODEL_NAME)
    if model is None:
        model = get_model()
        model_path = MODELS_DIR / "camembert_ml.pth"
        if not model_path.exists():
            raise FileNotFoundError("Poids CamemBERT introuvables. Veuillez d'abord l'entraîner.")
        model.load_state_dict(torch.load(str(model_path), map_location=device, weights_only=True))
        model = model.to(device)

    # Nettoyage des espaces superflus
    texte_clean = " ".join(str(texte).strip().split())

    model.eval()
    encoding = tokenizer(
        texte_clean,
        max_length=max_length,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    ).to(device)

    with torch.no_grad():
        outputs = model(**encoding)
        pred = torch.argmax(outputs.logits, dim=1).item()

    return ML_CLASSES[pred]


if __name__ == "__main__":
    train_camembert()
