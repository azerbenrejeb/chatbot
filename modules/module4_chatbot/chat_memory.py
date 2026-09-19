"""
MODULE 4 — Gestionnaire de mémoire de conversation du chatbot ESG.
Fournit une couche d'abstraction au-dessus de la base SQLite pour gérer
l'historique de conversation en cours et le contexte conversationnel.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.database import ChatDatabase


class ChatMemory:
    """
    Mémoire conversationnelle du chatbot.
    Conserve les N derniers échanges pour fournir du contexte au LLM
    sans dépasser la fenêtre de contexte de Mistral 7B.
    """

    def __init__(self, max_historique=10):
        """
        :param max_historique: Nombre maximal de messages à conserver en mémoire de travail.
        """
        self.db = ChatDatabase()
        self.max_historique = max_historique
        self.session_id = None

    def nouvelle_session(self, rapport_name="", titre="Nouvelle conversation"):
        """Crée une nouvelle session de conversation et la mémorise."""
        self.session_id = self.db.creer_session(rapport_name=rapport_name, titre=titre)
        return self.session_id

    def charger_session(self, session_id):
        """Charge une session existante."""
        self.session_id = session_id

    def mettre_a_jour_rapport(self, rapport_name):
        """Met à jour le rapport de la session courante en base de données."""
        if self.session_id is not None:
            self.db.mettre_a_jour_rapport_session(self.session_id, rapport_name)

    def ajouter_message(self, role, content):
        """
        Ajoute un message à la session courante.
        :param role: 'user' ou 'assistant'
        :param content: Contenu du message
        """
        if self.session_id is None:
            self.nouvelle_session()
        self.db.ajouter_message(self.session_id, role, content)

    def get_contexte_conversation(self):
        """
        Retourne les N derniers messages pour fournir du contexte au LLM.
        Formaté sous forme de chaîne lisible pour le prompt Mistral.
        """
        if self.session_id is None:
            return ""

        historique = self.db.get_historique(self.session_id)

        # Conserver uniquement les N derniers messages
        messages_recents = historique[-self.max_historique:]

        # Formater pour le prompt LLM
        lignes = []
        for msg in messages_recents:
            role_label = "Utilisateur" if msg['role'] == 'user' else "Assistant"
            lignes.append(f"{role_label}: {msg['content']}")

        return "\n".join(lignes)

    def get_historique_complet(self):
        """Retourne l'historique complet de la session courante."""
        if self.session_id is None:
            return []
        return self.db.get_historique(self.session_id)

    def get_toutes_sessions(self):
        """Retourne la liste de toutes les sessions de conversation."""
        return self.db.get_sessions()

    def supprimer_session(self, session_id):
        """Supprime une session et ses messages."""
        self.db.supprimer_session(session_id)
        if self.session_id == session_id:
            self.session_id = None


if __name__ == "__main__":
    mem = ChatMemory()
    sid = mem.nouvelle_session(rapport_name="Test.pdf")
    mem.ajouter_message("user", "Quelles sont les émissions CO2 ?")
    mem.ajouter_message("assistant", "Les émissions s'élèvent à 45 200 tCO2e.")
    print(f"[OK] Contexte :\n{mem.get_contexte_conversation()}")
