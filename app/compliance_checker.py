"""
Moteur de vérification de la conformité ESG réglementaire.
Compare les indicateurs extraits avec les référentiels GRI Standards 2021 et ESRS (CSRD).

Approche hybride :
  1. Détection directe des codes GRI (ex: "GRI 302", "302-1") dans le texte brut.
  2. Détection thématique par mots-clés (ex: "émissions CO2" → GRI 305) en fallback.
  3. Extraction spaCy NER si disponible.
"""
import sqlite3
import re
import sys
from pathlib import Path

# Résolution des imports
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, PROCESSED_DIR, RAW_PDF_DIR
from app.gri_referentiel import INDICATEURS_REQUIS

# ─────────────────────────────────────────────────────────────────────
# Dictionnaire de mots-clés thématiques pour la détection sans NER.
# Chaque entrée associe un code GRI normalisé à une liste de mots-clés
# en français (et anglais) couramment utilisés dans les rapports ESG.
# ─────────────────────────────────────────────────────────────────────
MOTS_CLES_GRI = {
    "GRI 302": [
        r"consommation.{0,15}énergie", r"énergie.{0,15}consomm",
        r"intensité énergétique", r"énergie renouvelable",
        r"kwh", r"mwh", r"gwh", r"tep", r"énergie primaire",
        r"mix énergétique", r"efficacité énergétique",
        r"energy consumption",
    ],
    "GRI 303": [
        r"consommation.{0,15}eau", r"eau.{0,15}consomm",
        r"prélèvement.{0,10}eau", r"effluents?",
        r"eau recyclée", r"gestion.{0,10}eau",
        r"m[³3].{0,5}eau",  r"litres? d.eau",
        r"water consumption", r"water withdrawal",
    ],
    "GRI 305": [
        r"émissions?.{0,10}gaz.{0,10}serre", r"émissions?.{0,5}co2",
        r"ges", r"gaz.{0,10}effet.{0,10}serre",
        r"scope\s*[123]", r"bilan.{0,10}carbone",
        r"tonnes?.{0,10}co2", r"teq\.?co2", r"tco2",
        r"empreinte.{0,10}carbone", r"neutralité carbone",
        r"greenhouse gas", r"ghg emissions?",
    ],
    "GRI 306": [
        r"déchets?", r"recyclage", r"valorisation.{0,10}déchet",
        r"économie circulaire", r"tonnage.{0,10}déchet",
        r"tonnes?.{0,10}déchet", r"déchets?.{0,10}dangereux",
        r"waste", r"circular economy",
    ],
    "GRI 401": [
        r"effectifs?", r"salariés?", r"collaborateurs?", r"employés?",
        r"embauches?", r"recrutements?", r"turnover",
        r"départs?", r"nombre.{0,10}employ",
        r"workforce", r"headcount",
    ],
    "GRI 403": [
        r"santé.{0,15}sécurité", r"accidents? du travail",
        r"taux.{0,10}accident", r"maladies? professionnelles?",
        r"taux.{0,10}fréquence", r"taux.{0,10}gravité",
        r"at/mp", r"absentéisme",
        r"health.{0,10}safety", r"work.{0,10}accident",
    ],
    "GRI 404": [
        r"formation", r"heures?.{0,10}formation",
        r"développement.{0,15}compétences", r"plan.{0,10}formation",
        r"e-learning", r"taux.{0,10}form",
        r"training", r"learning",
    ],
    "GRI 405": [
        r"diversité", r"égalité.{0,15}(femmes?.{0,10}hommes?|professionnelle)",
        r"parité", r"inclusion", r"féminisation",
        r"index.{0,10}égalité", r"femmes?.{0,10}(cadres?|direction|management)",
        r"diversity", r"gender",
    ],
    "GRI 205": [
        r"anti.?corruption", r"lutte.{0,15}corruption",
        r"conformité.{0,10}éthique", r"code.{0,10}éthique",
        r"code.{0,10}conduite", r"cadeaux?.{0,10}avantages?",
        r"corruption", r"bribery",
    ],
    "GRI 206": [
        r"concurrence.{0,10}loyale", r"pratiques?.{0,10}anticoncurrentielles?",
        r"droit.{0,10}concurrence", r"comportements?.{0,10}anticoncurrentiels?",
        r"competition", r"antitrust",
    ],
    "GRI 415": [
        r"lobbying", r"engagement.{0,15}politique",
        r"financement.{0,10}(politique|parti)", r"politique.{0,10}publique",
        r"association professionnelle", r"public policy",
    ],
    "GRI 419": [
        r"conformité.{0,20}(réglementaire|légale|lois?)",
        r"amendes?", r"sanctions?", r"infractions?",
        r"incidents?.{0,10}(sociaux?|environnementaux?)",
        r"violations?", r"compliance incidents?",
    ],
}

