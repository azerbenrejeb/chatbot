import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, OLLAMA_MODEL
from modules.module5_conformity.conformity_checker import check_conformity, get_session_data, detect_indicator
from modules.module5_conformity.gri_rules import GRI_RULES
from app.gri_referentiel import INDICATEURS_REQUIS
import ollama

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"


def _resoudre_session_ou_nom(target: str) -> tuple[str, str]:
    """
    Détermine si target est un ID de session ou un nom de rapport PDF.
    Retourne : (session_id_str, rapport_name)
    """
    target_str = str(target).strip()
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    # Si c'est un entier -> c'est un session_id
    if target_str.isdigit():
        sid = target_str
        cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (int(sid),))
        row = cursor.fetchone()
        rapport_name = row[0] if row and row[0] else f"Session {sid}"
        conn.close()
        return sid, rapport_name

    # Sinon c'est un nom de rapport PDF
    rapport_name = target_str
    cursor.execute("SELECT id FROM sessions WHERE rapport_name = ?", (rapport_name,))
    row = cursor.fetchone()
    if row:
        sid = str(row[0])
    else:
        # Créer une session légère pour ce rapport
        cursor.execute("INSERT INTO sessions (rapport_name, titre) VALUES (?, ?)", (rapport_name, f"Analyse {rapport_name}"))
        conn.commit()
        sid = str(cursor.lastrowid)
    conn.close()
    return sid, rapport_name


def comparer_rapports(identifiant_a, identifiant_b) -> dict:
    """
    Compare deux rapports RSE/ESG (soit par session_id, soit par nom de fichier).
    Effectue un audit rigoureux des 12 indicateurs GRI sur les 3 dimensions.
    """
    sid_a, name_a = _resoudre_session_ou_nom(identifiant_a)
    sid_b, name_b = _resoudre_session_ou_nom(identifiant_b)

    res_a = check_conformity(sid_a)
    res_b = check_conformity(sid_b)

    score_a = {
        "gri": res_a.get("score_global_gri", 0.0),
        "esrs": res_a.get("score_global_esrs", 0.0)
    }
    score_b = {
        "gri": res_b.get("score_global_gri", 0.0),
        "esrs": res_b.get("score_global_esrs", 0.0)
    }

    # Tableau comparatif complet des 12 indicateurs
    dimensions = ["Environnemental", "Social", "Gouvernance"]
    tableau_comparatif = []
    indicateurs_communs = {}

    for dim in dimensions:
        info_dim_a = res_a.get(dim, {})
        info_dim_b = res_b.get(dim, {})

        # Dictionnaires par code
        presents_a = {p["code"]: p for p in info_dim_a.get("presents", [])}
        presents_b = {p["code"]: p for p in info_dim_b.get("presents", [])}

        codes_dim = ["GRI 302", "GRI 303", "GRI 305", "GRI 306"] if dim == "Environnemental" else (
            ["GRI 401", "GRI 403", "GRI 404", "GRI 405"] if dim == "Social" else
            ["GRI 205", "GRI 206", "GRI 415", "GRI 419"]
        )

        for code in codes_dim:
            rule = GRI_RULES.get(code, {})
            nom_ind = rule.get("nom", code)
            desc_ind = rule.get("description", "")

            pa = presents_a.get(code)
            pb = presents_b.get(code)

            statut_a = f"✅ Présent ({pa.get('pages_str', 'Pages')})" if pa else "❌ Non détecté"
            statut_b = f"✅ Présent ({pb.get('pages_str', 'Pages')})" if pb else "❌ Non détecté"

            tableau_comparatif.append({
                "Dimension": dim,
                "Code": code,
                "Indicateur": nom_ind,
                "Rapport A": statut_a,
                "Rapport B": statut_b,
                "Couverture": "Les deux" if (pa and pb) else (f"Seulement {name_a[:15]}" if pa else (f"Seulement {name_b[:15]}" if pb else "Aucun"))
            })

            if pa and pb:
                indicateurs_communs[code] = {
                    "description": nom_ind,
                    "rapport_a": pa.get("pages_str", "Présent"),
                    "rapport_b": pb.get("pages_str", "Présent"),
                    "unite": ""
                }

    return {
        "nom_rapport_a": name_a,
        "nom_rapport_b": name_b,
        "score_a": score_a,
        "score_b": score_b,
        "scores_dimensions": {
            "Environnemental": {
                "score_a": res_a.get("Environnemental", {}).get("score", 0.0),
                "score_b": res_b.get("Environnemental", {}).get("score", 0.0)
            },
            "Social": {
                "score_a": res_a.get("Social", {}).get("score", 0.0),
                "score_b": res_b.get("Social", {}).get("score", 0.0)
            },
            "Gouvernance": {
                "score_a": res_a.get("Gouvernance", {}).get("score", 0.0),
                "score_b": res_b.get("Gouvernance", {}).get("score", 0.0)
            }
        },
        "tableau_comparatif": tableau_comparatif,
        "indicateurs_communs": indicateurs_communs
    }


