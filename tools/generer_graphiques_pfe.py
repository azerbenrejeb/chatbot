"""
Génère les graphiques et métriques du PFE (section « Résultats » et « Limites et perspectives »).

Sorties (dossier graphiques/) :
  A. Performances des modèles (valeurs mesurées sur le jeu de test de 581 paragraphes)
     g1_comparaison_modeles.png, g2_matrice_confusion_camembert.png,
     g3_metriques_par_classe_camembert.png, g4_ner_spacy.png
  B. Analyse critique du dataset (weak supervision)
     g5_distribution_classes.png, g6_marge_annotation.png,
     g7_longueur_paragraphes.png, g8_sous_chaines_parasites.png
  C. CNN : du filtre binaire au scoring (mesure réelle sur un rapport)
     g9_scores_cnn.png
  D. Conformité : regex seule vs regex + filet sémantique (mesure réelle sur les rapports extraits)
     g10_regex_vs_semantique.png, g11_calibration_seuil.png
  + metriques_pfe.json (toutes les valeurs chiffrées)

Usage : python tools/generer_graphiques_pfe.py
"""
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent))
from app.config import GRAPHIQUES_DIR, ML_DATASET_DIR, PROCESSED_DIR, RAW_PDF_DIR, MODELS_DIR

GRAPHIQUES_DIR.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid")
COULEURS = {"Environnemental": "#2E7D32", "Social": "#1565C0", "Gouvernance": "#EF6C00"}
METRIQUES = {}


def sauver(fig, nom):
    chemin = GRAPHIQUES_DIR / nom
    fig.tight_layout()
    fig.savefig(chemin, dpi=150)
    plt.close(fig)
    print(f"[OK] {chemin.name}")


# ═══════════════════════════════════════════════════════════════════
# A. PERFORMANCES DES MODÈLES (valeurs mesurées par evaluate_ml.py)
# ═══════════════════════════════════════════════════════════════════
def section_a():
    modeles = {
        "TF-IDF + Rég. Log.": (89.33, 89.08),
        "Random Forest": (90.71, 90.73),
        "CamemBERT": (90.88, 90.84),
    }
    METRIQUES["classification"] = {k: {"accuracy": v[0], "f1_macro": v[1]} for k, v in modeles.items()}

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(modeles))
    acc = [v[0] for v in modeles.values()]
    f1 = [v[1] for v in modeles.values()]
    b1 = ax.bar(x - 0.2, acc, 0.4, label="Accuracy", color="#455A64")
    b2 = ax.bar(x + 0.2, f1, 0.4, label="F1-macro", color="#90A4AE")
    ax.bar_label(b1, fmt="%.2f%%", fontsize=9)
    ax.bar_label(b2, fmt="%.2f%%", fontsize=9)
    ax.set_xticks(x, modeles.keys())
    ax.set_ylim(85, 93)
    ax.set_ylabel("Score (%)")
    ax.set_title("Classification E/S/G — comparaison des 3 modèles (test, n=581)")
    ax.legend()
    sauver(fig, "g1_comparaison_modeles.png")

    # Matrice de confusion CamemBERT (ordre : E, S, G)
    labels = ["Environnemental", "Social", "Gouvernance"]
    cm = np.array([[213, 18, 15], [5, 176, 8], [5, 2, 139]])
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel("Classe prédite")
    ax.set_ylabel("Classe réelle")
    ax.set_title("CamemBERT — Matrice de confusion")
    sauver(fig, "g2_matrice_confusion_camembert.png")

    par_classe = {
        "Environnemental": (0.96, 0.87, 0.91),
        "Social": (0.90, 0.93, 0.91),
        "Gouvernance": (0.86, 0.95, 0.90),
    }
    METRIQUES["camembert_par_classe"] = {k: dict(zip(["precision", "recall", "f1"], v)) for k, v in par_classe.items()}
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(3)
    for i, (nom, idx) in enumerate([("Précision", 0), ("Rappel", 1), ("F1", 2)]):
        vals = [v[idx] * 100 for v in par_classe.values()]
        b = ax.bar(x + (i - 1) * 0.27, vals, 0.27, label=nom)
        ax.bar_label(b, fmt="%.0f", fontsize=8)
    ax.set_xticks(x, par_classe.keys())
    ax.set_ylim(80, 100)
    ax.set_ylabel("%")
    ax.set_title("CamemBERT — métriques par pilier")
    ax.legend()
    sauver(fig, "g3_metriques_par_classe_camembert.png")

    ner = {"Précision": 95.36, "Rappel": 96.58, "F1": 95.97}
    METRIQUES["ner_spacy"] = ner
    fig, ax = plt.subplots(figsize=(6, 4))
    b = ax.bar(ner.keys(), ner.values(), color=["#6A1B9A", "#8E24AA", "#AB47BC"])
    ax.bar_label(b, fmt="%.2f%%")
    ax.set_ylim(90, 100)
    ax.set_title("spaCy NER personnalisé (entités ESG)")
    sauver(fig, "g4_ner_spacy.png")