DATABASE_PATH = BASE_DIR / "data" / "chatbot_history.db"


def normaliser_reference(ref: str) -> str:
    """
    Normalise une référence d'indicateur ESG par regex.
    - GRI : "GRI 305-1" -> "GRI 305", "gri305" -> "GRI 305"
    - ESRS : "E1-5", "S1-9", "G1-3" restent identiques.
    
    :param ref: Référence brute à normaliser.
    :return: Référence normalisée.
    """
    if not ref:
        return ""
    ref_upper = ref.strip().upper()
    
    # 1. Vérification du format GRI
    # Correspond à "GRI 302", "GRI302", "GRI-302", "GRI 302-3"
    gri_match = re.search(r"GRI\s*-?\s*(\d{3})", ref_upper)
    if gri_match:
        return f"GRI {gri_match.group(1)}"
    
    # Correspond à un nombre de 3 chiffres seul type "302" ou "302-3"
    raw_gri_match = re.match(r"^(\d{3})(-\d+)?$", ref_upper)
    if raw_gri_match:
        return f"GRI {raw_gri_match.group(1)}"
        
    # 2. Vérification du format ESRS (ex: E1-5, S1-14, G1-3)
    esrs_match = re.search(r"([ESG]\d+-\d+)", ref_upper)
    if esrs_match:
        return esrs_match.group(1)
        
    return ref_upper


def initialiser_table_indicateurs(conn):
    """Crée la table indicateurs_esg si elle n'existe pas, avec toutes les colonnes enrichies."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicateurs_esg (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            rapport_name TEXT,
            reference_gri TEXT NOT NULL,
            valeur TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            unite TEXT DEFAULT NULL,
            annee TEXT DEFAULT NULL,
            dimension TEXT DEFAULT NULL,
            confiance REAL DEFAULT 1.0
        )
    """)
    # Migration : ajouter les colonnes si elles n'existent pas (BDD existante)
    for col_def in [
        "ALTER TABLE indicateurs_esg ADD COLUMN unite TEXT DEFAULT NULL",
        "ALTER TABLE indicateurs_esg ADD COLUMN annee TEXT DEFAULT NULL",
        "ALTER TABLE indicateurs_esg ADD COLUMN dimension TEXT DEFAULT NULL",
        "ALTER TABLE indicateurs_esg ADD COLUMN confiance REAL DEFAULT 1.0",
    ]:
        try:
            cursor.execute(col_def)
        except Exception:
            pass  # Colonne déjà existante
    conn.commit()


def extraire_par_mots_cles(text: str) -> set:
    """
    Détecte les indicateurs GRI/ESRS par recherche de mots-clés thématiques dans le texte.
    Cette méthode fonctionne même si le NER spaCy ne trouve rien, car les rapports RSE
    parlent rarement de "GRI 302" explicitement mais mentionnent les thèmes correspondants.
    
    :param text: Texte complet du rapport RSE.
    :return: Ensemble des codes GRI détectés (ex: {"GRI 302", "GRI 305"}).
    """
    if not text:
        return set()
    
    text_lower = text.lower()
    detectes = set()
    
    # Étape 1 : Détection directe des codes GRI explicites dans le texte
    # Correspond à "GRI 302", "GRI302", "gri-305", "302-1", etc.
    codes_directs = re.findall(r"(?:GRI\s*[-:]?\s*)?(\d{3})(?:-\d+)?", text, re.IGNORECASE)
    for code in codes_directs:
        code_gri = f"GRI {code}"
        if code_gri in MOTS_CLES_GRI:  # Ne garder que les codes connus
            detectes.add(code_gri)
    
    # Étape 2 : Détection thématique par mots-clés (robuste aux textes sans codes GRI)
    for code_gri, patterns in MOTS_CLES_GRI.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                detectes.add(code_gri)
                break  # Un seul mot-clé suffit par indicateur
    
    return detectes


