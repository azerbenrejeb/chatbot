"""
Module de préparation du dataset et des Dataloaders PyTorch pour le modèle CNN.

Ce module charge les images générées à partir des pages de rapports PDF,
les répartit en ensembles d'entraînement, de validation et de test de manière stratifiée,
et applique des transformations d'images (data augmentation et normalisation).
"""
from pathlib import Path
import sys

from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# Ajouter le chemin racine du projet pour importer la configuration globale
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import CNN_DATASET_DIR, CNN_CLASSES, CNN_IMAGE_SIZE, CNN_BATCH_SIZE


class ESGImageDataset(Dataset):
    """
    Dataset personnalisé PyTorch pour le chargement d'images de pages ESG / NON_ESG.
    
    Hérite de torch.utils.data.Dataset et implémente les méthodes requises :
    - __len__ : pour obtenir la taille totale du jeu de données.
    - __getitem__ : pour charger et transformer une image à un index spécifique de manière paresseuse (lazy loading).
    """

    def __init__(self, image_paths, labels, transform=None):
        """
        Initialise le Dataset avec les chemins d'images et leurs étiquettes associées.
        
        Args:
            image_paths (list): Liste de chaînes de caractères contenant les chemins absolus des images.
            labels (list): Liste d'entiers représentant la classe de l'image (0 pour ESG, 1 pour NON_ESG).
            transform (torchvision.transforms): Séquence de transformations à appliquer à l'image.
        """
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        """Retourne le nombre total d'images dans le dataset."""
        return len(self.image_paths)

    def __getitem__(self, idx):
        """
        Charge l'image à l'index indiqué, la convertit et applique les transformations.
        
        Args:
            idx (int): Index de l'élément à charger.
            
        Returns:
            tuple: (image_transformée, classe_associée)
        """
        img_path = self.image_paths[idx]

        # Chargement de l'image via Pillow et conversion forcée en RGB.
        # Cela élimine les problèmes liés aux images en niveaux de gris (1 canal) ou avec canal alpha (RGBA, 4 canaux).
        image = Image.open(img_path).convert("RGB")
        label = self.labels[idx]

        # Application des transformations PyTorch (redimensionnement, tenseur, normalisation, etc.)
        if self.transform:
            image = self.transform(image)

        return image, label


def _can_stratify(labels):
    """
    Vérifie si la stratification est possible pour le découpage train_test_split.
    
    La stratification (qui conserve les proportions de chaque classe dans chaque sous-ensemble)
    nécessite au moins 2 exemples par classe unique présente dans la liste des labels.
    
    Args:
        labels (list): Liste des étiquettes de classe.
        
    Returns:
        bool: True si la stratification est mathématiquement réalisable, False sinon.
    """
    return all(labels.count(label_idx) >= 2 for label_idx in set(labels))


def _split_dataset(image_paths, labels):
    """
    Sépare le dataset global en trois ensembles distincts : Entraînement (70%), Validation (15%) et Test (15%).
    
    Utilise la stratification pour garantir que les proportions de pages ESG et NON_ESG 
    soient identiques dans chaque ensemble, évitant ainsi les biais de mesure.
    
    Args:
        image_paths (list): Liste des chemins de toutes les images.
        labels (list): Liste des classes correspondantes.
        
    Returns:
        tuple: Chemins et classes pour (train, val, test).
    """
    # Détermination de l'option de stratification
    stratify = labels if _can_stratify(labels) else None
    
    # Premier découpage : 70% Train, 30% temporaire (pour la Validation + Test)
    train_paths, temp_paths, train_labels, temp_labels = train_test_split(
        image_paths,
        labels,
        test_size=0.3,
        random_state=42,
        stratify=stratify,
    )

    # Deuxième découpage : sépare les 30% temporaires à parts égales (50/50)
    # Ce qui donne 15% de Validation et 15% de Test par rapport au total de départ.
    temp_stratify = temp_labels if _can_stratify(temp_labels) else None
    val_paths, test_paths, val_labels, test_labels = train_test_split(
        temp_paths,
        temp_labels,
        test_size=0.5,
        random_state=42,
        stratify=temp_stratify,
    )

    return train_paths, val_paths, test_paths, train_labels, val_labels, test_labels


