# Dictionnaire complet des règles de détection GRI 2021
# Chaque indicateur a ses mots-clés et si une valeur numérique est requise

GRI_RULES = {

    # ── ENVIRONNEMENTAL ──────────────────────────────────────────────────────

    "GRI 302": {
        "nom": "Énergie",
        "dimension": "Environnemental",
        "keywords": [
            "énergie", "energy", "kwh", "gj", "mwh", "térajoules",
            "consommation énergétique", "électricité", "gaz naturel",
            "fioul", "consommation d'énergie", "intensité énergétique"
        ],
        "requires_value": True,
        "description": "Consommation d'énergie totale (kWh, GJ, MWh)"
    },

    "GRI 303": {
        "nom": "Eau et effluents",
        "dimension": "Environnemental",
        "keywords": [
            "eau", "water", "m³", "mètres cubes", "prélèvement",
            "hydrique", "consommation d'eau", "rejets", "effluents",
            "recyclage eau", "stress hydrique"
        ],
        "requires_value": True,
        "description": "Consommation d'eau (m³ prélevés et recyclés)"
    },

    "GRI 305": {
        "nom": "Émissions GES",
        "dimension": "Environnemental",
        "keywords": [
            "co₂", "co2", "tco₂e", "tco2e", "ges", "émissions",
            "scope 1", "scope 2", "scope 3", "carbone", "gaz à effet",
            "bilan carbone", "empreinte carbone", "équivalent co2"
        ],
        "requires_value": True,
        "description": "Émissions de gaz à effet de serre (tCO₂e)"
    },

    "GRI 306": {
        "nom": "Déchets",
        "dimension": "Environnemental",
        "keywords": [
            "déchets", "waste", "recyclage", "enfouissement",
            "tonnes métriques", "déchets recyclés", "valorisation",
            "déchets dangereux", "élimination", "compostage"
        ],
        "requires_value": True,
        "description": "Production et gestion des déchets (tonnes)"
    },

    # ── SOCIAL ───────────────────────────────────────────────────────────────

    "GRI 401": {
        "nom": "Emploi",
        "dimension": "Social",
        "keywords": [
            "employés", "salariés", "effectif", "collaborateurs",
            "turnover", "recrutement", "workforce", "headcount",
            "embauches", "départs", "contrats", "emplois créés"
        ],
        "requires_value": True,
        "description": "Effectifs totaux, recrutements, départs"
    },

    "GRI 403": {
        "nom": "Santé et sécurité",
        "dimension": "Social",
        "keywords": [
            "accident", "sécurité", "blessure", "taux de fréquence",
            "décès", "maladie professionnelle", "trir", "taux d'accident",
            "at/mp", "arrêt de travail", "sécurité au travail"
        ],
        "requires_value": True,
        "description": "Accidents du travail, maladies professionnelles"
    },

    "GRI 404": {
        "nom": "Formation",
        "dimension": "Social",
        "keywords": [
            "formation", "training", "heures de formation",
            "développement", "compétences", "e-learning",
            "plan de formation", "heures par employé", "budget formation"
        ],
        "requires_value": True,
        "description": "Heures de formation par employé"
    },

    "GRI 405": {
        "nom": "Diversité et égalité",
        "dimension": "Social",
        "keywords": [
            "femmes", "parité", "diversité", "genre",
            "égalité", "% femmes", "women", "mixité",
            "handicap", "travailleurs handicapés", "écart salarial"
        ],
        "requires_value": True,
        "description": "% femmes, parité, diversité"
    },

    # ── GOUVERNANCE ──────────────────────────────────────────────────────────

    "GRI 205": {
        "nom": "Anti-corruption",
        "dimension": "Gouvernance",
        "keywords": [
            "corruption", "anti-corruption", "éthique",
            "intégrité", "conformité", "lutte contre la corruption",
            "alertes", "whistleblowing", "code de conduite"
        ],
        "requires_value": False,
        "description": "Politique anti-corruption, formations, incidents"
    },

    "GRI 206": {
        "nom": "Concurrence loyale",
        "dimension": "Gouvernance",
        "keywords": [
            "concurrence", "antitrust", "pratiques anticoncurrentielles",
            "entente", "abus de position", "droit de la concurrence"
        ],
        "requires_value": False,
        "description": "Procédures légales liées à la concurrence"
    },

    "GRI 415": {
        "nom": "Contributions politiques",
        "dimension": "Gouvernance",
        "keywords": [
            "contributions politiques", "lobbying", "partis politiques",
            "financement politique", "associations professionnelles"
        ],
        "requires_value": False,
        "description": "Contributions politiques déclarées"
    },

    "GRI 419": {
        "nom": "Conformité socio-économique",
        "dimension": "Gouvernance",
        "keywords": [
            "amendes", "sanctions", "non-conformité",
            "réglementation", "pénalités", "infractions",
            "violations", "litiges réglementaires"
        ],
        "requires_value": False,
        "description": "Amendes et sanctions réglementaires"
    }
}

# Seuils de conformité
CONFORMITY_THRESHOLDS = {
    "CONFORME":               80,   # score >= 80% → vert ✅
    "PARTIELLEMENT_CONFORME": 50,   # score >= 50% → orange ⚠️
    "NON_CONFORME":           0     # score < 50%  → rouge ❌
}