def extraire_references_uniques(session_id, rapport_name=None):
    """
    Se connecte à la base SQLite existante, récupère les indicateurs de la table
    indicateurs_esg pour la session/rapport donné, normalise et retourne un set.
    
    Stratégie hybride de fallback (3 niveaux) :
      1. Récupération depuis la table indicateurs_esg (résultat NER stocké au moment de l'upload).
      2. Self-healing spaCy NER + extraction par mots-clés sur le texte JSON extrait.
      3. Extraction par mots-clés uniquement si spaCy NER échoue.
    
    :param session_id: Identifiant de la session en base.
    :param rapport_name: Nom du rapport PDF (facultatif).
    :return: Un ensemble (set) de références normalisées trouvées.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    initialiser_table_indicateurs(conn)
    cursor = conn.cursor()
    
    # 1. Récupérer le nom de fichier du rapport si non spécifié
    if not rapport_name and session_id:
        try:
            cursor.execute("SELECT rapport_name FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                rapport_name = row[0]
        except sqlite3.OperationalError:
            pass

    # 2. Chercher dans indicateurs_esg
    has_records = False
    query_params = []
    where_clauses = []
    
    if session_id:
        where_clauses.append("session_id = ?")
        query_params.append(session_id)
    if rapport_name:
        where_clauses.append("rapport_name = ?")
        query_params.append(rapport_name)
        
    if where_clauses:
        where_sql = " OR ".join(where_clauses)
        cursor.execute(f"SELECT COUNT(*) FROM indicateurs_esg WHERE {where_sql}", query_params)
        count = cursor.fetchone()[0]
        has_records = count > 0

    # 3. Self-healing : Si aucun enregistrement en base, relancer l'extraction
    if not has_records and (session_id or rapport_name):
        text = ""
        try:
            cursor.execute("SELECT full_text FROM analysis_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row:
                text = row[0]
        except sqlite3.OperationalError:
            pass

        if not text and rapport_name:
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
                    print(f"[WARN] Impossible de lire le JSON pour self-healing: {e}")

        # Fallback ultime : extraction directe depuis le PDF brut avec PyMuPDF
        if not text and rapport_name:
            pdf_path = RAW_PDF_DIR / rapport_name
            if pdf_path.exists():
                try:
                    import fitz
                    doc = fitz.open(str(pdf_path))
                    text_parts = [page.get_text('text').strip() for page in doc]
                    text = "\n".join(p for p in text_parts if p)
                    doc.close()
                    if text:
                        print(f"[OK] Self-healing : texte extrait directement du PDF ({len(text)} car.)")
                    else:
                        print(f"[WARN] Self-healing : le PDF '{rapport_name}' ne contient aucun texte vectoriel (scanné ?).")
                except Exception as e:
                    print(f"[WARN] Impossible d'extraire le texte du PDF brut : {e}")

        if text:
            # Niveau A : extraction par mots-clés thématiques (méthode principale de fallback)
            refs_mots_cles = extraire_par_mots_cles(text)
            
            # Niveau B : extraction spaCy NER (si disponible, en complément)
            refs_ner = set()
            try:
                from modules.module2_nlp.ml2_ner_spacy import extraire_entites
                raw_entities = extraire_entites(text[:50000])  # Limiter la taille
                for ent in raw_entities:
                    if ent["label"] == "REFERENCE_GRI":
                        norm = normaliser_reference(ent["texte"])
                        if norm:
                            refs_ner.add(norm)
            except Exception as e:
                print(f"[INFO] spaCy NER non disponible, mots-clés utilisés : {e}")
            
            # Fusionner les deux sources
            all_refs = refs_mots_cles | refs_ner
            
            if all_refs:
                # Déterminer la dimension de chaque indicateur pour l'enrichissement
                _DIM_MAP = {
                    "GRI 302": "Environnemental", "GRI 303": "Environnemental",
                    "GRI 305": "Environnemental", "GRI 306": "Environnemental",
                    "GRI 401": "Social", "GRI 403": "Social",
                    "GRI 404": "Social", "GRI 405": "Social",
                    "GRI 205": "Gouvernance", "GRI 206": "Gouvernance",
                    "GRI 415": "Gouvernance", "GRI 419": "Gouvernance",
                }
                for ref in all_refs:
                    dim = _DIM_MAP.get(ref, None)
                    cursor.execute("""
                        INSERT INTO indicateurs_esg (session_id, rapport_name, reference_gri, valeur, dimension, confiance)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (session_id, rapport_name, ref, None, dim, 1.0))
                conn.commit()
                print(f"[OK] Self-healing : {len(all_refs)} indicateurs détectés et stockés → {sorted(all_refs)}")
            else:
                print("[WARN] Self-healing : aucun indicateur détecté dans le texte du rapport.")

    # 4. Récupérer les indicateurs depuis la base
    references_trouvees = set()
    if where_clauses:
        where_sql = " OR ".join(where_clauses)
        cursor.execute(f"SELECT reference_gri FROM indicateurs_esg WHERE {where_sql}", query_params)
        for row in cursor.fetchall():
            norm = normaliser_reference(row[0])
            if norm:
                references_trouvees.add(norm)
                
    conn.close()
    return references_trouvees


