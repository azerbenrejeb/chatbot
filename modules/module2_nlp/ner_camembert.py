"""
MODULE 4 (CAMEMBERT NER) — Reconnaissance d'Entités Nommées (NER) avec CamemBERT.
Ce script implémente le fine-tuning de CamemBERT pour la classification de tokens
(Token Classification) au format IOB2, afin d'extraire les entités RSE clés.
"""
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import CamembertTokenizer, CamembertForTokenClassification
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import (
    NER_LABELS, NER_MODEL_NAME, NER_BATCH_SIZE, NER_EPOCHS,
    NER_LEARNING_RATE, NER_MAX_LENGTH, NER_DATASET_DIR, MODELS_DIR
)


class NERDataset(Dataset):
    """
    Dataset PyTorch sur-mesure pour encapsuler et tokeniser les phrases NER au format IOB2.
    """

    def __init__(self, sentences, labels, tokenizer, label2id, max_length=512):
        """
        :param sentences: Liste de phrases (chaque phrase est une liste de mots/tokens)
        :param labels: Liste de labels associés (chaque label est une liste d'étiquettes IOB2)
        :param tokenizer: Le tokenizer CamembertTokenizer
        :param label2id: Dictionnaire de mapping label texte -> ID numérique
        """
        self.sentences = sentences
        self.labels = labels
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length

    def __len__(self):
        """Retourne le nombre total de phrases."""
        return len(self.sentences)

    def __getitem__(self, idx):
        """
        Découpe la phrase en sous-mots, aligne les étiquettes avec ces sous-mots
        et formate le tenseur pour CamemBERT Token Classification.
        """
        words = self.sentences[idx]
        word_labels = self.labels[idx]

        # Tokenisation de la liste de mots déjà découpés
        encoding = self.tokenizer(
            words,
            is_split_into_words=True,  # Indique que l'entrée est déjà segmentée en mots
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Les tokenizers de Transformers découpent souvent un mot en plusieurs sous-mots (subtokens).
        # Nous devons aligner l'étiquette unique du mot avec l'ensemble de ses sous-mots.
        # Les tokens spéciaux (ex: <s>, </s>) reçoivent la valeur -100 pour être ignorés lors du calcul de la perte.
        word_ids = encoding.word_ids()
        label_ids = []
        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)  # Ignorer dans CrossEntropyLoss
            else:
                label_ids.append(self.label2id[word_labels[word_id]])

        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label_ids, dtype=torch.long)
        }


def charger_dataset_iob2():
    """
    Charge le dataset NER au format IOB2.
    Format du fichier attendu :
        mot1    LABEL1
        mot2    LABEL2
        (ligne vide = séparateur de phrases)
    """
    dataset_path = NER_DATASET_DIR / "ner_dataset.txt"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset NER non trouvé : {dataset_path}")

    sentences = []
    labels = []
    current_sentence = []
    current_labels = []

    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == '':
                if current_sentence:
                    sentences.append(current_sentence)
                    labels.append(current_labels)
                    current_sentence = []
                    current_labels = []
            else:
                parts = line.split('\t')
                if len(parts) == 2:
                    current_sentence.append(parts[0])
                    current_labels.append(parts[1])

    if current_sentence:
        sentences.append(current_sentence)
        labels.append(current_labels)

    print(f"[OK] {len(sentences)} phrases chargées depuis le dataset NER")
    return sentences, labels


def get_model():
    """
    Instancie le modèle CamemBERT de Token Classification.
    Configure une tête de classification linéaire de taille 6 pour classifier chaque token.
    """
    model = CamembertForTokenClassification.from_pretrained(
        NER_MODEL_NAME,
        num_labels=len(NER_LABELS)
    )
    return model


def train_ner():
    """
    Boucle d'entraînement pour fine-tuner CamemBERT Token Classification.
    """
    print("[STAT] Lancement de l'entraînement NER CamemBERT...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Appareil cible pour le NER : {device}")

    label2id = {label: i for i, label in enumerate(NER_LABELS)}

    sentences, labels = charger_dataset_iob2()
    tokenizer = CamembertTokenizer.from_pretrained(NER_MODEL_NAME)

    # Découpage simple Train (80%) / Validation (20%)
    split = int(0.8 * len(sentences))
    train_sentences, val_sentences = sentences[:split], sentences[split:]
    train_labels, val_labels = labels[:split], labels[split:]

    train_dataset = NERDataset(train_sentences, train_labels, tokenizer, label2id, NER_MAX_LENGTH)
    val_dataset = NERDataset(val_sentences, val_labels, tokenizer, label2id, NER_MAX_LENGTH)

    train_loader = DataLoader(train_dataset, batch_size=NER_BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=NER_BATCH_SIZE, shuffle=False)

    model = get_model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=NER_LEARNING_RATE)
    
    model_path = MODELS_DIR / "camembert_ner.pth"
    best_val_loss = float('inf')

    for epoch in range(NER_EPOCHS):
        # 1. PHASE D'ENTRAÎNEMENT
        model.train()
        total_loss = 0
        for batch in train_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            batch_labels = batch['labels'].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=batch_labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # 2. PHASE DE VALIDATION
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                batch_labels = batch['labels'].to(device)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=batch_labels)
                val_loss += outputs.loss.item()

        avg_val_loss = val_loss / max(len(val_loader), 1)
        print(f"Epoch [{epoch+1}/{NER_EPOCHS}] - Train Loss: {total_loss/len(train_loader):.4f} | Val Loss: {avg_val_loss:.4f}")

        # Sauvegarde conditionnelle du meilleur modèle
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), str(model_path))
            print(f"   [SAVE] Modèle CamemBERT NER sauvegardé (Perte de val : {avg_val_loss:.4f})")

    print("[OK] Entraînement NER CamemBERT terminé !")


if __name__ == "__main__":
    train_ner()