# ═══════════════════════════════════════════════════════════════════
# B. ANALYSE ET QUALITÉ DU DATASET
# ═══════════════════════════════════════════════════════════════════
def section_b():
    from prepare_ml_annotations import LABEL_KEYWORDS, normalize

    df = pd.read_csv(ML_DATASET_DIR / "classification" / "ml_dataset.csv")
    counts = df["label"].value_counts()
    METRIQUES["dataset"] = {"total": int(len(df)), "par_classe": {k: int(v) for k, v in counts.items()}}

    fig, ax = plt.subplots(figsize=(6, 4))
    b = ax.bar(counts.index, counts.values, color=[COULEURS[c] for c in counts.index])
    ax.bar_label(b)
    ax.set_title(f"Répartition du dataset annoté (n={len(df)})")
    sauver(fig, "g5_distribution_classes.png")

    # Marge entre le 1er et le 2e score de mots-clés
    scores = df[["score_env", "score_social", "score_gouv"]].values
    tri = -np.sort(-scores, axis=1)
    marge = tri[:, 0] - tri[:, 1]
    pct_marge1 = float((marge == 1).mean() * 100)
    METRIQUES["annotation"] = {"pct_marge_1": round(pct_marge1, 1), "marge_moyenne": round(float(marge.mean()), 2)}
    fig, ax = plt.subplots(figsize=(7, 4))
    vals, nb = np.unique(marge, return_counts=True)
    b = ax.bar(vals, nb, color=["#C62828" if v == 1 else "#78909C" for v in vals])
    ax.bar_label(b, fontsize=8)
    ax.set_xlabel("Marge = score(1er pilier) − score(2e pilier)")
    ax.set_ylabel("Paragraphes")
    ax.set_title(f"Fragilité de l'annotation : {pct_marge1:.1f}% des labels tiennent à 1 seul mot-clé")
    sauver(fig, "g6_marge_annotation.png")

    longueurs = df["texte"].astype(str).str.split().str.len()
    METRIQUES["longueur_mots"] = {"mediane": int(longueurs.median()), "p95": int(longueurs.quantile(0.95))}
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(longueurs.clip(upper=300), bins=40, color="#546E7A")
    ax.axvline(longueurs.median(), color="red", ls="--", label=f"Médiane = {int(longueurs.median())} mots")
    ax.set_xlabel("Longueur (mots)")
    ax.set_title("Longueur des paragraphes du dataset")
    ax.legend()
    sauver(fig, "g7_longueur_paragraphes.png")

    # Sous-chaînes parasites : correspondance "sous-chaîne" vs "mot entier"
    textes = [normalize(t) for t in df["texte"].astype(str)]
    tous_mots = [kw for kws in LABEL_KEYWORDS.values() for kw in kws]
    resultats = []
    for kw in tous_mots:
        motif = re.compile(r"\b" + re.escape(kw) + r"\b")
        n_sub = sum(1 for t in textes if kw in t)
        n_mot = sum(1 for t in textes if motif.search(t))
        if n_sub:
            resultats.append((kw, n_sub, n_mot, n_sub - n_mot))
    resultats.sort(key=lambda r: r[3], reverse=True)
    top = resultats[:10]

    # Combien de labels changeraient avec une recherche par mot entier ?
    def label_mot_entier(t):
        sc = {lab: sum(1 for kw in kws if re.search(r"\b" + re.escape(kw) + r"\b", t))
              for lab, kws in LABEL_KEYWORDS.items()}
        ordre = sorted(sc.items(), key=lambda i: i[1], reverse=True)
        if ordre[0][1] < 2 or ordre[0][1] == ordre[1][1]:
            return None
        return ordre[0][0]

    nouveaux = [label_mot_entier(t) for t in textes]
    changes = sum(1 for a, b in zip(df["label"], nouveaux) if b is not None and a != b)
    rejetes = sum(1 for b in nouveaux if b is None)
    METRIQUES["sous_chaines"] = {
        "top_faux_positifs": {r[0]: r[3] for r in top},
        "labels_changes_mot_entier": changes,
        "paragraphes_devenus_ambigus": rejetes,
        "pct_dataset_affecte": round((changes + rejetes) / len(df) * 100, 1),
    }

    fig, ax = plt.subplots(figsize=(8, 5))
    y = np.arange(len(top))
    ax.barh(y, [r[2] for r in top], color="#2E7D32", label="Mot entier (correct)")
    ax.barh(y, [r[3] for r in top], left=[r[2] for r in top], color="#C62828", label="Sous-chaîne parasite")
    ax.set_yticks(y, [f"« {r[0]} »" for r in top])
    ax.invert_yaxis()
    ax.set_xlabel("Paragraphes contenant le mot-clé")
    ax.set_title(f"Faux positifs par sous-chaîne — {changes} labels changeraient, "
                 f"{rejetes} deviendraient ambigus")
    ax.legend()
    sauver(fig, "g8_sous_chaines_parasites.png")


