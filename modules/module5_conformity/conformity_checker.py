import sqlite3
import re
import unicodedata
from pathlib import Path
import sys

# Résolution des chemins
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import BASE_DIR, PROCESSED_DIR, RAW_PDF_DIR
from modules.module5_conformity.gri_rules import GRI_RULES, CONFORMITY_THRESHOLDS

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"


def _clean_text(text: str) -> str:
    """Supprime les accents et passe en minuscules pour une comparaison robuste."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")


def get_session_data(session_id: str = None, rapport_name: str = None) -> dict:
    """
    Récupère le texte découpé par page et les entités pour le rapport lié à la session donnée
    ou directement pour le nom de fichier du rapport.
    Retourne : {"rapport_name": str, "pages": [{"page": int, "text": str}], "text": str, "entities": list}
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Si rapport_name n'est pas fourni, chercher à partir de session_id
    if not rapport_name and session_id is not None:
        s_val = str(session_id).strip()
        if s_val.lower().endswith(".pdf") or not s_val.isdigit():
            rapport_name = s_val
        else:
            try:
                cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    rapport_name = row[0]
            except Exception:
                pass

    pages_data = []
    full_text = ""

    if rapport_name:
        rapport_stem = Path(rapport_name).stem
        json_path = PROCESSED_DIR / f"{rapport_stem}_extracted.json"
        
        # 1. Charger depuis le JSON extrait s'il existe
        if json_path.exists():
            import json
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                for p in d.get("pages", []):
                    ptxt = p.get("text", "")
                    pnum = p.get("page_number", len(pages_data) + 1)
                    if ptxt.strip():
                        pages_data.append({"page": pnum, "text": ptxt})
                full_text = "\n".join(p["text"] for p in pages_data)
            except Exception as e:
                print(f"[WARN] Erreur lecture JSON extrait : {e}")

        # 2. Fallback direct : extraction PyMuPDF page par page
        if not pages_data:
            pdf_path = RAW_PDF_DIR / rapport_name
            if pdf_path.exists():
                try:
                    import fitz
                    doc = fitz.open(str(pdf_path))
                    for idx, page in enumerate(doc):
                        ptxt = page.get_text("text").strip()
                        if ptxt:
                            pages_data.append({"page": idx + 1, "text": ptxt})
                    doc.close()
                    full_text = "\n".join(p["text"] for p in pages_data)
                except Exception as e:
                    print(f"[WARN] Erreur extraction PDF : {e}")

    # Récupérer les entités déjà enregistrées en base
    entities = []
    try:
        cursor.execute("""
            SELECT valeur FROM indicateurs_esg
            WHERE (session_id = ? OR rapport_name = ?) AND valeur IS NOT NULL
        """, (session_id, rapport_name))
        for r in cursor.fetchall():
            if r[0]:
                entities.append({"label": "VALEUR", "text": str(r[0])})
    except Exception:
        pass

    conn.close()
    return {
        "rapport_name": rapport_name,
        "pages": pages_data,
        "text": full_text,
        "entities": entities
    }


def detect_indicator(indicator_code: str, pages_data: list) -> dict:
    """
    Détecte précisément si un indicateur GRI est présent en scannant page par page.
    Retourne :
      {
        "present": bool,
        "pages": list[int],
        "pages_str": str,
        "snippet": str
      }
    """
    rules = GRI_RULES.get(indicator_code)
    if not rules:
        return {"present": False, "pages": [], "pages_str": "", "snippet": ""}

    code_regex = rules.get("code_regex", "")
    patterns = rules.get("patterns", [])
    found_pages = []
    snippet = ""

    for p in pages_data:
        pnum = p.get("page", 1)
        raw_text = p.get("text", "")
        clean = _clean_text(raw_text)

        matched = False
        # 1. Vérifier si le code explicite apparaît (ex: GRI 302, 302-1)
        if code_regex and re.search(code_regex, clean):
            matched = True
        else:
            # 2. Vérifier les motifs contextuels stricts
            for pat in patterns:
                pat_clean = _clean_text(pat)
                if re.search(pat_clean, clean):
                    matched = True
                    break

        if matched:
            found_pages.append(pnum)
            if not snippet:
                # Extraire un extrait court représentatif
                lines = [l.strip() for l in raw_text.split("\n") if len(l.strip()) > 15]
                snippet = lines[0] if lines else ""

    found_pages = sorted(list(set(found_pages)))
    is_present = len(found_pages) > 0

    pages_str = ""
    if is_present:
        if len(found_pages) <= 4:
            pages_str = "Page" + ("s " if len(found_pages) > 1 else " ") + ", ".join(str(p) for p in found_pages)
        else:
            pages_str = f"Pages {found_pages[0]}, {found_pages[1]}, {found_pages[2]} (+{len(found_pages)-3})"

    return {
        "present": is_present,
        "pages": found_pages,
        "pages_str": pages_str,
        "snippet": snippet
    }


def get_conformity_status(score: float) -> dict:
    """Retourne le statut, la couleur et l'emoji selon le score."""
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


