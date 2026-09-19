"""
Modèle CNN pour classer les pages de documents en deux classes : ESG (pertinente) et NON_ESG (non pertinente / bruit).

Ce module propose deux architectures au choix :
1. ESG_CNN_Light : Un réseau de neurones convolutif léger, conçu sur-mesure pour être rapide et optimisé pour l'entraînement sur CPU.
2. ESG_CNN : Un modèle basé sur ResNet-50 utilisant le Transfer Learning (apprentissage par transfert) pré-entraîné sur ImageNet, plus lourd mais offrant de meilleures performances de généralisation.
"""
import torch.nn as nn
from torchvision import models


class ESG_CNN_Light(nn.Module):
    """
    Réseau de Neurones Convolutif (CNN) Léger personnalisé pour CPU.

    Cette architecture extrait les caractéristiques visuelles de la page (mise en page, 
    présence de tableaux, graphiques, logos ou blocs textuels denses) grâce à des couches de convolution.
    
    Architecture détaillée :
    - Bloc 1 : Conv2d (3 -> 16 filtres) + BatchNorm + ReLU + MaxPool
    - Bloc 2 : Conv2d (16 -> 32 filtres) + BatchNorm + ReLU + MaxPool
    - Bloc 3 : Conv2d (32 -> 64 filtres) + BatchNorm + ReLU + MaxPool
    - Tête de classification : AdaptiveAvgPool2d + Flatten + Dropout(30%) + Linéaire (64 -> 2 classes)
    """

    def __init__(self, num_classes=2):
        """
        Initialise les couches du réseau léger.
        
        Args:
            num_classes (int): Nombre de classes de sortie (par défaut 2 : ESG et NON_ESG).
        """
        super(ESG_CNN_Light, self).__init__()
        
        # Le feature extractor (extracteur de caractéristiques visuelles)
        self.features = nn.Sequential(
            # --- BLOC 1 : Détection des formes simples et contours (lignes, blocs textuels de base) ---
            # Entrée : image RGB de taille (Batch, 3, 224, 224)
            # Conv2d : applique 16 filtres de taille 3x3. Le padding=1 conserve la dimension spatiale (224x224).
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            # BatchNorm2d : normalise les activations pour accélérer la convergence et stabiliser l'apprentissage.
            nn.BatchNorm2d(16),
            # ReLU : fonction d'activation non-linéaire f(x) = max(0, x). Permet d'apprendre des relations complexes.
            nn.ReLU(),
            # MaxPool2d : réduit la dimension spatiale par 2 (de 224x224 à 112x112) en ne gardant que la valeur maximale locale.
            nn.MaxPool2d(2, 2),

            # --- BLOC 2 : Combinaison des contours en motifs plus complexes (titres, marges, images) ---
            # Entrée : (Batch, 16, 112, 112) -> Sortie : (Batch, 32, 112, 112)
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            # MaxPool2d : réduit la taille à 56x56
            nn.MaxPool2d(2, 2),

            # --- BLOC 3 : Abstraction spatiale de haut niveau (structure globale de la page) ---
            # Entrée : (Batch, 32, 56, 56) -> Sortie : (Batch, 64, 56, 56)
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            # MaxPool2d : réduit la taille finale à 28x28
            nn.MaxPool2d(2, 2),
        )
        
        # Le classifier (tête de classification finale)
        self.classifier = nn.Sequential(
            # AdaptiveAvgPool2d : Calcule la valeur moyenne globale de chaque carte de caractéristiques (feature map).
            # Réduit la taille géométrique de n'importe quelle entrée (ex: 28x28) à exactement (1, 1).
            # Sortie : (Batch, 64, 1, 1)
            nn.AdaptiveAvgPool2d((1, 1)),
            # Flatten : Aplantit les dimensions pour obtenir un vecteur 1D adapté aux couches linéaires.
            # Sortie : (Batch, 64)
            nn.Flatten(),
            # Dropout : Désactive aléatoirement 30% des neurones pendant l'entraînement.
            # Cela force le réseau à ne pas trop se reposer sur des détails spécifiques (anti-overfitting).
            nn.Dropout(0.3),
            # Linear : Couche de décision finale qui projette les 64 caractéristiques vers les scores des 2 classes.
            # Sortie : (Batch, num_classes) (logits non normalisés)
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        """
        Définit le passage des données à travers le réseau (propagation avant).
        
        Args:
            x (torch.Tensor): Tensor d'images de taille (Batch, 3, 224, 224).
            
        Returns:
            torch.Tensor: Logits des prédictions pour chaque classe.
        """
        x = self.features(x)
        x = self.classifier(x)
        return x


class ESG_CNN(nn.Module):
    """
    Réseau de Neurones lourd basé sur ResNet-50 (Transfer Learning).

    Cette classe charge un modèle ResNet-50 pré-entraîné sur le dataset géant ImageNet.
    Comme le modèle sait déjà détecter les formes, couleurs et structures, nous gelons
    ses paramètres (le "backbone") pour ne pas effacer ces connaissances.
    Nous remplaçons uniquement la couche finale (Fully Connected) pour l'adapter à nos 2 classes.
    """

    def __init__(self, num_classes=2, pretrained=True):
        """
        Initialise le modèle ResNet-50 et modifie la couche de classification.
        
        Args:
            num_classes (int): Nombre de classes cibles (ESG / NON_ESG).
            pretrained (bool): Si True, charge les poids pré-entraînés d'ImageNet.
        """
        super(ESG_CNN, self).__init__()
        
        if pretrained:
            # Récupère les poids recommandés pour ResNet-50
            weights = models.ResNet50_Weights.DEFAULT
            self.model = models.resnet50(weights=weights)
        else:
            self.model = models.resnet50()

        # GEL DES GRADIENTS : On empêche la mise à jour des poids du backbone pré-entraîné
        # Cela réduit drastiquement le temps d'entraînement et évite la dégradation des filtres de base.
        for param in self.model.parameters():
            param.requires_grad = False

        # Extraction du nombre de caractéristiques d'entrée de la couche de décision d'origine
        num_ftrs = self.model.fc.in_features
        
        # Remplacement de la couche fully connected (fc) par notre propre tête de classification binaire
        self.model.fc = nn.Sequential(
            # Dropout de 50% pour minimiser le risque de surapprentissage sur nos quelques rapports
            nn.Dropout(0.5),
            # Couche linéaire finale produisant les logits pour ESG / NON_ESG
            nn.Linear(num_ftrs, num_classes),
        )

        # On s'assure que les paramètres de cette nouvelle couche finale soient bien mis à jour par l'optimiseur
        for param in self.model.fc.parameters():
            param.requires_grad = True

    def forward(self, x):
        """
        Propagation avant à travers le modèle ResNet-50 modifié.
        
        Args:
            x (torch.Tensor): Images d'entrée.
            
        Returns:
            torch.Tensor: Logits des prédictions.
        """
        return self.model(x)


def get_model(num_classes=2, use_light=True):
    """
    Factory function pour instancier le modèle choisi.

    Par défaut, use_light=True instancie le CNN léger personnalisé.
    Ce choix est recommandé pour les environnements CPU locaux car il est rapide à exécuter
    et ne nécessite pas le téléchargement volumineux des poids de ResNet-50 (environ 100 Mo).
    
    Pour un entraînement haute fidélité avec GPU, use_light=False est préférable.
    
    Args:
        num_classes (int): Nombre de classes en sortie (2).
        use_light (bool): Choix de l'architecture légère (True) ou lourde (False).
        
    Returns:
        nn.Module: Le modèle PyTorch instancié.
    """
    if use_light:
        print("[INFO] Utilisation de l'architecture légère optimisée pour CPU (ESG_CNN_Light).")
        return ESG_CNN_Light(num_classes=num_classes)

    print("[INFO] Utilisation de l'architecture ResNet-50 avec Transfer Learning (ESG_CNN).")
    return ESG_CNN(num_classes=num_classes)
