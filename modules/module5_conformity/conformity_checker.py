import sqlite3
from pathlib import Path
import sys

# Résolution des chemins
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import BASE_DIR, PROCESSED_DIR, RAW_PDF_DIR
from modules.module5_conformity.gri_rules import GRI_RULES, CONFORMITY_THRESHOLDS

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"

def get_session_data(session_id: str) -> dict:
    """
    Récupère le texte extrait et extrait les entités NER
    pour le rapport lié à la session donnée.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Essayer de lire depuis analysis_sessions si existant
    try:
        cursor.execute("""
            SELECT full_text FROM analysis_sessions
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        text = row[0] if row else ""
    except sqlite3.OperationalError:
        # Fallback : Récupérer le nom du rapport lié à la session
        cursor.execute("""
            SELECT rapport_name FROM sessions
            WHERE id = ?
        """, (session_id,))
        row = cursor.fetchone()
        rapport_name = row[0] if row else ""
        text = ""

        if rapport_name:
            # Charger depuis le fichier json extrait
            rapport_stem = Path(rapport_name).stem
            json_path = PROCESSED_DIR / f"{rapport_stem}_extracted.json"
            if json_path.exists():
                import json
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    pages = data.get('pages', [])
                    text_parts = [p.get('text', '') for p in pages if p.get('text')]
                    text = "\n".join(text_parts)
                except Exception as e:
                    print(f"[WARN] Erreur chargement JSON extrait: {e}")

            # Fallback ultime : extraction directe depuis le PDF brut avec PyMuPDF
            if not text:
                pdf_path = RAW_PDF_DIR / rapport_name
                if pdf_path.exists():
                    try:
                        import fitz
                        doc = fitz.open(str(pdf_path))
                        text_parts = [page.get_text('text').strip() for page in doc]
                        text = "\n".join(p for p in text_parts if p)
                        doc.close()
                        if text:
                            print(f"[OK] Conformity checker : texte extrait du PDF ({len(text)} car.)")
                    except Exception as e:
                        print(f"[WARN] Impossible d'extraire le texte du PDF : {e}")

    # Récupérer les entités NER
    entities = []
    try:
        cursor.execute("""
            SELECT entity_label, entity_text FROM ner_entities
            WHERE session_id = ?
        """, (session_id,))
        entities = [{"label": r[0], "text": r[1]} for r in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Fallback : Extraire dynamiquement les entités avec le modèle spaCy NER existant
        if text:
            try:
                from modules.module2_nlp.ml2_ner_spacy import extraire_entites
                raw_entities = extraire_entites(text)
                entities = [{"label": e["label"], "text": e["texte"]} for e in raw_entities]
            except Exception as e:
                print(f"[WARN] Erreur extraction NER : {e}")

    conn.close()
    return {"text": text, "entities": entities}


def is_indicator_present(indicator_code: str, text: str, entities: list) -> bool:
    """
    Vérifie si un indicateur GRI est présent dans le rapport.
    Utilise les mots-clés ET les entités NER déjà extraites.
    """
    rules = GRI_RULES[indicator_code]
    text_lower = text.lower()

    # Vérification des mots-clés
    keyword_found = any(
        kw.lower() in text_lower
        for kw in rules["keywords"]
    )

    if not keyword_found:
        return False

    # Si valeur numérique requise, vérifier dans les entités NER
    if rules["requires_value"]:
        has_value = any(
            e["label"] == "VALEUR"
            for e in entities
        )
        return keyword_found and has_value

    return keyword_found


def get_conformity_status(score: float) -> dict:
    """
    Retourne le statut, la couleur et l'emoji selon le score.
    """
    if score >= CONFORMITY_THRESHOLDS["CONFORME"]:
        return {
            "label": "CONFORME",
            "emoji": "✅",
            "color": "#16A34A"   # vert
        }
    elif score >= CONFORMITY_THRESHOLDS["PARTIELLEMENT_CONFORME"]:
        return {
            "label": "PARTIELLEMENT CONFORME",
            "emoji": "⚠️",
            "color": "#D97706"   # orange
        }
    else:
        return {
            "label": "NON CONFORME",
            "emoji": "❌",
            "color": "#DC2626"   # rouge
        }


def check_conformity(session_id: str) -> dict:
    """
    Fonction principale.
    Vérifie la conformité GRI 2021 d'un rapport
    en utilisant les données déjà extraites ou chargées.
    Retourne un dictionnaire hybride compatible avec chatbot_app.py
    (clés score_global_gri, score_global_esrs, dimensions) ET
    avec conformity_widget.py (clés Global, Environnemental, etc.).
    """

    # Récupérer données existantes depuis SQLite / fichiers
    data = get_session_data(session_id)
    has_text = bool(data["text"].strip()) if data["text"] else False

    # Grouper les indicateurs par dimension
    dimensions = {
        "Environnemental": ["GRI 302", "GRI 303", "GRI 305", "GRI 306"],
        "Social":          ["GRI 401", "GRI 403", "GRI 404", "GRI 405"],
        "Gouvernance":     ["GRI 205", "GRI 206", "GRI 415", "GRI 419"]
    }

    resultats = {}
    # Structure "dimensions" compatible avec chatbot_app.py
    dimensions_compat = {}
    total_presents = 0
    total_indicateurs = 0

    for dimension, indicateurs in dimensions.items():
        presents = []
        manquants = []

        for gri_code in indicateurs:
            if is_indicator_present(gri_code, data["text"], data["entities"]):
                presents.append({
                    "code": gri_code,
                    "nom": GRI_RULES[gri_code]["nom"]
                })
                total_presents += 1
            else:
                manquants.append({
                    "code": gri_code,
                    "nom": GRI_RULES[gri_code]["nom"],
                    "description": GRI_RULES[gri_code]["description"]
                })
            total_indicateurs += 1

        score = len(presents) / len(indicateurs) * 100
        status = get_conformity_status(score)

        # Format original pour conformity_widget.py
        resultats[dimension] = {
            "score": round(score, 1),
            "presents": presents,
            "manquants": manquants,
            "status": status,
            "total": len(indicateurs)
        }

        # Format compatible chatbot_app.py (sous-clés gri/esrs)
        gri_trouves = [p["code"] for p in presents]
        gri_manquants = [{"code": m["code"], "description": m["description"]} for m in manquants]
        dimensions_compat[dimension] = {
            "gri": {
                "score": round(score, 1),
                "trouves": gri_trouves,
                "manquants": gri_manquants
            },
            "esrs": {
                "score": round(score, 1),
                "trouves": gri_trouves,
                "manquants": gri_manquants
            }
        }

    # Score global
    score_global = total_presents / total_indicateurs * 100 if total_indicateurs > 0 else 0
    resultats["Global"] = {
        "score": round(score_global, 1),
        "presents_count": total_presents,
        "total_count": total_indicateurs,
        "status": get_conformity_status(score_global),
        "has_text": has_text
    }

    # Clés compatibles chatbot_app.py
    resultats["score_global_gri"] = round(score_global, 1)
    resultats["score_global_esrs"] = round(score_global, 1)
    resultats["dimensions"] = dimensions_compat
    resultats["has_text"] = has_text

    # Recommandations automatiques
    resultats["recommandations"] = generate_recommendations(resultats)

    return resultats


def generate_recommendations(resultats: dict) -> list:
    """
    Génère une liste de recommandations
    basée sur les indicateurs manquants.
    """
    recommandations = []

    RECOMMANDATIONS_MAP = {
        "GRI 302": "Ajouter les données de consommation énergétique (kWh/GJ) par source",
        "GRI 303": "Inclure les données de consommation et recyclage d'eau (m³)",
        "GRI 305": "Déclarer les émissions GES Scope 1, 2 et 3 en tCO₂e",
        "GRI 306": "Rapporter la production de déchets et les taux de recyclage (tonnes)",
        "GRI 401": "Indiquer les effectifs totaux, recrutements et départs",
        "GRI 403": "Publier les taux d'accidents du travail et de maladies professionnelles",
        "GRI 404": "Déclarer les heures de formation par employé",
        "GRI 405": "Inclure les données de diversité (% femmes, parité salariale)",
        "GRI 205": "Décrire la politique anti-corruption et les formations associées",
        "GRI 206": "Mentionner les procédures liées à la concurrence loyale",
        "GRI 415": "Déclarer les contributions politiques et activités de lobbying",
        "GRI 419": "Rapporter les amendes et sanctions réglementaires"
    }

    for dimension, data in resultats.items():
        if not isinstance(data, dict):
            continue
        if dimension == "Global" or dimension == "recommandations" or dimension == "dimensions":
            continue
        for manquant in data.get("manquants", []):
            code = manquant["code"]
            if code in RECOMMANDATIONS_MAP:
                recommandations.append({
                    "dimension": dimension,
                    "indicateur": code,
                    "nom": manquant["nom"],
                    "action": RECOMMANDATIONS_MAP[code]
                })

    return recommandations