# ═══════════════════════════════════════════════════════════════════
# C. CNN : DU FILTRE BINAIRE AU SCORING (mesure réelle)
# ═══════════════════════════════════════════════════════════════════
def section_c(nom_pdf="Rapport_RSE_Colas_2023.pdf"):
    import torch
    import torchvision.transforms as transforms
    from PIL import Image
    from extraction.pdf_to_images import convert_pdf_to_images
    from modules.module1_cnn.cnn_classifier import get_model

    pdf_path = RAW_PDF_DIR / nom_pdf
    poids = MODELS_DIR / "cnn_resnet50_esg.pth"
    if not pdf_path.exists() or not poids.exists():
        print("[WARN] Section C ignorée (PDF ou poids CNN absents).")
        return

    # Même chargement que app/main.py
    model = get_model(num_classes=2)
    model.load_state_dict(torch.load(str(poids), map_location="cpu", weights_only=True))
    model.eval()
    transform = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    tmp = GRAPHIQUES_DIR / "_tmp_cnn"
    tmp.mkdir(exist_ok=True)
    try:
        convert_pdf_to_images(pdf_path, tmp)
        images = sorted(tmp.glob(f"{pdf_path.stem}_page_*.jpg"),
                        key=lambda p: int(p.stem.split("_page_")[-1]))
        scores = []
        for img in images:
            t = transform(Image.open(img).convert("RGB")).unsqueeze(0)
            with torch.no_grad():
                scores.append(torch.softmax(model(t), dim=1)[0][0].item())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    scores = np.array(scores)
    perdues = int((scores < 0.5).sum())
    zone_grise = int(((scores >= 0.3) & (scores < 0.7)).sum())
    METRIQUES["cnn_scoring"] = {
        "rapport": nom_pdf, "pages": int(len(scores)),
        "pages_eliminees_par_argmax": perdues,
        "pct_pages_eliminees": round(perdues / max(len(scores), 1) * 100, 1),
        "pages_zone_grise_0.3_0.7": zone_grise,
        "score_moyen": round(float(scores.mean()), 3),
    }

    fig, ax = plt.subplots(figsize=(10, 4.5))
    couleurs = ["#2E7D32" if s >= 0.5 else "#C62828" for s in scores]
    ax.bar(np.arange(1, len(scores) + 1), scores, color=couleurs)
    ax.axhline(0.5, color="black", ls="--", lw=1, label="Ancien seuil argmax (0.5)")
    ax.set_xlabel("Page")
    ax.set_ylabel("P(ESG) — softmax")
    ax.set_ylim(0, 1)
    ax.set_title(f"CNN sur « {nom_pdf} » : {perdues}/{len(scores)} pages auraient été supprimées "
                 f"par l'ancien filtre — désormais conservées et notées")
    ax.legend()
    sauver(fig, "g9_scores_cnn.png")


