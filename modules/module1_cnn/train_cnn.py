"""
Script d'entraînement du modèle de classification de pages CNN (ESG vs NON_ESG).

Ce script configure l'environnement PyTorch, calcule des poids de pondération pour
corriger les déséquilibres entre classes, exécute la boucle d'entraînement et de validation,
et sauvegarde les poids du meilleur modèle trouvé (le plus bas score de validation).
"""
from pathlib import Path
import sys

import torch
import torch.nn as nn
import torch.optim as optim

# Intégration du dossier parent pour importer les configurations globales
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import MODELS_DIR, CNN_EPOCHS, CNN_LEARNING_RATE, CNN_CLASSES, CNN_DATASET_DIR
from modules.module1_cnn.cnn_classifier import get_model
from modules.module1_cnn.dataset_builder import get_dataloaders


def _count_images(class_name):
    """
    Compte le nombre total d'images présentes dans le dossier d'une classe spécifique.
    
    Args:
        class_name (str): Le nom de la classe (ex: 'ESG' ou 'NON_ESG').
        
    Returns:
        int: Nombre de fichiers images trouvés.
    """
    class_dir = CNN_DATASET_DIR / class_name
    if not class_dir.exists():
        return 0
    return sum(1 for path in class_dir.glob("*.*") if path.suffix.lower() in [".jpg", ".jpeg", ".png"])


def _build_class_weights(device):
    """
    Calcule des coefficients de pondération inversement proportionnels à la fréquence des classes.

    Pourquoi ?
    Si une classe (ex: NON_ESG) possède beaucoup moins d'images que l'autre, le réseau
    peut tricher en prédisant systématiquement la classe majoritaire pour obtenir un bon score.
    En donnant plus de poids à la classe rare lors du calcul de l'erreur (Loss), chaque erreur
    sur cette classe coûtera plus cher, forçant le modèle à y prêter une attention accrue.

    Calcul :
        poids_classe = total_exemples / (nombre_de_classes * exemples_dans_la_classe)
        
    Args:
        device (torch.device): CPU ou GPU de traitement.
        
    Returns:
        torch.FloatTensor: Vecteur contenant les poids de chaque classe.
    """
    counts = [max(_count_images(class_name), 1) for class_name in CNN_CLASSES]
    total = sum(counts)
    # Formule standard pour rééquilibrer les classes
    weights = [total / (len(CNN_CLASSES) * count) for count in counts]

    print("[INFO] Répartition actuelle dans le dataset CNN : " + ", ".join(
        f"{class_name}={count}" for class_name, count in zip(CNN_CLASSES, counts)
    ))
    print("[INFO] Coefficients de correction de classe (weights) : " + ", ".join(
        f"{class_name}={weight:.2f}" for class_name, weight in zip(CNN_CLASSES, weights)
    ))

    return torch.FloatTensor(weights).to(device)


def _evaluate(model, loader, criterion, device):
    """
    Évalue les performances du modèle (Calcul de la perte et de la précision).
    
    Désactive le calcul des gradients (via torch.no_grad()) et passe le modèle en
    mode 'eval' pour désactiver des comportements spécifiques comme le Dropout ou la Batch Normalization.
    
    Args:
        model (nn.Module): Modèle à évaluer.
        loader (DataLoader): Dataloader (Validation ou Test).
        criterion (nn.Module): Fonction de calcul d'erreur (Loss).
        device (torch.device): Matériel exécutant les calculs (CPU/CUDA).
        
    Returns:
        tuple: (perte_moyenne, precision_pourcentage)
    """
    model.eval()  # Désactive le Dropout et fige les paramètres de BatchNorm
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():  # Économise de la mémoire en désactivant le suivi des gradients
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * inputs.size(0)
            predicted = torch.argmax(outputs, dim=1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    if total == 0:
        return 0.0, 0.0
    return total_loss / total, 100 * correct / total


def train_model():
    """
    Fonction principale orchestrant l'entraînement complet du CNN.
    """
    print("[STAT] Lancement du pipeline d'entraînement du modèle CNN...")

    # Création du dossier d'enregistrement des modèles si manquant
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Détection automatique de la présence d'une puce GPU Nvidia (CUDA) pour accélérer le calcul
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Périphérique de calcul détecté : {device}")

    try:
        train_loader, val_loader, test_loader = get_dataloaders()
    except Exception as e:
        print(f"[ERR] Échec de la préparation des Dataloaders : {e}")
        return

    # Instanciation du modèle (use_light=True pour compatibilité et exécution rapide locale sur CPU)
    model = get_model(num_classes=len(CNN_CLASSES), use_light=True).to(device)

    # Définition de la fonction de coût CrossEntropy avec les poids calculés pour corriger le déséquilibre
    criterion = nn.CrossEntropyLoss(weight=_build_class_weights(device))
    
    # Choix de l'optimiseur Adam (recommandé pour sa vitesse de convergence et ajustement dynamique du pas de gradient)
    optimizer = optim.Adam(model.parameters(), lr=CNN_LEARNING_RATE)

    best_val_loss = float("inf")
    model_path = MODELS_DIR / "cnn_resnet50_esg.pth"

    # --- Boucle d'entraînement principale ---
    for epoch in range(CNN_EPOCHS):
        model.train()  # Active explicitement le Dropout et la BatchNorm pour l'apprentissage
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            # --- CYCLE STANDARD DE RETROPROPAGATION ---
            # 1. Remise à zéro des gradients accumulés au pas précédent (indispensable sous PyTorch)
            optimizer.zero_grad()
            
            # 2. Propagation avant : calcul des prédictions (logits)
            outputs = model(inputs)
            
            # 3. Calcul de la perte entre la prédiction et l'étiquette réelle
            loss = criterion(outputs, labels)
            
            # 4. Rétropropagation : calcul automatique des dérivées partielles de la perte par rapport aux poids
            loss.backward()
            
            # 5. Mise à jour des poids du modèle selon la direction du gradient et le taux d'apprentissage
            optimizer.step()

            # Métriques temporaires
            running_loss += loss.item() * inputs.size(0)
            predicted = torch.argmax(outputs, dim=1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        # Calcul des scores moyens de l'époque
        train_loss = running_loss / max(total, 1)
        train_acc = 100 * correct / max(total, 1)
        
        # Évaluation sur l'ensemble de Validation
        val_loss, val_acc = _evaluate(model, val_loader, criterion, device)

        print(
            f"Époque [{epoch + 1}/{CNN_EPOCHS}] - "
            f"Perte Train: {train_loss:.4f}, Précision Train: {train_acc:.2f}% | "
            f"Perte Val: {val_loss:.4f}, Précision Val: {val_acc:.2f}%"
        )

        # Sauvegarde du modèle uniquement si la perte de Validation diminue.
        # Cela empêche le surapprentissage (Overfitting) : si la perte en train continue de baisser
        # mais que la perte en validation remonte, le modèle commence à mémoriser au lieu de généraliser.
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), str(model_path))
            print("   [SAVE] Nouvelle meilleure perte de validation. Poids enregistrés.")

    # --- Évaluation finale sur l'ensemble de Test indépendant ---
    if model_path.exists():
        model.load_state_dict(torch.load(str(model_path), map_location=device, weights_only=True))
    test_loss, test_acc = _evaluate(model, test_loader, criterion, device)
    print(f"[OK] Entraînement terminé. Performance de Test finale -> Perte : {test_loss:.4f}, Précision : {test_acc:.2f}%")


if __name__ == "__main__":
    train_model()
