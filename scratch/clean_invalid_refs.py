"""
Script de nettoyage des references_gri invalides dans indicateurs_esg.
"""
import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chatbot_history.db"
conn = sqlite3.connect(str(DB_PATH))
c = conn.cursor()

# Récupérer toutes les références
c.execute("SELECT DISTINCT reference_gri FROM indicateurs_esg")
refs = [row[0] for row in c.fetchall()]

# Identifier les invalides (ne commencent pas par GRI suivi d'un espace+chiffre, ou format ESRS Xn-n)
valides = set()
invalides = set()
for ref in refs:
    if ref and (
        re.match(r'^GRI \d{3}$', ref) or
        re.match(r'^[ESG]\d+-\d+$', ref)
    ):
        valides.add(ref)
    else:
        invalides.add(ref)

print(f"Références valides ({len(valides)}): {sorted(valides)}")
print(f"Références invalides ({len(invalides)}): {sorted(invalides)[:20]}")

# Supprimer les invalides
if invalides:
    for ref in invalides:
        c.execute("DELETE FROM indicateurs_esg WHERE reference_gri = ?", (ref,))
    conn.commit()
    print(f"[OK] {len(invalides)} références invalides supprimées.")

c.execute("SELECT COUNT(*) FROM indicateurs_esg")
print(f"[OK] Rows restantes: {c.fetchone()[0]}")
conn.close()
