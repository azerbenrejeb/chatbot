from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from modules.module5_conformity.conformity_checker import check_conformity
from modules.module5_conformity.conformity_report import generate_conformity_pdf

router = APIRouter(prefix="/conformity", tags=["Conformité GRI"])

class ConformityRequest(BaseModel):
    session_id: str

@router.post("/check")
async def check_gri_conformity(request: ConformityRequest):
    """
    Vérifie la conformité GRI d'un rapport analysé.
    Utilise les données déjà extraites par les modules 1 et 2.
    """
    try:
        results = check_conformity(request.session_id)
        # Ajouter le score ESG global sur 100 (pondéré E:40, S:35, G:25)
        from app.compliance_checker import calculer_score_esg_global_100
        results["score_esg_100"] = calculer_score_esg_global_100(results)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{session_id}")
async def download_conformity_report(session_id: str):
    """
    Télécharge le rapport PDF de conformité GRI.
    """
    try:
        results = check_conformity(session_id)
        pdf_path = generate_conformity_pdf(session_id, results)
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"Rapport_Conformite_GRI_{session_id}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
