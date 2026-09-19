"""
MODULE 4 — Gestionnaire d'upload et de traitement des rapports PDF.
Encapsule la logique d'upload côté Streamlit : validation du fichier,
sauvegarde locale et appel au backend FastAPI pour lancer le pipeline complet.
"""
import requests
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.config import RAW_PDF_DIR, FASTAPI_HOST, FASTAPI_PORT


# URL par défaut du backend FastAPI
fastapi_host_client = FASTAPI_HOST if FASTAPI_HOST != "0.0.0.0" else "127.0.0.1"
FASTAPI_URL = f"http://{fastapi_host_client}:{FASTAPI_PORT}"


def valider_pdf(uploaded_file):
    """
    Vérifie que le fichier uploadé est un PDF valide.
    :param uploaded_file: Objet UploadedFile de Streamlit.
    :return: Tuple (is_valid: bool, message: str).
    """
    if uploaded_file is None:
        return False, "Aucun fichier sélectionné."

    # Vérification de l'extension
    if not uploaded_file.name.lower().endswith('.pdf'):
        return False, "Le fichier doit être au format PDF."

    # Vérification de la taille (max 100 Mo)
    MAX_SIZE_MB = 100
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_SIZE_MB:
        return False, f"Le fichier est trop volumineux ({file_size_mb:.1f} Mo). Maximum : {MAX_SIZE_MB} Mo."

    # Vérification de l'en-tête magique PDF (%PDF-)
    uploaded_file.seek(0)
    header = uploaded_file.read(5)
    uploaded_file.seek(0)  # Remettre le curseur au début
    if header != b'%PDF-':
        return False, "Le fichier ne semble pas être un PDF valide (en-tête magique manquant)."

    return True, f"Fichier valide : {uploaded_file.name} ({file_size_mb:.1f} Mo)"


def sauvegarder_pdf_local(uploaded_file):
    """
    Sauvegarde le fichier PDF uploadé dans le dossier des rapports bruts.
    :param uploaded_file: Objet UploadedFile de Streamlit.
    :return: Chemin du fichier sauvegardé (Path).
    """
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = RAW_PDF_DIR / uploaded_file.name

    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    print(f"[OK] PDF sauvegardé localement : {pdf_path}")
    return pdf_path


def envoyer_au_backend(uploaded_file, api_url=None):
    """
    Envoie le PDF au backend FastAPI pour lancer le pipeline complet
    (CNN → Extraction → Classification → Indexation ChromaDB).
    :param uploaded_file: Objet UploadedFile de Streamlit.
    :param api_url: URL de l'API FastAPI (optionnel).
    :return: Dictionnaire de résultats du pipeline.
    """
    if api_url is None:
        api_url = FASTAPI_URL

    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post(f"{api_url}/upload-rapport", files=files, timeout=600)

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Erreur API ({response.status_code}): {response.text}"}
    except requests.ConnectionError:
        return {"success": False, "error": "Impossible de se connecter au backend FastAPI. Vérifiez qu'il est lancé."}
    except requests.Timeout:
        return {"success": False, "error": "Le traitement a pris trop de temps (timeout > 10 min)."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def lister_rapports_charges():
    """Liste les rapports PDF déjà présents dans le dossier brut."""
    RAW_PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(RAW_PDF_DIR.glob("*.pdf"))
    return [{"nom": p.name, "taille_mo": p.stat().st_size / (1024*1024)} for p in pdfs if p.stat().st_size > 0]


if __name__ == "__main__":
    rapports = lister_rapports_charges()
    print(f"[OK] {len(rapports)} rapports PDF dans le dossier brut :")
    for r in rapports:
        print(f"  - {r['nom']} ({r['taille_mo']:.1f} Mo)")
