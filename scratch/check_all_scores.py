import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import sqlite3
from app.compliance_checker import extraire_references_uniques, calculer_score_conformite

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chatbot_history.db"
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()
c.execute('SELECT DISTINCT rapport_name FROM indicateurs_esg WHERE rapport_name IS NOT NULL')
reports = [r[0] for r in c.fetchall() if r]

for r in reports:
    refs = extraire_references_uniques(session_id=None, rapport_name=r)
    sc = calculer_score_conformite(refs)
    print(f"{r} -> GRI: {sc['score_global_gri']}% | ESRS: {sc['score_global_esrs']}% | {len(refs)} refs: {sorted(refs)}")

conn.close()
