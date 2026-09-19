"""
Base de données SQLite pour le stockage persistant des sessions de chat et de l'historique
des conversations du chatbot ESG.

Pourquoi SQLite ?
- Base de données relationnelle légère intégrée à Python (module sqlite3 standard).
- Ne nécessite aucun serveur externe, idéal pour une application locale/Docker.
- Permet de conserver l'historique des conversations entre les sessions utilisateur.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR


# Chemin par défaut de la base de données SQLite
DEFAULT_DB_PATH = BASE_DIR / "data" / "chatbot_history.db"


class ChatDatabase:
    """
    Gestionnaire de la base de données de l'historique du chatbot ESG.
    Stocke les sessions de conversation et les messages échangés.
    """

    def __init__(self, db_path=None):
        """
        Initialise la connexion à la base SQLite et crée les tables si nécessaire.
        :param db_path: Chemin du fichier .db (optionnel, utilise le chemin par défaut sinon)
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        self._creer_tables()

    def _creer_tables(self):
        """Crée les tables de la base si elles n'existent pas encore."""
        cursor = self.conn.cursor()

        # Table des sessions de conversation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                rapport_name TEXT DEFAULT '',
                titre TEXT DEFAULT 'Nouvelle conversation'
            )
        """)

        # Table des messages (chaque message appartient à une session)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # Table des résultats de conformité
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conformity_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                dimension TEXT NOT NULL,
                score REAL NOT NULL,
                presents TEXT NOT NULL,
                manquants TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des indicateurs extraits par le NER
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indicateurs_esg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                rapport_name TEXT,
                reference_gri TEXT NOT NULL,
                valeur TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def creer_session(self, rapport_name="", titre="Nouvelle conversation"):
        """
        Crée une nouvelle session de conversation.
        :param rapport_name: Nom du rapport ESG chargé dans cette session.
        :param titre: Titre de la conversation.
        :return: L'identifiant unique (int) de la session créée.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (rapport_name, titre) VALUES (?, ?)",
            (rapport_name, titre)
        )
        self.conn.commit()
        return cursor.lastrowid

    def mettre_a_jour_rapport_session(self, session_id, rapport_name):
        """
        Met à jour le nom du rapport associé à une session.
        :param session_id: Identifiant de la session.
        :param rapport_name: Nouveau nom du rapport.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET rapport_name = ? WHERE id = ?",
            (rapport_name, session_id)
        )
        self.conn.commit()

    def ajouter_message(self, session_id, role, content):
        """
        Ajoute un message à une session existante.
        :param session_id: Identifiant de la session.
        :param role: Rôle de l'émetteur ('user', 'assistant' ou 'system').
        :param content: Contenu textuel du message.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        self.conn.commit()

    def get_historique(self, session_id):
        """
        Récupère l'historique complet des messages d'une session.
        :param session_id: Identifiant de la session.
        :return: Liste de dictionnaires [{'role': str, 'content': str, 'created_at': str}].
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_sessions(self):
        """
        Récupère la liste de toutes les sessions de conversation.
        :return: Liste de dictionnaires [{'id': int, 'created_at': str, 'rapport_name': str, 'titre': str}].
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, created_at, rapport_name, titre FROM sessions ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

    def supprimer_session(self, session_id):
        """Supprime une session et tous ses messages associés."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()

    def fermer(self):
        """Ferme proprement la connexion à la base de données."""
        self.conn.close()


if __name__ == "__main__":
    # Test de la base de données
    db = ChatDatabase()
    sid = db.creer_session(rapport_name="Test_Rapport_ESG.pdf", titre="Test session")
    db.ajouter_message(sid, "user", "Quelles sont les émissions CO2 ?")
    db.ajouter_message(sid, "assistant", "Selon le rapport, les émissions s'élèvent à 45 200 tCO2e.")
    historique = db.get_historique(sid)
    sessions = db.get_sessions()
    print(f"[OK] Sessions : {len(sessions)}")
    print(f"[OK] Messages dans la session {sid} : {len(historique)}")
    for msg in historique:
        print(f"  [{msg['role']}] {msg['content']}")
    db.fermer()