def calculer_score_conformite(references_trouvees):
    """
    Calcule les scores de conformité pour GRI et ESRS par dimension et de manière globale.
    
    :param references_trouvees: Ensemble (set) des références normalisées détectées.
    :return: Dictionnaire structuré contenant les scores et indicateurs manquants.
    """
    resultats = {
        "score_global_gri": 0.0,
        "score_global_esrs": 0.0,
        "score_global_combine": 0.0,
        "dimensions": {}
    }
    
    somme_score_gri = 0.0
    somme_score_esrs = 0.0
    dimensions_count = 0
    
    for dimension, indicateurs in INDICATEURS_REQUIS.items():
        dimensions_count += 1
        
        # Pour GRI
        gri_requis = []
        gri_trouves = []
        gri_manquants = []
        
        # Pour ESRS
        esrs_requis = []
        esrs_trouves = []
        esrs_manquants = []
        
        for cle, info in indicateurs.items():
            # Standard GRI
            gri_code = info["GRI"]
            gri_requis.append(gri_code)
            if gri_code in references_trouvees:
                gri_trouves.append(gri_code)
            else:
                gri_manquants.append({
                    "code": gri_code,
                    "description": info["description"]
                })
                
            # Standard ESRS
            esrs_code = info["ESRS"]
            esrs_requis.append(esrs_code)
            if esrs_code in references_trouvees or gri_code in references_trouvees:
                # Si le mapping GRI correspond à l'ESRS et qu'on a le GRI, on considère présent
                esrs_trouves.append(esrs_code)
            else:
                esrs_manquants.append({
                    "code": esrs_code,
                    "description": info["description"]
                })
                
        # Calcul du score par dimension
        score_gri = (len(gri_trouves) / len(gri_requis) * 100) if gri_requis else 0.0
        score_esrs = (len(esrs_trouves) / len(esrs_requis) * 100) if esrs_requis else 0.0
        
        somme_score_gri += score_gri
        somme_score_esrs += score_esrs
        
        resultats["dimensions"][dimension] = {
            "gri": {
                "score": round(score_gri, 1),
                "trouves": gri_trouves,
                "manquants": gri_manquants
            },
            "esrs": {
                "score": round(score_esrs, 1),
                "trouves": esrs_trouves,
                "manquants": esrs_manquants
            }
        }
        
    if dimensions_count > 0:
        resultats["score_global_gri"] = round(somme_score_gri / dimensions_count, 1)
        resultats["score_global_esrs"] = round(somme_score_esrs / dimensions_count, 1)
        resultats["score_global_combine"] = round(
            (resultats["score_global_gri"] + resultats["score_global_esrs"]) / 2, 1
        )
        
    return resultats