# ═══════════════════════════════════════════════════════════════════
# D. CONFORMITÉ : REGEX SEULE vs REGEX + FILET SÉMANTIQUE
# ═══════════════════════════════════════════════════════════════════
def _sans_accents(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def detecter_regex(pages_data, mots_cles):
    """Réplique la détection regex de extraire_et_stocker_indicateurs (sans écriture BDD)."""
    trouves = set()
    for code, patterns in mots_cles.items():
        num = code.replace("GRI ", "")
        pats = [_sans_accents(p) for p in patterns]
        for p in pages_data:
            txt = _sans_accents(p["text"])
            if re.search(rf"gri\s*{num}|{num}-\d", txt) or any(re.search(pt, txt) for pt in pats):
                trouves.add(code)
                break
    return trouves


def section_d(max_rapports=8):
    from sentence_transformers import util
    import app.compliance_checker as cc

    cc.MAX_PASSAGES_SEMANTIQUE = 800  # Plafond réduit pour le benchmark CPU
    embedder = cc._get_embedder()
    phrases = cc.get_phrases_reference()
    codes = list(cc.MOTS_CLES_GRI.keys())
    emb_refs = {c: embedder.encode(phrases[c], convert_to_tensor=True) for c in codes}

    exclus = ("table03", "world-stats", "pocketbook")
    fichiers = [f for f in sorted(PROCESSED_DIR.glob("*_extracted.json")) if not any(e in f.name.lower() for e in exclus)]
    lignes, scores_pos, scores_neg = [], [], []

    for f in fichiers:
        if len(lignes) >= max_rapports:
            break
        data = json.loads(f.read_text(encoding="utf-8"))
        pages = [{"page": p.get("page_number", i + 1), "text": p.get("text", "")}
                 for i, p in enumerate(data.get("pages", [])) if p.get("text", "").strip()]
        if sum(len(p["text"]) for p in pages) < 2000:
            continue
        regex = detecter_regex(pages, cc.MOTS_CLES_GRI)
        passages = cc._decouper_passages(pages)
        if not passages:
            continue
        emb = embedder.encode([p["texte"] for p in passages], convert_to_tensor=True,
                              batch_size=64, show_progress_bar=False)
        best = {c: float(util.cos_sim(emb_refs[c], emb)[0].max()) for c in codes}
        for c in codes:
            (scores_pos if c in regex else scores_neg).append(best[c])
        recup = [c for c in codes if c not in regex and best[c] >= cc.SEUIL_SEMANTIQUE]
        nom = f.name.replace("_extracted.json", "")[:28]
        lignes.append({"rapport": nom, "regex": len(regex), "semantique": len(recup),
                       "absents": len(codes) - len(regex) - len(recup), "codes_recuperes": recup})
        print(f"   {nom}: regex={len(regex)} +sémantique={len(recup)}")

    if not lignes:
        print("[WARN] Section D ignorée (aucun rapport exploitable).")
        return

    tot_regex = sum(l["regex"] for l in lignes)
    tot_sem = sum(l["semantique"] for l in lignes)
    METRIQUES["conformite"] = {
        "rapports_testes": len(lignes),
        "indicateurs_possibles": len(lignes) * len(codes),
        "trouves_regex": tot_regex,
        "recuperes_semantique": tot_sem,
        "gain_couverture_pct": round(tot_sem / max(tot_regex, 1) * 100, 1),
        "seuil": cc.SEUIL_SEMANTIQUE,
        "score_moyen_indic_trouves_regex": round(float(np.mean(scores_pos)), 3) if scores_pos else None,
        "score_moyen_indic_absents_regex": round(float(np.mean(scores_neg)), 3) if scores_neg else None,
        "detail": lignes,
    }

    fig, ax = plt.subplots(figsize=(10, 5))
    noms = [l["rapport"] for l in lignes]
    r = [l["regex"] for l in lignes]
    s = [l["semantique"] for l in lignes]
    a = [l["absents"] for l in lignes]
    ax.barh(noms, r, color="#1565C0", label="Trouvé par regex")
    ax.barh(noms, s, left=r, color="#F9A825", label="Récupéré par le filet sémantique")
    ax.barh(noms, a, left=np.add(r, s), color="#E0E0E0", label="Absent")
    ax.set_xlabel(f"Indicateurs GRI (sur {len(codes)})")
    ax.set_title(f"Couverture GRI : +{tot_sem} indicateurs récupérés par le filet sémantique "
                 f"(seuil {cc.SEUIL_SEMANTIQUE})")
    ax.invert_yaxis()
    ax.legend(loc="lower right")
    sauver(fig, "g10_regex_vs_semantique.png")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bins = np.linspace(0, 1, 30)
    ax.hist(scores_pos, bins=bins, alpha=0.7, color="#1565C0", label="Indicateurs trouvés par regex")
    ax.hist(scores_neg, bins=bins, alpha=0.7, color="#C62828", label="Indicateurs NON trouvés par regex")
    ax.axvline(cc.SEUIL_SEMANTIQUE, color="black", ls="--", label=f"Seuil = {cc.SEUIL_SEMANTIQUE}")
    ax.set_xlabel("Meilleure similarité cosinus (passage ↔ phrase de référence GRI)")
    ax.set_ylabel("Nombre (rapport × indicateur)")
    ax.set_title("Calibration du seuil sémantique")
    ax.legend()
    sauver(fig, "g11_calibration_seuil.png")


if __name__ == "__main__":
    for nom, fn in [("A — Modèles", section_a), ("B — Dataset", section_b),
                    ("C — CNN scoring", section_c), ("D — Regex vs sémantique", section_d)]:
        print(f"\n=== Section {nom} ===")
        try:
            fn()
        except Exception as e:
            print(f"[ERR] Section {nom} : {e}")
    sortie = GRAPHIQUES_DIR / "metriques_pfe.json"
    sortie.write_text(json.dumps(METRIQUES, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] Métriques sauvegardées : {sortie}")
