"""
MODULE 4 — Gestionnaire de sessions pour le chatbot ESG Streamlit.
Encapsule la gestion de l'état de session Streamlit (st.session_state)
pour le suivi de la conversation, du rapport chargé et des préférences utilisateur.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


def initialiser_session(st):
    """
    Initialise les variables de session Streamlit si elles n'existent pas encore.
    Appelée au démarrage de l'application chatbot.

    :param st: Module Streamlit importé (passé en paramètre pour éviter l'import circulaire).
    """
    # Historique des messages de la conversation active
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Nom du rapport PDF actuellement chargé
    if "rapport_actif" not in st.session_state:
        st.session_state.rapport_actif = None

    # Identifiant de la session de base de données
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    # Compteur de messages échangés
    if "compteur_messages" not in st.session_state:
        st.session_state.compteur_messages = 0

    # Filtre ESG actif (Environnemental, Social, Gouvernance ou None)
    if "filtre_esg" not in st.session_state:
        st.session_state.filtre_esg = None

    # Indicateur de traitement en cours
    if "traitement_en_cours" not in st.session_state:
        st.session_state.traitement_en_cours = False


def ajouter_message_session(st, role, content, sources=None):
    """
    Ajoute un message à l'historique de la session Streamlit.

    :param st: Module Streamlit.
    :param role: 'user' ou 'assistant'.
    :param content: Contenu textuel du message.
    :param sources: Liste de sources optionnelles (pour les réponses assistant).
    """
    message = {"role": role, "content": content}
    if sources:
        message["sources"] = sources
    st.session_state.messages.append(message)
    st.session_state.compteur_messages += 1


def reset_conversation(st):
    """
    Réinitialise la conversation active en vidant l'historique des messages.
    Le rapport chargé reste en mémoire.

    :param st: Module Streamlit.
    """
    st.session_state.messages = []
    st.session_state.compteur_messages = 0
    st.session_state.session_id = None


def set_rapport_actif(st, rapport_name):
    """
    Définit le rapport actuellement actif dans la session.

    :param st: Module Streamlit.
    :param rapport_name: Nom du fichier PDF.
    """
    st.session_state.rapport_actif = rapport_name


def get_resume_session(st):
    """
    Retourne un résumé de l'état de la session active.

    :param st: Module Streamlit.
    :return: Dictionnaire résumé.
    """
    return {
        "rapport_actif": st.session_state.get("rapport_actif", None),
        "nb_messages": st.session_state.get("compteur_messages", 0),
        "filtre_esg": st.session_state.get("filtre_esg", None),
        "traitement_en_cours": st.session_state.get("traitement_en_cours", False),
    }