def get_dataloaders():
    """
    Scanne les dossiers de données, prépare les jeux de données et génère les Dataloaders PyTorch.
    
    Les transformations appliquées comprennent :
    - Pour l'entraînement : Redimensionnement + Augmentation (Flip horizontal aléatoire,
      variations de luminosité et contraste) pour améliorer la robustesse du modèle + Normalisation.
    - Pour la validation/test : Uniquement le redimensionnement et la normalisation (aucune augmentation).
    
    Note sur la Normalisation :
    Les valeurs de moyenne (mean=[0.485, 0.456, 0.406]) et d'écart-type (std=[0.229, 0.224, 0.225])
    sont les standards issus du jeu de données ImageNet. Elles sont requises si on utilise 
    le transfert d'apprentissage avec ResNet-50.
    
    Returns:
        tuple: (train_loader, val_loader, test_loader)
    """
    all_images = []
    all_labels = []

    # Parcours des classes d'images configurées (ESG et NON_ESG)
    for label_idx, cls_name in enumerate(CNN_CLASSES):
        cls_dir = CNN_DATASET_DIR / cls_name
        if not cls_dir.exists():
            continue

        # Lecture des fichiers d'images supportés (.jpg, .jpeg, .png)
        for img_path in sorted(cls_dir.glob("*.*")):
            if img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
                all_images.append(str(img_path))
                all_labels.append(label_idx)

    # Sécurité si aucun jeu de données n'est annoté ou extrait
    if not all_images:
        raise ValueError("Aucune image trouvée dans le dataset CNN. Veuillez d'abord exécuter l'extraction des PDF en images.")

    # Affichage des statistiques de répartition
    class_counts = {
        cls_name: sum(1 for label in all_labels if label == label_idx)
        for label_idx, cls_name in enumerate(CNN_CLASSES)
    }
    print(f"[INFO] Images CNN trouvées pour l'entraînement : {class_counts}")

    # Séparation en train / val / test
    train_paths, val_paths, test_paths, train_labels, val_labels, test_labels = _split_dataset(
        all_images,
        all_labels,
    )

    # 1. Pipeline de transformations pour l'entraînement avec augmentation de données (Data Augmentation)
    train_transform = transforms.Compose([
        # Redimensionne l'image à la taille d'entrée du CNN (ex: 224x224)
        transforms.Resize((CNN_IMAGE_SIZE, CNN_IMAGE_SIZE)),
        # Retourne horizontalement l'image aléatoirement avec une probabilité de 50%
        transforms.RandomHorizontalFlip(),
        # Ajoute du bruit colorimétrique léger (luminosité et contraste modifiés de +/- 20%)
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        # Convertit l'image PIL (valeurs [0, 255]) en Tenseur PyTorch (valeurs [0.0, 1.0])
        transforms.ToTensor(),
        # Normalise les canaux RGB du tenseur avec la moyenne et l'écart-type d'ImageNet
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # 2. Pipeline de transformations de validation et de test (sans bruit ni augmentation)
    val_test_transform = transforms.Compose([
        transforms.Resize((CNN_IMAGE_SIZE, CNN_IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Instanciation des objets Dataset
    train_dataset = ESGImageDataset(train_paths, train_labels, transform=train_transform)
    val_dataset = ESGImageDataset(val_paths, val_labels, transform=val_test_transform)
    test_dataset = ESGImageDataset(test_paths, test_labels, transform=val_test_transform)

    # Instanciation des Dataloaders PyTorch
    # Le DataLoader gère automatiquement le regroupement en lots (batching), le mélange aléatoire (shuffle)
    # et le chargement en parallèle via des sous-processus si nécessaire.
    train_loader = DataLoader(train_dataset, batch_size=CNN_BATCH_SIZE, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_dataset, batch_size=CNN_BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=CNN_BATCH_SIZE, shuffle=False)

    print(
        "[OK] Dataloaders CNN créés avec succès : "
        f"Entraînement={len(train_dataset)}, Validation={len(val_dataset)}, Test={len(test_dataset)}"
    )

    return train_loader, val_loader, test_loader


if __name__ == "__main__":
    get_dataloaders()
