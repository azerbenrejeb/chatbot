"""
MODULE 4 (SPACY NER) — Reconnaissance d'Entités Nommées (NER) avec spaCy.
Entraîne un modèle spaCy customisé léger et extrêmement rapide pour extraire
les chiffres clés, unités, années, tendances et références GRI.
"""
import spacy
from spacy.training import Example
from spacy.util import minibatch
import random
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import NER_DATASET_DIR, MODELS_DIR


def charger_dataset_iob2():
    """
    Charge le fichier ner_dataset.txt et le convertit au format d'entraînement spaCy :
    [ ( "texte complet", { "entities": [ (start_char, end_char, "LABEL"), ... ] } ), ... ]
    """
    dataset_path = NER_DATASET_DIR / "ner_dataset.txt"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset NER non trouvé : {dataset_path}")

    print(f"[STAT] Chargement et conversion du dataset NER : {dataset_path}")
    
    sentences = []
    current_words = []
    current_labels = []

    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line == '':
                if current_words:
                    sentences.append((current_words, current_labels))
                    current_words = []
                    current_labels = []
            else:
                parts = line.split('\t')
                if len(parts) == 2:
                    current_words.append(parts[0])
                    current_labels.append(parts[1])

    if current_words:
        sentences.append((current_words, current_labels))

    # Conversion en format spaCy (offsets de caractères)
    training_data = []
    for words, labels in sentences:
        text = ""
        entities = []
        char_idx = 0
        
        for word, label in zip(words, labels):
            start = char_idx
            end = start + len(word)
            text += word + " "
            char_idx = end + 1 # +1 pour l'espace
            
            if label != "O":
                # Supprimer le préfixe B- pour le format interne de spaCy
                clean_label = label.replace("B-", "")
                entities.append((start, end, clean_label))
                
        # Éliminer les éventuels chevauchements et nettoyer
        training_data.append((text.strip(), {"entities": entities}))

    print(f"[OK] {len(training_data)} phrases converties pour spaCy NER.")
    return training_data


def train_spacy_ner(epochs=5, limit_sentences=1500):
    """
    Entraîne un pipeline spaCy NER vide pour le français.
    """
    print("[STAT] Lancement de l'entraînement spaCy NER...")

    # Charger le dataset et mélanger
    all_data = charger_dataset_iob2()
    random.seed(42)
    random.shuffle(all_data)

    # Limiter la taille pour un entraînement CPU ultra-rapide et performant
    train_data = all_data[:limit_sentences]
    print(f"[STAT] Entraînement sur {len(train_data)} phrases sélectionnées...")

    # 1. Créer un modèle vierge en français
    nlp = spacy.blank("fr")

    # 2. Ajouter le composant NER s'il n'existe pas
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # 3. Ajouter les 5 étiquettes RSE à notre composant NER
    labels_to_add = ["VALEUR", "UNITE", "ANNEE", "TENDANCE", "REFERENCE_GRI"]
    for label in labels_to_add:
        ner.add_label(label)

    # 4. Initialisation de l'entraînement
    optimizer = nlp.begin_training()

    # 5. Boucle d'entraînement
    for epoch in range(epochs):
        random.shuffle(train_data)
        losses = {}
        
        # Découpage des données en petits lots (minibatches)
        batches = minibatch(train_data, size=8)
        for batch in batches:
            examples = []
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                # Création de l'objet d'apprentissage spaCy Example
                try:
                    example = Example.from_dict(doc, annotations)
                    examples.append(example)
                except Exception:
                    continue
            
            # Mise à jour des poids du modèle
            nlp.update(examples, sgd=optimizer, losses=losses)
            
        print(f"Epoch [{epoch+1}/{epochs}] - Loss NER: {losses.get('ner', 0.0):.4f}")

    # 6. Sauvegarde du modèle entraîné
    output_dir = MODELS_DIR / "spacy_ner"
    output_dir.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_dir)
    print(f"[OK] Modèle spaCy NER sauvegardé dans : {output_dir}")
    return nlp


def extraire_entites(texte, nlp=None):
    """
    Extrait les entités ESG d'un texte avec le modèle spaCy NER entraîné.
    """
    if nlp is None:
        model_path = MODELS_DIR / "spacy_ner"
        if not model_path.exists():
            raise FileNotFoundError("Modèle spaCy NER introuvable. Veuillez d'abord l'entraîner.")
        nlp = spacy.load(model_path)

    doc = nlp(texte)
    entites = []
    for ent in doc.ents:
        entites.append({
            "texte": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })
    return entites


if __name__ == "__main__":
    train_spacy_ner()
