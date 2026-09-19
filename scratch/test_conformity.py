"""Test rapide du module conformité GRI."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.module5_conformity.conformity_checker import check_conformity

# Tester avec la session existante (la session 1 qui est liée à un rapport)
import sqlite3
conn = sqlite3.connect("data/chatbot_history.db")
cur = conn.cursor()
cur.execute("SELECT id, rapport_name, titre FROM sessions ORDER BY id DESC LIMIT 5")
sessions = cur.fetchall()
print("Sessions disponibles :")
for s in sessions:
    print(f"  ID={s[0]}, rapport='{s[1]}', titre='{s[2]}'")

# Trouver une session avec un rapport
for s in sessions:
    if s[1]:  # rapport_name non vide
        session_id = str(s[0])
        print(f"\n--- Test conformité sur session {session_id} (rapport: {s[1]}) ---")
        results = check_conformity(session_id)
        
        global_data = results["Global"]
        print(f"\nScore global : {global_data['score']}% — {global_data['status']['label']}")
        print(f"Indicateurs : {global_data['presents_count']}/{global_data['total_count']}")
        
        for dim in ["Environnemental", "Social", "Gouvernance"]:
            d = results[dim]
            presents = [p['code'] for p in d['presents']]
            manquants = [m['code'] for m in d['manquants']]
            print(f"\n{dim} : {d['score']}% — {d['status']['label']}")
            if presents:
                print(f"  ✅ Présents : {', '.join(presents)}")
            if manquants:
                print(f"  ❌ Manquants : {', '.join(manquants)}")
        
        if results["recommandations"]:
            print(f"\n💡 {len(results['recommandations'])} recommandation(s)")
        break
else:
    print("Aucune session avec rapport trouvée.")

conn.close()