def generer_resume_conformite_textuel(rapport_conformite):
    """
    Génère un résumé textuel clair en français destiné au prompt RAG / LLM.
    
    :param rapport_conformite: Dictionnaire retourné par calculer_score_conformite.
    :return: Chaîne de caractères formatée.
    """
    lignes = [
        "RAPPORT DE CONFORMITÉ ESG — GRI Standards 2021 & ESRS (CSRD)",
        "",
        f"Score global GRI  : {rapport_conformite['score_global_gri']:.1f}%",
        f"Score global ESRS : {rapport_conformite['score_global_esrs']:.1f}%",
        f"Score combiné     : {rapport_conformite['score_global_combine']:.1f}%",
        ""
    ]
    
    for dimension, data in rapport_conformite["dimensions"].items():
        lignes.append(f"── Dimension {dimension}e ──")
        
        # GRI
        gri_data = data["gri"]
        presents_gri = ", ".join(gri_data["trouves"]) if gri_data["trouves"] else "aucun"
        lignes.append(f"GRI  : {gri_data['score']:.1f}% ({len(gri_data['trouves'])}/4 indicateurs présents : {presents_gri})")
        for manquant in gri_data["manquants"]:
            lignes.append(f"  Indicateur GRI manquant : {manquant['code']} ({manquant['description']})")
            
        # ESRS
        esrs_data = data["esrs"]
        presents_esrs = ", ".join(esrs_data["trouves"]) if esrs_data["trouves"] else "aucun"
        lignes.append(f"ESRS : {esrs_data['score']:.1f}% ({len(esrs_data['trouves'])}/4 indicateurs présents : {presents_esrs})")
        for manquant in esrs_data["manquants"]:
            lignes.append(f"  Indicateur ESRS manquant : {manquant['code']} ({manquant['description']})")
            
        lignes.append("")
        
    return "\n".join(lignes).strip()


