"""
Script d'évaluation fine du modèle CNN entraîné sur le jeu de test.

Ce script charge les poids sauvegardés du modèle, effectue des prédictions
sur l'ensemble de test (jamais vu lors de l'entraînement) et calcule :
1. La précision globale du modèle.
2. La précision détaillée pour chaque classe (ESG vs NON_ESG).
"""
import torch
from pathlib import Path
import sys

# Ajouter le chemin racine du projet pour importer la configuration globale
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import MODELS_DIR, CNN_CLASSES
from modules.module1_cnn.cnn_classifier import get_model
from modules.module1_cnn.dataset_builder import get_dataloaders


def evaluate_model():
    """
    Charge le modèle entraîné et calcule les statistiques de performance de test.
    """
    print("[STAT] Lancement de l'évaluation globale du modèle CNN...")
    
    # Choix matériel automatique
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = MODELS_DIR / "cnn_resnet50_esg.pth"
    
    # Vérification de l'existence des poids du modèle avant évaluation
    if not model_path.exists():
        print("[ERR] Aucun modèle entraîné trouvé ! Veuillez d'abord lancer 'train_cnn.py'.")
        return
        
    try:
        # Récupération uniquement du test_loader (les deux autres ne sont pas nécessaires ici)
        _, _, test_loader = get_dataloaders()
    except Exception as e:
        print(f"[ERR] Erreur lors de l'initialisation du dataloader : {e}")
        return
        
    # Instanciation du modèle et chargement des poids sauvegardés
    model = get_model(num_classes=len(CNN_CLASSES))
    model.load_state_dict(torch.load(str(model_path), map_location=device, weights_only=True))
    model = model.to(device)
    model.eval()  # Mode d'évaluation (désactivation du dropout et stabilisation de la batchnorm)
    
    correct = 0
    total = 0
    # Listes pour suivre les statistiques par classe individuelle
    class_correct = list(0. for i in range(len(CNN_CLASSES)))
    class_total = list(0. for i in range(len(CNN_CLASSES)))
    
    with torch.no_grad():  # Pas besoin de suivre les gradients pendant l'évaluation
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            # Propagation avant (forward pass) pour obtenir les prédictions
            outputs = model(inputs)
            # Récupère l'index de la classe ayant obtenu le score le plus élevé (logit maximum)
            _, predicted = torch.max(outputs, 1)
            
            # Mise à jour des compteurs généraux
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            # Calcul des compteurs individuels par classe pour repérer d'éventuels biais
            c = (predicted == labels).squeeze()
            for i in range(len(labels)):
                label = labels[i].item()
                # Sécurité si le batch est composé d'une seule image (c est alors scalaire)
                if c.dim() == 0:
                    class_correct[label] += c.item()
                else:
                    class_correct[label] += c[i].item()
                class_total[label] += 1
                
    # Calcul et affichage des métriques globales
    acc = 100 * correct / total
    print(f"\n==========================================")
    print(f"PRÉCISION GLOBALE SUR LE JEU DE TEST : {acc:.2f} %")
    print(f"==========================================\n")
    
    # Affichage détaillé de la précision par classe
    for i in range(len(CNN_CLASSES)):
        if class_total[i] > 0:
            print(f"Précision pour la classe {CNN_CLASSES[i]}: {100 * class_correct[i] / class_total[i]:.2f} % (Basé sur {int(class_total[i])} images)")
        else:
            print(f"Précision pour la classe {CNN_CLASSES[i]}: Non testable (aucune image de cette classe dans le test set)")


if __name__ == "__main__":
    evaluate_model()