def check_conformity(session_id: str = None, rapport_name: str = None) -> dict:
    """
    Fonction principale de vérification de conformité GRI & ESRS.
    Analyse page par page avec précision, identifie les pages exactes de chaque indicateur,
    et synchronise la base SQLite.
    """
    data = get_session_data(session_id=session_id, rapport_name=rapport_name)
    pages_data = data.get("pages", [])
    rapport_name = data.get("rapport_name", "")
    has_text = bool(data.get("text", "").strip())

    # Dimensions réglementaires GRI Standards
    dimensions = {
        "Environnemental": ["GRI 302", "GRI 303", "GRI 305", "GRI 306"],
        "Social":          ["GRI 401", "GRI 403", "GRI 404", "GRI 405"],
        "Gouvernance":     ["GRI 205", "GRI 206", "GRI 415", "GRI 419"]
    }

    resultats = {}
    dimensions_compat = {}
    total_presents = 0
    total_indicateurs = 0

    all_detected_records = []

    for dimension, indicateurs in dimensions.items():
        presents = []
        manquants = []

        for gri_code in indicateurs:
            det = detect_indicator(gri_code, pages_data)
            info = GRI_RULES[gri_code]

            if det["present"]:
                item = {
                    "code": gri_code,
                    "nom": info["nom"],
                    "pages": det["pages"],
                    "pages_str": det["pages_str"],
                    "snippet": det["snippet"]
                }
                presents.append(item)
                total_presents += 1
                all_detected_records.append({
                    "reference_gri": gri_code,
                    "dimension": dimension,
                    "page": det["pages_str"],
                    "pages_list": det["pages"]
                })
            else:
                manquants.append({
                    "code": gri_code,
                    "nom": info["nom"],
                    "description": info["description"]
                })
            total_indicateurs += 1

        score = (len(presents) / len(indicateurs) * 100) if indicateurs else 0.0
        status = get_conformity_status(score)

        resultats[dimension] = {
            "score": round(score, 1),
            "presents": presents,
            "manquants": manquants,
            "status": status,
            "total": len(indicateurs)
        }

        # Format structuré compatible Streamlit
        dimensions_compat[dimension] = {
            "gri": {
                "score": round(score, 1),
                "trouves": presents,  # liste d'objets avec code, nom, pages_str
                "manquants": manquants
            },
            "esrs": {
                "score": round(score, 1),
                "trouves": presents,
                "manquants": manquants
            }
        }

    score_global = (total_presents / total_indicateurs * 100) if total_indicateurs > 0 else 0.0
    
    resultats["Global"] = {
        "score": round(score_global, 1),
        "presents_count": total_presents,
        "total_count": total_indicateurs,
        "status": get_conformity_status(score_global),
        "has_text": has_text,
        "rapport_name": rapport_name
    }

    resultats["score_global_gri"] = round(score_global, 1)
    resultats["score_global_esrs"] = round(score_global, 1)
    resultats["dimensions"] = dimensions_compat
    resultats["has_text"] = has_text
    resultats["rapport_name"] = rapport_name

    # Recommandations automatiques basées sur les indicateurs manquants
    resultats["recommandations"] = generate_recommendations(resultats)

    # Note ESG pondérée sur 100
    try:
        from app.compliance_checker import calculer_score_esg_global_100
        resultats["score_esg_100"] = calculer_score_esg_global_100(resultats)
    except Exception:
        resultats["score_esg_100"] = {"note_globale_100": round(score_global, 1)}

    # Synchroniser les pages détectées dans la table indicateurs_esg en SQLite
    if rapport_name and all_detected_records:
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cur = conn.cursor()
            for rec in all_detected_records:
                cur.execute("""
                    UPDATE indicateurs_esg 
                    SET page = ?
                    WHERE (rapport_name = ? OR session_id = ?) AND reference_gri = ?
                """, (rec["page"], rapport_name, session_id, rec["reference_gri"]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[WARN] Erreur mise à jour pages dans BDD : {e}")

    return resultats


def generate_recommendations(resultats: dict) -> list:
    """Génère des recommandations ciblées basées sur les indicateurs manquants."""
    recommandations = []

    RECOMMANDATIONS_MAP = {
        "GRI 302": "Publier les données consolidées de consommation d'énergie totale (kWh/MWh) et le mix énergétique renouvelable.",
        "GRI 303": "Intégrer le bilan des prélèvements et rejets d'eau (m³) ainsi que l'évaluation du stress hydrique des sites.",
        "GRI 305": "Quantifier précisément les émissions de gaz à effet de serre selon le protocole GHG (Scope 1 direct et Scope 2 indirect en tCO₂e).",
        "GRI 306": "Documenter la production totale de déchets (tonnes), la part valorisée/recyclée et les filières agréées d'élimination.",
        "GRI 401": "Détailler les effectifs totaux (ETP), les taux de recrutement et de rotation du personnel (turnover) sur l'exercice.",
        "GRI 403": "Déclarer les statistiques de santé et sécurité au travail : taux de fréquence et de gravité des accidents du travail.",
        "GRI 404": "Indiquer le nombre moyen d'heures de formation dispensées par salarié et par catégorie socioprofessionnelle.",
        "GRI 405": "Fournir les indicateurs de mixité et de parité : % de femmes dans le management et index d'égalité professionnelle.",
        "GRI 205": "Formaliser une politique anti-corruption, un code de conduite éthique et un dispositif d'alerte professionnelle (whistleblowing).",
        "GRI 206": "Déclarer la conformité aux règles de concurrence loyale et les éventuelles procédures juridiques antitrust.",
        "GRI 415": "Déclarer explicitement la politique de l'entreprise concernant le lobbying et les contributions financières aux partis politiques.",
        "GRI 419": "Publier l'état des éventuelles amendes ou sanctions administratives ou juridiques pour non-conformité réglementaire."
    }

    dimensions = ["Environnemental", "Social", "Gouvernance"]
    for dim in dimensions:
        dim_data = resultats.get(dim, {})
        for m in dim_data.get("manquants", []):
            code = m["code"]
            action = RECOMMANDATIONS_MAP.get(code, f"Intégrer le reporting relatif à {m['nom']}")
            recommandations.append({
                "dimension": dim,
                "indicateur": code,
                "nom": m["nom"],
                "action": action
            })

    return recommandations
