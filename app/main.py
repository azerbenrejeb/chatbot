"""
BACKEND — FastAPI Principal.
Orchestre le pipeline complet du Chatbot ESG per CDC.
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import shutil
import sys
import torch
import torchvision.transforms as transforms
from PIL import Image

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.config import (
    RAW_PDF_DIR, PROCESSED_DIR, MODELS_DIR, ML_CLASSES,
    create_directories, FASTAPI_HOST, FASTAPI_PORT
)
from extraction.pdf_extractor import extraire_texte, extraire_tableaux
from extraction.text_preprocessor import segmenter_paragraphes
from extraction.pdf_to_images import convert_pdf_to_images
from modules.module1_cnn.cnn_classifier import get_model as get_cnn_model
from modules.module2_nlp.ml1_camembert import predire as predire_classe
from modules.module2_nlp.ml1_random_forest import predire as predire_rf
from modules.module3_llm_rag.vector_store import stocker_paragraphes
from modules.module3_llm_rag.rag_engine import interroger_rapports

# Initialisation
create_directories()

app = FastAPI(title="ESG Chatbot API", description="API Backend pour le Chatbot ESG Intelligent")

# Activer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers.conformity import router as conformity_router
app.include_router(conformity_router)

from typing import Optional

class Question(BaseModel):
    texte: str
    rapport: Optional[str] = None
    filtre_label: Optional[str] = None
    session_id: Optional[int] = None


# --- Chargement des modèles avec fallback gracieux ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Modèle CNN
cnn_model_path = MODELS_DIR / "cnn_resnet50_esg.pth"
cnn_model = None
if cnn_model_path.exists():
    try:
        cnn_model = get_cnn_model(num_classes=2)
        cnn_model.load_state_dict(torch.load(str(cnn_model_path), map_location=device, weights_only=True))
        cnn_model = cnn_model.to(device)
        cnn_model.eval()
        print("[OK] Modèle CNN chargé avec succès.")
    except Exception as e:
        print(f"[WARN] Erreur chargement CNN: {e}. Fallback vers extraction complète.")
else:
    print("[WARN] Modèle CNN non trouvé. Fallback vers extraction complète.")

# Modèles CamemBERT & Random Forest
ml_model_path = MODELS_DIR / "camembert_ml.pth"
rf_model_path = MODELS_DIR / "rf_model.pkl"
if ml_model_path.exists():
    print("[OK] Modèle CamemBERT classification disponible pour inference.")
elif rf_model_path.exists():
    print("[OK] Modèle Random Forest disponible comme fallback pour classification.")
else:
    print("[WARN] Modèles CamemBERT et Random Forest non trouvés. Fallback vers classification par mots-clés.")


# --- Pipeline Helper ---
def filtrer_pages_cnn(pdf_path):
    """Convertit le PDF en images et utilise le CNN pour filtrer les pages ESG."""
    temp_img_dir = PROCESSED_DIR / "temp_images"
    temp_img_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Convertir en images
    convert_pdf_to_images(pdf_path, temp_img_dir)
    
    image_paths = sorted(list(temp_img_dir.glob(f"{pdf_path.stem}_page_*.jpg")))
    
    if not image_paths:
        return []

    # Si le modèle CNN n'est pas encore entraîné, on prend toutes les pages par défaut
    if cnn_model is None:
        print("[INFO] CNN non disponible, traitement de toutes les pages.")
        pages_esg = list(range(len(image_paths)))
        return pages_esg

    # Transformation d'image pour ResNet-50
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    pages_esg = []
    for img_path in image_paths:
        try:
            # Récupérer l'index de page depuis le nom (ex: name_page_3.jpg -> index 2)
            page_num = int(img_path.stem.split("_page_")[-1]) - 1
            
            img = Image.open(img_path).convert('RGB')
            tensor = transform(img).unsqueeze(0).to(device)
            
            with torch.no_grad():
                outputs = cnn_model(tensor)
                pred = torch.argmax(outputs, dim=1).item()
                
            if pred == 0:  # ESG (Classe 0)
                pages_esg.append(page_num)
        except Exception as e:
            print(f"[ERR] Erreur classification page {img_path.name}: {e}")

    print(f"[OK] CNN a filtré {len(pages_esg)} pages ESG sur {len(image_paths)} au total.")
    return pages_esg


def extraire_texte_ocr(pdf_path, pages_esg, temp_img_dir, max_pages=8):
    """
    Extrait le texte des pages ESG en utilisant EasyOCR si pdfplumber n'a rien extrait.
    Optimisé pour la vitesse :
      - Limité à 8 pages max
      - Images redimensionnées à 1200px de large
      - detail=0 pour extraction texte brut uniquement
    """
    import time as _time
    pages_to_ocr = pages_esg[:max_pages]
    print(f"[OCR] Lancement OCR EasyOCR rapide pour {len(pages_to_ocr)} pages sur {len(pages_esg)}...")
    t_start = _time.time()
    try:
        import easyocr
        import torch
        from PIL import Image
        use_gpu = torch.cuda.is_available()
        reader = easyocr.Reader(['fr'], gpu=use_gpu)
        
        textes = []
        for page_num in pages_to_ocr:
            image_name = f"{pdf_path.stem}_page_{page_num + 1}.jpg"
            image_path = temp_img_dir / image_name
            
            if image_path.exists():
                t_page = _time.time()
                # Redimensionner l'image à 1200px de large pour accélérer l'OCR
                try:
                    img = Image.open(image_path)
                    max_width = 1200
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_size = (max_width, int(img.height * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                        resized_path = temp_img_dir / f"resized_{image_name}"
                        img.save(str(resized_path), quality=85)
                        ocr_input = str(resized_path)
                    else:
                        ocr_input = str(image_path)
                except Exception:
                    ocr_input = str(image_path)
                
                # detail=0 retourne directement la liste des chaînes de texte (plus rapide)
                results = reader.readtext(ocr_input, detail=0, paragraph=True)
                page_text = " ".join(results).strip()
                elapsed = _time.time() - t_page
                print(f"[OCR] Page {page_num + 1} → {len(page_text)} car. en {elapsed:.1f}s")
                if len(page_text) > 0:
                    textes.append({
                        'page': page_num + 1,
                        'texte': page_text
                    })
        
        total_time = _time.time() - t_start
        print(f"[OCR] Terminé : {len(textes)} pages récupérées en {total_time:.1f}s ({total_time/max(len(pages_to_ocr),1):.1f}s/page)")
        return textes
    except Exception as e:
        print(f"[WARN] Erreur lors de l'OCR EasyOCR : {e}")
        return []


@app.post("/upload-rapport")
async def upload_rapport(file: UploadFile = File(...)):
    """Pipeline complet d'indexation d'un rapport PDF."""
    temp_img_dir = PROCESSED_DIR / "temp_images"
    try:
        # 1. Sauvegarder le PDF
        pdf_path = RAW_PDF_DIR / file.filename
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[FASTAPI] Fichier sauvegardé : {pdf_path}")

        # 1.5 Vérifier si le rapport a déjà été traité (cache JSON)
        rapport_stem = pdf_path.stem
        json_path = PROCESSED_DIR / f"{rapport_stem}_extracted.json"
        if json_path.exists():
            print(f"[FASTAPI] Rapport '{file.filename}' déjà traité. Chargement depuis le cache JSON...")
            try:
                import json
                with open(json_path, 'r', encoding='utf-8') as f:
                    extracted_data = json.load(f)
                pages = extracted_data.get('pages', [])
                total_chars = sum(len(p.get('text', '')) for p in pages if p.get('text'))
                
                # S'assurer que les indicateurs sont bien extraits et stockés en base
                full_text = "\n".join([p.get('text', '') for p in pages if p.get('text')])
                if full_text:
                    from app.compliance_checker import extraire_et_stocker_indicateurs
                    extraire_et_stocker_indicateurs(file.filename, full_text)
                
                return {
                    "message": f"Rapport '{file.filename}' chargé avec succès depuis le cache",
                    "pages_pertinentes": len(pages),
                    "paragraphes_indexes": len(pages),
                    "ocr_used": "easyocr" in extracted_data.get('metadata', {}).get('extracteur', ''),
                    "has_text": total_chars > 0
                }
            except Exception as e:
                print(f"[WARN] Erreur chargement depuis le cache JSON : {e}. Relancement du pipeline complet...")

        # 2. CNN filtre les pages ESG
        pages_esg = filtrer_pages_cnn(pdf_path)
        
        if not pages_esg:
            return {"message": "Aucune page ESG détectée par le CNN.", "pages_traitees": 0}

        # 3. Extraire le texte des pages ESG
        pages_texte = extraire_texte(pdf_path, pages_esg)
        
        # 3.5 Fallback OCR si le texte extrait est vide (PDF scanné)
        total_chars = sum(len(pt['texte']) for pt in pages_texte if pt.get('texte'))
        is_ocr_used = False
        if total_chars < 100:
            print(f"[INFO] Texte extrait standard insuffisant ({total_chars} caract.). Tentative d'OCR...")
            ocr_textes = extraire_texte_ocr(pdf_path, pages_esg, temp_img_dir)
            if ocr_textes:
                pages_texte = ocr_textes
                total_chars = sum(len(pt['texte']) for pt in pages_texte if pt.get('texte'))
                is_ocr_used = True
        
        # 4. Extraire aussi les tableaux des pages ESG
        tableaux_texte = extraire_tableaux(pdf_path, pages_esg)

        # 4.4 Sauvegarder le JSON extrait pour le conformité checker
        try:
            import json
            rapport_stem = pdf_path.stem
            json_path = PROCESSED_DIR / f"{rapport_stem}_extracted.json"
            pages_json = []
            for pt in pages_texte:
                text_content = pt.get('texte', '')
                pages_json.append({
                    "page_number": pt.get('page', 0),
                    "text": text_content,
                    "tables": [],
                    "has_text": bool(text_content),
                    "char_count": len(text_content)
                })
            extracted_data = {
                "metadata": {
                    "nom_fichier": file.filename,
                    "nombre_pages": len(pages_texte),
                    "chemin": str(pdf_path),
                    "extracteur": "pdfplumber + easyocr (upload pipeline)" if is_ocr_used else "pdfplumber (upload pipeline)"
                },
                "pages": pages_json
            }
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            print(f"[OK] JSON extrait sauvegardé pour conformité : {json_path}")
        except Exception as e:
            print(f"[WARN] Erreur lors de la création du JSON extrait : {e}")

        # 4.5 Extraire et stocker les indicateurs ESG via spaCy NER
        if pages_texte:
            try:
                full_text = "\n".join([pt['texte'] for pt in pages_texte if pt.get('texte')])
                from app.compliance_checker import extraire_et_stocker_indicateurs
                extraire_et_stocker_indicateurs(file.filename, full_text)
            except Exception as e:
                print(f"[WARN] Erreur lors de l'extraction/stockage des indicateurs : {e}")

        # 5. Segmenter et classifier les paragraphes
        paragraphes_a_stocker = []
        labels_a_stocker = []
        metadonnees_a_stocker = []

        # Traiter les paragraphes normaux
        for pt in pages_texte:
            paras = segmenter_paragraphes(pt['texte'])
            for p in paras:
                # Classification CamemBERT ou Random Forest
                label = None
                if ml_model_path.exists():
                    label = predire_classe(p)
                elif rf_model_path.exists():
                    try:
                        label = predire_rf(p)
                    except Exception as e:
                        print(f"[WARN] Erreur prediction Random Forest : {e}")
                
                if not label:
                    # Fallback simple si modèles non disponibles ou en échec
                    if any(w in p.lower() for w in ["écol", "carbone", "co2", "climat", "vert", "environnement"]):
                        label = "Environnemental"
                    elif any(w in p.lower() for w in ["social", "employé", "femme", "diversité", "salar", "sécurité"]):
                        label = "Social"
                    else:
                        label = "Gouvernance"

                paragraphes_a_stocker.append(p)
                labels_a_stocker.append(label)
                metadonnees_a_stocker.append({
                    'page': pt['page'],
                    'rapport': file.filename,
                    'annee': "2024"  # Année par défaut ou extraite du nom
                })

        # Traiter les tableaux comme des paragraphes Gouvernance/Environnemental
        for tab in tableaux_texte:
            paragraphes_a_stocker.append(tab['tableau'])
            labels_a_stocker.append("Gouvernance")  # Généralement gouvernance/chiffres
            metadonnees_a_stocker.append({
                'page': tab['page'],
                'rapport': file.filename,
                'annee': "2024"
            })

        # 6. Stocker dans ChromaDB
        if paragraphes_a_stocker:
            stocker_paragraphes(paragraphes_a_stocker, labels_a_stocker, metadonnees_a_stocker)

        return {
            "message": f"Rapport '{file.filename}' traité avec succès",
            "pages_pertinentes": len(pages_esg),
            "paragraphes_indexes": len(paragraphes_a_stocker),
            "ocr_used": is_ocr_used,
            "has_text": total_chars > 0
        }

    except Exception as e:
        print(f"[ERR] Erreur lors de l'upload/traitement : {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Nettoyer les images temporaires à la fin
        if temp_img_dir.exists():
            try:
                shutil.rmtree(temp_img_dir)
                print("[OK] Nettoyage des images temporaires effectué.")
            except Exception as e:
                print(f"[WARN] Erreur nettoyage dossier temporaire : {e}")


@app.post("/question")
async def poser_question(q: Question):
    """Répond à une question en utilisant ChromaDB et Mistral 7B."""
    try:
        res = interroger_rapports(
            q.texte, 
            filtre_label=q.filtre_label, 
            filtre_rapport=q.rapport, 
            session_id=q.session_id
        )
        return res
    except Exception as e:
        print(f"[ERR] Erreur lors du traitement de la question : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def obtenir_stats():
    """Statistiques sur la base vectorielle."""
    from modules.module3_llm_rag.vector_store import get_stats
    return get_stats()


# ═══════════════════════════════════════════════════════════════════════
# NOUVEAUX ENDPOINTS — 5 Fonctionnalités ESG Additionnelles
# ═══════════════════════════════════════════════════════════════════════

# Cache en mémoire pour les résumés automatiques (évite les appels Mistral répétés)
_resume_cache = {}


class ResumeRequest(BaseModel):
    session_id: str


class CompareRequest(BaseModel):
    session_id_a: str
    session_id_b: str


@app.post("/rapport/resume")
async def obtenir_resume(req: ResumeRequest):
    """
    Génère (ou récupère du cache) un résumé automatique du rapport
    lié à la session donnée. Appelle Mistral via Ollama.
    """
    sid = req.session_id
    
    # Vérifier le cache en mémoire
    if sid in _resume_cache:
        return {"resume": _resume_cache[sid], "cached": True}
    
    try:
        from app.rapport_summary import generer_resume_rapport
        resume = generer_resume_rapport(int(sid))
        # Stocker dans le cache pour réutilisation immédiate
        _resume_cache[sid] = resume
        return {"resume": resume, "cached": False}
    except Exception as e:
        print(f"[ERR] Erreur lors de la génération du résumé : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rapport/comparer")
async def comparer_deux_rapports(req: CompareRequest):
    """
    Compare deux rapports ESG identifiés par leurs session_id.
    Retourne les indicateurs communs alignés, les scores et une synthèse rédigée.
    """
    try:
        from app.rapport_comparateur import comparer_rapports, generer_synthese_comparaison
        result = comparer_rapports(int(req.session_id_a), int(req.session_id_b))
        synthese = generer_synthese_comparaison(result)
        result["synthese"] = synthese
        return result
    except Exception as e:
        print(f"[ERR] Erreur lors de la comparaison de rapports : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rapport/tendances")
async def obtenir_tendances(session_id: str):
    """
    Détecte les tendances temporelles pour les indicateurs ayant
    des données sur plusieurs années dans le rapport de la session.
    """
    try:
        from app.tendances_detector import detecter_tendances
        tendances = detecter_tendances(int(session_id))
        return {"tendances": tendances, "count": len(tendances)}
    except Exception as e:
        print(f"[ERR] Erreur lors de la détection des tendances : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rapport/recommandations")
async def obtenir_recommandations(session_id: str):
    """
    Génère les 3 recommandations prioritaires via Mistral
    basées sur les indicateurs GRI manquants.
    """
    try:
        from app.recommandations_generator import generer_recommandations
        recos = generer_recommandations(int(session_id))
        return {"recommandations": recos, "count": len(recos)}
    except Exception as e:
        print(f"[ERR] Erreur lors de la génération des recommandations : {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=FASTAPI_HOST, port=FASTAPI_PORT, reload=True)

