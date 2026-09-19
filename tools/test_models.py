"""
Outil interactif de test pour évaluer les modèles NLP en temps réel.
Permet d'entrer une phrase et d'obtenir en direct les classifications (E/S/G) 
et les entités extraites (NER).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config import MODELS_DIR

# Importation sécurisée des modèles
from modules.module2_nlp import ml1_baseline_tfidf
from modules.module2_nlp import ml1_random_forest
from modules.module2_nlp import ml2_ner_spacy

# Exemples par défaut pour le test
EXEMPLES = [
    "En 2023, nous avons réduit nos émissions de gaz à effet de serre (GES) de 15 % par rapport à 2022.",
    "Le groupe emploie 45 200 collaborateurs dont 32% de femmes à la fin de l'exercice 2024.",
    "Le conseil d'administration, réuni le 15 décembre, compte 12 administrateurs dont 4 indépendants pour assurer la conformité aux exigences de gouvernance.",
    "Conformément à la norme GRI 305-1, le scope 1 direct s'élève à 12 500 tonnes de CO2."
]


def tester_phrase(phrase):
    """Exécute la prédiction de classification et NER sur une phrase donnée."""
    print("\n" + "-"*60)
    print(f"📝 Phrase testée : \"{phrase}\"")
    print("-"*60)
    
    # 1. Classification
    try:
        class_tfidf = ml1_baseline_tfidf.predire(phrase)
        print(f"🎯 Classification TF-IDF Baseline   : {class_tfidf}")
    except Exception as e:
        print(f"⚠️ Erreur classification TF-IDF : {e}")

    try:
        class_rf = ml1_random_forest.predire(phrase)
        print(f"🎯 Classification Random Forest    : {class_rf}")
    except Exception as e:
        print(f"⚠️ Erreur classification Random Forest : {e}")

    # 2. NER (Extraction d'Entités)
    try:
        entites = ml2_ner_spacy.extraire_entites(phrase)
        print("\n🔍 Entités RSE détectées (spaCy NER) :")
        if not entites:
            print("   (Aucune entité détectée)")
        else:
            emojis = {
                "VALEUR": "🔢",
                "UNITE": "📏",
                "ANNEE": "📅",
                "TENDANCE": "📈",
                "REFERENCE_GRI": "📋"
            }
            for ent in entites:
                label = ent["label"]
                emoji = emojis.get(label, "⬜")
                print(f"   {emoji} [{label}] : \"{ent['texte']}\" (positions: {ent['start']}-{ent['end']})")
    except Exception as e:
        print(f"⚠️ Erreur extraction NER : {e}")
    print("-"*60)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test interactif ou automatique des modèles NLP.")
    parser.add_argument("--no-interactive", action="store_true", help="Exécuter uniquement les exemples et quitter.")
    args = parser.parse_args()

    print("="*60)
    print("🧪 CONSOLE DE TEST DES MODÈLES NLP ESG")
    print("="*60)
    
    print("\n--- TEST DES PHRASES D'EXEMPLE TYPES ---")
    for exemple in EXEMPLES:
        tester_phrase(exemple)
        
    if args.no_interactive:
        print("\n[OK] Mode non-interactif. Fin du script.")
        return

    print("\n💡 À vous de jouer !")
    print("Saisissez vos propres phrases ESG pour tester les modèles (ou tapez 'exit' pour quitter).")
    
    while True:
        try:
            phrase = input("\n✍️ Entrez une phrase ESG : ").strip()
            if phrase.lower() in ("exit", "quit", "q", "sortir"):
                print("\n👋 Fin de la session de test. À bientôt !")
                break
            if not phrase:
                continue
            tester_phrase(phrase)
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Fin de la session de test. À bientôt !")
            break


if __name__ == "__main__":
    main()