def extraire_et_stocker_indicateurs(rapport_name, text):
    """
    Extrait les indicateurs ESG avec une approche hybride et les stocke en base SQLite :
      1. Extraction par mots-clés thématiques (robuste, ne dépend pas du NER).
      2. Extraction spaCy NER en complément (si le modèle est disponible).
    
    :param rapport_name: Nom du fichier rapport PDF.
    :param text: Contenu textuel complet du rapport.
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    initialiser_table_indicateurs(conn)
    cursor = conn.cursor()
    
    # Supprimer les anciens indicateurs pour éviter les doublons
    cursor.execute("DELETE FROM indicateurs_esg WHERE rapport_name = ?", (rapport_name,))
    
    all_refs = set()
    
    # Méthode 1 : Extraction par mots-clés thématiques (principale)
    refs_mots_cles = extraire_par_mots_cles(text)
    all_refs |= refs_mots_cles
    print(f"[NLP] Mots-clés thématiques : {len(refs_mots_cles)} indicateurs → {sorted(refs_mots_cles)}")
    
    # Méthode 2 : Extraction spaCy NER (complémentaire)
    try:
        from modules.module2_nlp.ml2_ner_spacy import extraire_entites
        raw_entities = extraire_entites(text[:50000])  # Limiter pour la performance
        for ent in raw_entities:
            if ent["label"] == "REFERENCE_GRI":
                norm = normaliser_reference(ent["texte"])
                if norm:
                    all_refs.add(norm)
        print(f"[NLP] spaCy NER : {len(all_refs) - len(refs_mots_cles)} indicateurs supplémentaires détectés.")
    except Exception as e:
        print(f"[INFO] spaCy NER non disponible pour l'extraction initiale : {e}")
    
    # Stockage en base avec enrichissement des dimensions
    _DIM_MAP = {
        "GRI 302": "Environnemental", "GRI 303": "Environnemental",
        "GRI 305": "Environnemental", "GRI 306": "Environnemental",
        "GRI 401": "Social", "GRI 403": "Social",
        "GRI 404": "Social", "GRI 405": "Social",
        "GRI 205": "Gouvernance", "GRI 206": "Gouvernance",
        "GRI 415": "Gouvernance", "GRI 419": "Gouvernance",
    }
    for ref in all_refs:
        dim = _DIM_MAP.get(ref, None)
        cursor.execute("""
            INSERT INTO indicateurs_esg (rapport_name, reference_gri, valeur, dimension, confiance)
            VALUES (?, ?, ?, ?, ?)
        """, (rapport_name, ref, None, dim, 1.0))
    
    conn.commit()
    conn.close()
    print(f"[OK] {len(all_refs)} indicateurs ESG/GRI stockés en BDD pour : {rapport_name}")


def calculer_score_esg_global_100(rapport_conformite: dict) -> dict:
    """
    Calcule la note ESG globale sur 100 à partir des scores de conformité GRI.
    Pondération : Environnemental (40), Social (35), Gouvernance (25).
    Si une dimension a un score de 0% et aucun indicateur trouvé, elle est exclue
    (statut 'Non calculé') et le poids est redistribué proportionnellement.
    
    :param rapport_conformite: Dictionnaire retourné par calculer_score_conformite.
    :return: Dictionnaire contenant les scores sur 100 par dimension et le score global.
    """
    poids_originaux = {
        "Environnemental": 40.0,
        "Social": 35.0,
        "Gouvernance": 25.0
    }
    
    dimensions_non_calculees = []
    poids_actifs = {}
    
    # 1. Identifier les dimensions non calculées (score = 0% ET aucun indicateur trouvé)
    for dim, poids in poids_originaux.items():
        dim_data = rapport_conformite.get("dimensions", {}).get(dim, {})
        # Dans la structure de conformité, pour chaque dimension, on a dim_data['gri']['score']
        # et dim_data['gri']['trouves'].
        gri_data = dim_data.get("gri", {})
        score = gri_data.get("score", 0.0)
        trouves = gri_data.get("trouves", [])
        
        if score == 0.0 and len(trouves) == 0:
            dimensions_non_calculees.append(dim)
        else:
            poids_actifs[dim] = poids
            
    # Si aucune dimension n'est calculée
    if not poids_actifs:
        return {
            "score_environnemental_100": None,
            "score_social_100": None,
            "score_gouvernance_100": None,
            "score_global_100": None,
            "poids_utilises": poids_originaux,
            "dimensions_non_calculees": list(poids_originaux.keys())
        }
        
    # 2. Recalculer les poids des dimensions actives de sorte que leur somme fasse 100%
    somme_poids_actifs = sum(poids_actifs.values())
    poids_recalcules = {dim: (p / somme_poids_actifs) * 100.0 for dim, p in poids_actifs.items()}
    
    scores_100 = {}
    for dim in poids_originaux:
        if dim in dimensions_non_calculees:
            scores_100[dim] = None
        else:
            dim_data = rapport_conformite["dimensions"][dim]
            score_pourcent = dim_data["gri"]["score"]
            # Calcul du score sur 100 : pourcentage_trouve * poids_relatif_de_la_dimension
            scores_100[dim] = round((score_pourcent / 100.0) * poids_recalcules[dim], 2)
            
    # Le score global sur 100 est la somme des scores dimensionnels
    score_global_100 = round(sum(val for val in scores_100.values() if val is not None), 2)
    
    # Arrondir les poids utilisés pour l'affichage
    poids_utilises = {dim: round(poids_recalcules[dim], 2) for dim in poids_actifs}
    
    return {
        "score_environnemental_100": scores_100["Environnemental"],
        "score_social_100": scores_100["Social"],
        "score_gouvernance_100": scores_100["Gouvernance"],
        "score_global_100": score_global_100,
        "poids_utilises": poids_utilises,
        "dimensions_non_calculees": dimensions_non_calculees
    }

