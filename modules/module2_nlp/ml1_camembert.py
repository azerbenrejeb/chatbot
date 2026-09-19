"""
MODULE 3 (CAMEMBERT) — Classification multiclasse de paragraphes ESG avec CamemBERT.
Ce script utilise l'apprentissage profond (Deep Learning) pour classifier des paragraphes
dans les 3 piliers de la RSE : Environnemental (0), Social (1), Gouvernance (2).

Le modèle utilisé est 'camembert-base' (modèle pré-entraîné de type BERT adapté au français).
"""
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import CamembertTokenizer, CamembertForSequenceClassification
from sklearn.model_selection import train_test_split
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
        Récupère un élément du dataset à l'index donné, le tokenise et le formate
        pour qu'il soit directement exploitable par CamemBERT.
        """
        texte = str(self.textes[idx])
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


def get_dataloaders():
    """
    Crée les instances DataLoader (Train/Val/Test) à l'aide du découpage stratifié.
    La stratification permet de conserver la proportion d'exemples E, S, G dans chaque partition.
    """
    textes, labels = charger_dataset()

    # Initialisation du Tokenizer CamemBERT
    # Il utilise le modèle d'encodage SentencePiece entraîné sur le corpus français OSCAR.
    tokenizer = CamembertTokenizer.from_pretrained(ML_MODEL_NAME)

    # Découpage stratifié : Train = 70%, Test = 30%
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        textes, labels, test_size=0.3, random_state=42, stratify=labels
    )
    # Découpage du bloc Test en Validation (15%) et Test Final (15%)
    val_texts, test_texts, val_labels, test_labels = train_test_split(
        test_texts, test_labels, test_size=0.5, random_state=42, stratify=test_labels
    )

    # Instanciation de nos datasets PyTorch personnalisés
    train_dataset = ESGTextDataset(train_texts, train_labels, tokenizer, ML_MAX_LENGTH)
    val_dataset = ESGTextDataset(val_texts, val_labels, tokenizer, ML_MAX_LENGTH)
    test_dataset = ESGTextDataset(test_texts, test_labels, tokenizer, ML_MAX_LENGTH)

    # Création des DataLoader qui gèrent le chargement par batchs (paquets de données),
    # et mélange (shuffle) les données d'entraînement pour éviter les biais d'apprentissage.
    train_loader = DataLoader(train_dataset, batch_size=ML_BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=ML_BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=ML_BATCH_SIZE, shuffle=False)

    print(f"[OK] Dataloaders CamemBERT: Train={len(train_dataset)}, Val={len(val_dataset)}, Test={len(test_dataset)}")
    return train_loader, val_loader, test_loader, tokenizer


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


def train_camembert():
    """
    Boucle d'entraînement principale du modèle CamemBERT de classification de paragraphes ESG.
    Optimise les poids en fonction de la perte CrossEntropy.
    """
    print("[STAT] Lancement de l'entraînement CamemBERT...")

    # Utilise la carte graphique (GPU CUDA) si disponible, sinon se rabat sur le processeur (CPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Appareil cible pour l'entraînement : {device}")

    train_loader, val_loader, _, tokenizer = get_dataloaders()
    model = get_model().to(device)

    # Optimiseur AdamW (Adam avec correction de la décroissance des poids ou weight decay)
    # Recommandé pour l'apprentissage profond sur Transformer avec un taux d'apprentissage faible.
    optimizer = torch.optim.AdamW(model.parameters(), lr=ML_LEARNING_RATE)
    
    best_val_loss = float('inf')
    model_path = MODELS_DIR / "camembert_ml.pth"

    for epoch in range(ML_EPOCHS):
        # 1. PHASE D'ENTRAÎNEMENT (Train)
        model.train()
        total_loss = 0
        correct = 0
        total = 0

        for batch in train_loader:
            # Transfert des tenseurs sur la puce GPU/CPU active
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['label'].to(device)

            # Remise à zéro des gradients pour éviter les accumulations
            optimizer.zero_grad()

            # Propagation avant (Forward Pass)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            
            # Calcul de la perte CrossEntropy
            loss = outputs.loss
            
            # Rétropropagation des erreurs (Backward Pass)
            loss.backward()
            
            # Ajustement des poids du réseau
            optimizer.step()

            # Métriques d'entraînement cumulées
            total_loss += loss.item() * input_ids.size(0)
            preds = torch.argmax(outputs.logits, dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        train_acc = 100 * correct / total

        # 2. PHASE D'ÉVALUATION (Validation)
        model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0

        # Désactive le calcul automatique des gradients pour économiser de la RAM/VRAM
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                labels = batch['label'].to(device)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                val_loss += outputs.loss.item() * input_ids.size(0)
                preds = torch.argmax(outputs.logits, dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += labels.size(0)

        epoch_val_loss = val_loss / val_total
        val_acc = 100 * val_correct / val_total

        print(f"Epoch [{epoch+1}/{ML_EPOCHS}] - Train Acc: {train_acc:.2f}% | Val Loss: {epoch_val_loss:.4f}, Val Acc: {val_acc:.2f}%")

        # 3. SAUVEGARDE DU MEILLEUR MODÈLE (Early Stopping implicite)
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            # Enregistrer l'état du dictionnaire des poids entraînés
            torch.save(model.state_dict(), str(model_path))
            print(f"   [SAVE] Modèle CamemBERT sauvegardé avec succès (Perte minimale : {best_val_loss:.4f})")

    print("[OK] Entraînement CamemBERT complété !")


def predire(texte, model=None, tokenizer=None):
    """
    Effectue l'inférence (prédiction en temps réel) sur un paragraphe ESG unique.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if tokenizer is None:
        tokenizer = CamembertTokenizer.from_pretrained(ML_MODEL_NAME)
    if model is None:
        model = get_model()
        model_path = MODELS_DIR / "camembert_ml.pth"
        if not model_path.exists():
            raise FileNotFoundError("Poids CamemBERT introuvables. Veuillez d'abord l'entraîner.")
        model.load_state_dict(torch.load(str(model_path), map_location=device, weights_only=True))
        model = model.to(device)

    model.eval()
    encoding = tokenizer(
        texte,
        max_length=ML_MAX_LENGTH,
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