def generer_synthese_comparaison(resultat_comparaison: dict) -> str:
    """
    Génère une synthèse comparative fluide et structurée via Mistral ou fallback local.
    """
    name_a = resultat_comparaison.get("nom_rapport_a", "Rapport A")
    name_b = resultat_comparaison.get("nom_rapport_b", "Rapport B")
    sc_a = resultat_comparaison.get("score_a", {}).get("gri", 0.0)
    sc_b = resultat_comparaison.get("score_b", {}).get("gri", 0.0)
    dims = resultat_comparaison.get("scores_dimensions", {})

    communs = resultat_comparaison.get("indicateurs_communs", {})
    nb_communs = len(communs)

    # Prompt pour Mistral
    prompt = f"""Tu es un auditeur ESG expert. Rédige une synthèse comparative en 5 lignes maximum comparant ces deux rapports RSE :
- Rapport A : {name_a} (Score global GRI : {sc_a}%, E: {dims.get('Environnemental',{}).get('score_a')}%, S: {dims.get('Social',{}).get('score_a')}%, G: {dims.get('Gouvernance',{}).get('score_a')}%)
- Rapport B : {name_b} (Score global GRI : {sc_b}%, E: {dims.get('Environnemental',{}).get('score_b')}%, S: {dims.get('Social',{}).get('score_b')}%, G: {dims.get('Gouvernance',{}).get('score_b')}%)
- Nombre d'indicateurs GRI communs déclarés : {nb_communs} sur 12.

Mets en évidence le rapport ayant la meilleure maturité globale et les dimensions de différenciation. Réponds en français de façon concise et professionnelle."""

    try:
        import requests
        resp = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "Tu es un expert ESG chargé de synthèses comparatives structurées et objectives en français."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=20
        )
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "").strip()
    except Exception:
        pass

    # Fallback analytique déterministe immédiat
    meilleur = name_a if sc_a > sc_b else (name_b if sc_b > sc_a else "les deux rapports au même niveau")
    lignes = [
        f"**Synthèse Comparative ESG :**",
        f"- **Maturité globale :** {name_a} affiche un score de conformité GRI de **{sc_a}%** contre **{sc_b}%** pour {name_b}.",
        f"- **Dimension Environnementale :** {name_a} ({dims.get('Environnemental',{}).get('score_a')}%) vs {name_b} ({dims.get('Environnemental',{}).get('score_b')}%).",
        f"- **Dimension Sociale :** {name_a} ({dims.get('Social',{}).get('score_a')}%) vs {name_b} ({dims.get('Social',{}).get('score_b')}%).",
        f"- **Gouvernance :** {name_a} ({dims.get('Gouvernance',{}).get('score_a')}%) vs {name_b} ({dims.get('Gouvernance',{}).get('score_b')}%).",
        f"- **Convergence :** {nb_communs} indicateurs GRI sont conjointement couverts par les deux entreprises."
    ]
    return "\n\n".join(lignes)
