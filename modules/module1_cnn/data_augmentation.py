"""
MODULE 1 — Techniques d'augmentation de données pour l'entraînement du CNN.

Pourquoi l'augmentation de données ?
- Un modèle de Deep Learning a besoin de beaucoup de données variées pour bien généraliser.
- Dans notre cas, le nombre d'images de pages ESG / NON_ESG est limité (~2200 images).
- L'augmentation crée artificiellement de la diversité en appliquant des transformations
  aléatoires aux images d'entraînement (flips, rotations, variations de couleur).
- Cela force le modèle à apprendre des caractéristiques visuelles robustes plutôt que
  de mémoriser les images exactes (prévention du surapprentissage / overfitting).

Note : Les transformations ne sont appliquées qu'à l'entraînement.
Pour la validation et le test, on applique uniquement le redimensionnement et la normalisation.
"""
import torchvision.transforms as transforms
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import CNN_IMAGE_SIZE


# Moyennes et écarts-types de normalisation ImageNet.
# ResNet-50 a été pré-entraîné sur ImageNet avec ces valeurs.
# On doit utiliser les mêmes pour que les poids pré-entraînés fonctionnent correctement.
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms():
    """
    Retourne les transformations d'augmentation pour l'entraînement.
    Chaque transformation a un rôle précis :

    1. Resize(CNN_IMAGE_SIZE) : Redimensionne l'image à 224x224 pixels (taille d'entrée de ResNet-50).
    2. RandomHorizontalFlip(p=0.5) : Retourne l'image horizontalement avec 50% de probabilité.
       → Ajoute de la variabilité sans modifier le contenu sémantique de la page.
    3. RandomRotation(degrees=3) : Rotation aléatoire de ±3 degrés.
       → Simule les légères inclinaisons des scans PDF réels.
    4. ColorJitter : Variations aléatoires de luminosité, contraste, saturation et teinte.
       → Rend le modèle insensible aux différences de qualité de scan/impression.
    5. ToTensor() : Convertit l'image PIL en tenseur PyTorch (dimensions CHW, valeurs [0, 1]).
    6. Normalize(ImageNet) : Centre les pixels autour de 0 avec les statistiques d'ImageNet.
    """
    return transforms.Compose([
        transforms.Resize((CNN_IMAGE_SIZE, CNN_IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=3),
        transforms.ColorJitter(
            brightness=0.15,
            contrast=0.15,
            saturation=0.1,
            hue=0.05
        ),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])


def get_val_transforms():
    """
    Retourne les transformations pour la validation et le test.
    Aucune augmentation aléatoire n'est appliquée, uniquement le redimensionnement
    et la normalisation pour garantir une évaluation déterministe et reproductible.
    """
    return transforms.Compose([
        transforms.Resize((CNN_IMAGE_SIZE, CNN_IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])


if __name__ == "__main__":
    # Test des transformations
    from PIL import Image
    import torch

    # Créer une image de test
    img_test = Image.new("RGB", (300, 400), color=(128, 128, 128))

    train_tf = get_train_transforms()
    val_tf = get_val_transforms()

    tensor_train = train_tf(img_test)
    tensor_val = val_tf(img_test)

    print(f"[OK] Transformations d'entraînement : {tensor_train.shape} (C x H x W)")
    print(f"[OK] Transformations de validation   : {tensor_val.shape} (C x H x W)")
    print(f"[OK] Plage de valeurs (train) : [{tensor_train.min():.3f}, {tensor_train.max():.3f}]")
