"""
MODULE 5 — Gestionnaire d'Embeddings pour le pipeline RAG.
Encapsule le modèle SentenceTransformer pour convertir du texte en vecteurs numériques
de dimension fixe (embeddings). Ces vecteurs permettent la recherche sémantique dans ChromaDB.

Pourquoi des embeddings ?
- Un moteur de recherche classique cherche des mots exacts (TF-IDF, BM25).
- Un embedding encode le SENS d'une phrase dans un espace vectoriel de haute dimension.
- Deux phrases ayant un sens similaire auront des vecteurs proches (cosinus similaire ~ 1.0).
- Exemple : "émissions de CO2" et "gaz à effet de serre" auront des embeddings très proches
  même s'ils ne partagent aucun mot en commun.
"""
from sentence_transformers import SentenceTransformer
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import EMBEDDING_MODEL_NAME


class EmbeddingManager:
    """
    Gestionnaire paresseux (lazy loading) du modèle d'embedding multilingue.
    Le modèle n'est chargé en mémoire qu'au premier appel, ce qui évite
    de consommer de la RAM inutilement si le module n'est pas utilisé.
    """

    def __init__(self, model_name=None):
        """
        :param model_name: Nom du modèle SentenceTransformer à charger.
                           Par défaut, utilise le modèle défini dans app/config.py.
        """
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        self._model = None  # Chargement différé (lazy)

    @property
    def model(self):
        """Charge le modèle SentenceTransformer à la première utilisation."""
        if self._model is None:
            print(f"[STAT] Chargement du modèle d'embedding : {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            print(f"[OK] Modèle d'embedding chargé (dimension : {self._model.get_sentence_embedding_dimension()})")
        return self._model

    def encoder_texte(self, texte):
        """
        Encode un texte unique en un vecteur numérique (embedding).
        :param texte: Chaîne de caractères à encoder.
        :return: Liste de floats représentant le vecteur d'embedding.
        """
        embedding = self.model.encode(texte, convert_to_numpy=True)
        return embedding.tolist()

    def encoder_batch(self, textes):
        """
        Encode un lot de textes en vecteurs numériques.
        Plus efficace que d'appeler encoder_texte en boucle car le modèle
        traite les textes en parallèle sur le GPU/CPU.
        :param textes: Liste de chaînes de caractères.
        :return: Liste de listes de floats.
        """
        embeddings = self.model.encode(textes, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()

    def get_dimension(self):
        """Retourne la dimension des vecteurs produits par le modèle."""
        return self.model.get_sentence_embedding_dimension()


# Instance globale réutilisable dans tout le projet
embedding_manager = EmbeddingManager()


if __name__ == "__main__":
    # Test rapide du gestionnaire d'embeddings
    em = EmbeddingManager()
    texte_test = "Les émissions de CO2 du groupe s'élèvent à 45 200 tCO2e en 2023."
    vec = em.encoder_texte(texte_test)
    print(f"Texte : {texte_test}")
    print(f"Dimension du vecteur : {len(vec)}")
    print(f"Premiers 5 éléments : {vec[:5]}")
