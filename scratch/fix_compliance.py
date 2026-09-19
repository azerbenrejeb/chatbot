"""
Script de correction : vide la table indicateurs_esg et teste l'extraction
par mots-clés thématiques sur les rapports déjà uploadés (fichiers JSON).
"""
import sqlite3
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import BASE_DIR, PROCESSED_DIR
from app.compliance_checker import extraire_par_mots_cles, extraire_et_stocker_indicateurs

db_path = BASE_DIR / "data" / "chatbot_history.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Lister les tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("Tables:", tables)

# Vider indicateurs_esg pour forcer ré-extraction
cursor.execute("DELETE FROM indicateurs_esg")
conn.commit()
print("Table indicateurs_esg vidée.")

# Afficher les rapports connus
if "sessions" in tables:
    cursor.execute("SELECT id, rapport_name FROM sessions ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    print("\nSessions récentes:")
    for r in rows:
        print(f"  id={r[0]}, rapport={r[1]}")

conn.close()

# Tester extraction mots-clés sur les JSON existants
print()
json_files = list(Path(str(PROCESSED_DIR)).glob("*_extracted.json"))
print(f"Fichiers JSON disponibles: {[f.name for f in json_files]}")

for jf in json_files[:5]:
    try:
        data = json.loads(jf.read_text(encoding="utf-8"))
        pages = data.get("pages", [])
        text = " ".join(p.get("text", "") for p in pages)
        refs = extraire_par_mots_cles(text)
        print(f"\n  [{jf.stem}]")
        print(f"  Indicateurs détectés: {sorted(refs)}")
        print(f"  Score GRI estimé: {len(refs)}/12 indicateurs = {len(refs)/12*100:.0f}%")
        
        # Stocker en base
        rapport_name = jf.stem.replace("_extracted", "") + ".pdf"
        extraire_et_stocker_indicateurs(rapport_name, text)
    except Exception as e:
        print(f"  {jf.name}: ERREUR - {e}")

print("\nTerminé.")
