# Dictionnaire complet et rigoureux des règles de détection GRI 2021
# Chaque indicateur possède son nom, sa dimension, sa regex de détection explicite,
# ses patterns contextuels rigoureux (avec métriques/unités) et sa description.

GRI_RULES = {

    # ── ENVIRONNEMENTAL ──────────────────────────────────────────────────────

    "GRI 302": {
        "nom": "Énergie",
        "dimension": "Environnemental",
        "code_regex": r"(?:gri\s*302|302-\d)",
        "patterns": [
            r"consommation.{0,15}énergie",
            r"énergie.{0,15}consomm",
            r"intensité énergétique",
            r"mix énergétique",
            r"énergie.{0,25}(?:kwh|mwh|gwh|gj|tep|renouvelable)",
            r"(?:kwh|mwh|gwh|gj).{0,25}énergie",
            r"efficacité énergétique"
        ],
        "keywords": [
            "consommation énergétique", "consommation d'énergie",
            "intensité énergétique", "mix énergétique", "kwh", "mwh", "gwh", "gj", "tep"
        ],
        "requires_value": True,
        "description": "Consommation d'énergie totale (kWh, GJ, MWh)"
    },

    "GRI 303": {
        "nom": "Eau et effluents",
        "dimension": "Environnemental",
        "code_regex": r"(?:gri\s*303|303-\d)",
        "patterns": [
            r"consommation.{0,15}eau",
            r"eau.{0,15}consomm",
            r"prélèvement.{0,10}eau",
            r"stress hydrique",
            r"effluents?",
            r"eau.{0,15}(?:m[³3]|litres?|rejets)",
            r"(?:m[³3]|litres?).{0,15}eau",
            r"gestion.{0,10}eau"
        ],
        "keywords": [
            "consommation d'eau", "prélèvement d'eau", "stress hydrique",
            "effluents", "mètres cubes d'eau", "rejets d'eau"
        ],
        "requires_value": True,
        "description": "Consommation d'eau (m³ prélevés et recyclés)"
    },

    "GRI 305": {
        "nom": "Émissions GES",
        "dimension": "Environnemental",
        "code_regex": r"(?:gri\s*305|305-\d)",
        "patterns": [
            r"scope\s*[123]",
            r"gaz.{0,10}effet.{0,10}serre",
            r"bilan.{0,10}carbone",
            r"bilan.{0,5}ges",
            r"émissions?.{0,10}co[₂2]",
            r"émissions?.{0,10}ges",
            r"tco[₂2]|tco[₂2]e|teq\.?\s*co[₂2]",
            r"neutralité carbone",
            r"empreinte.{0,10}carbone"
        ],
        "keywords": [
            "scope 1", "scope 2", "scope 3", "émissions ges",
            "bilan carbone", "gaz à effet de serre", "tco2", "tco2e"
        ],
        "requires_value": True,
        "description": "Émissions de gaz à effet de serre (tCO₂e Scope 1, 2, 3)"
    },

    "GRI 306": {
        "nom": "Déchets",
        "dimension": "Environnemental",
        "code_regex": r"(?:gri\s*306|306-\d)",
        "patterns": [
            r"déchets?.{0,15}dangereux",
            r"valorisation.{0,15}déchets?",
            r"recyclage.{0,15}déchets?",
            r"taux.{0,10}recyclage",
            r"économie circulaire",
            r"tonnage.{0,10}déchets?",
            r"déchets?.{0,15}(?:tonnes?|kilos?|élimination|filière)"
        ],
        "keywords": [
            "déchets dangereux", "valorisation des déchets", "recyclage des déchets",
            "économie circulaire", "tonnage de déchets", "taux de recyclage"
        ],
        "requires_value": True,
        "description": "Production et valorisation des déchets (tonnes, taux de recyclage)"
    },

    # ── SOCIAL ───────────────────────────────────────────────────────────────

    "GRI 401": {
        "nom": "Emploi",
        "dimension": "Social",
        "code_regex": r"(?:gri\s*401|401-\d)",
        "patterns": [
            r"effectif.{0,15}(?:total|groupe|salarié|moyen|etp)",
            r"nombre.{0,10}(?:d'employés?|de salariés?|de collaborateurs?)",
            r"turnover|taux.{0,10}rotation",
            r"embauches?.{0,10}(?:recrutement|cdi|cdd)",
            r"recrutements?.{0,15}(?:salariés?|collaborateurs?)",
            r"départs?.{0,10}(?:démission|licenciement)"
        ],
        "keywords": [
            "effectif total", "taux de turnover", "taux de rotation",
            "recrutements", "embauches", "départs", "effectif moyen"
        ],
        "requires_value": True,
        "description": "Effectifs totaux, recrutements, départs et turnover"
    },

    "GRI 403": {
        "nom": "Santé et sécurité",
        "dimension": "Social",
        "code_regex": r"(?:gri\s*403|403-\d)",
        "patterns": [
            r"taux.{0,10}fréquence",
            r"taux.{0,10}gravité",
            r"accidents?.{0,15}travail",
            r"santé.{0,10}sécurité",
            r"maladies?.{0,10}professionnelles?",
            r"jours?.{0,10}perdus?.{0,10}accident",
            r"arrêt.{0,10}travail.{0,10}accident"
        ],
        "keywords": [
            "taux de fréquence", "taux de gravité", "accidents du travail",
            "maladies professionnelles", "santé et sécurité au travail", "at/mp"
        ],
        "requires_value": True,
        "description": "Accidents du travail, taux de fréquence/gravité"
    },

    "GRI 404": {
        "nom": "Formation",
        "dimension": "Social",
        "code_regex": r"(?:gri\s*404|404-\d)",
        "patterns": [
            r"heures?.{0,10}formation",
            r"plan.{0,10}formation",
            r"formation.{0,15}(?:salarié|employé|collaborateur)",
            r"salariés?.{0,10}formés?",
            r"budget.{0,10}formation",
            r"développement.{0,15}compétences"
        ],
        "keywords": [
            "heures de formation", "plan de formation", "formation par salarié",
            "salariés formés", "budget formation", "développement des compétences"
        ],
        "requires_value": True,
        "description": "Heures de formation par employé et développement des compétences"
    },

    "GRI 405": {
        "nom": "Diversité et égalité",
        "dimension": "Social",
        "code_regex": r"(?:gri\s*405|405-\d)",
        "patterns": [
            r"égalité.{0,15}(?:femmes?.{0,5}hommes?|professionnelle)",
            r"index.{0,10}égalité",
            r"part.{0,10}femmes?",
            r"femmes?.{0,10}(?:cadres?|direction|management|effectif)",
            r"parité.{0,10}(?:femmes?|genres?)",
            r"handicap.{0,15}(?:salariés?|insertion|emploi)"
        ],
        "keywords": [
            "égalité femmes-hommes", "index égalité", "part des femmes",
            "parité", "femmes cadres", "travailleurs handicapés", "diversité et inclusion"
        ],
        "requires_value": True,
        "description": "% femmes, parité, index d'égalité et inclusion du handicap"
    },

    # ── GOUVERNANCE ──────────────────────────────────────────────────────────

    "GRI 205": {
        "nom": "Anti-corruption",
        "dimension": "Gouvernance",
        "code_regex": r"(?:gri\s*205|205-\d)",
        "patterns": [
            r"anti.?corruption",
            r"lutte.{0,15}corruption",
            r"code.{0,10}conduite",
            r"code.{0,10}éthique",
            r"dispositif.{0,10}alerte",
            r"whistleblowing",
            r"politique.{0,10}anti.?corruption"
        ],
        "keywords": [
            "anti-corruption", "lutte contre la corruption", "code de conduite",
            "code d'éthique", "dispositif d'alerte", "whistleblowing"
        ],
        "requires_value": False,
        "description": "Politique anti-corruption, formations et alertes éthiques"
    },

    "GRI 206": {
        "nom": "Concurrence loyale",
        "dimension": "Gouvernance",
        "code_regex": r"(?:gri\s*206|206-\d)",
        "patterns": [
            r"droit.{0,10}concurrence",
            r"pratiques?.{0,10}anticoncurrentielles?",
            r"entente.{0,10}illicite",
            r"abus.{0,10}position dominante",
            r"litiges?.{0,10}concurrence",
            r"antitrust"
        ],
        "keywords": [
            "droit de la concurrence", "pratiques anticoncurrentielles",
            "entente illicite", "abus de position dominante", "litige concurrence", "antitrust"
        ],
        "requires_value": False,
        "description": "Conformité au droit de la concurrence et contentieux antitrust"
    },

    "GRI 415": {
        "nom": "Contributions politiques",
        "dimension": "Gouvernance",
        "code_regex": r"(?:gri\s*415|415-\d)",
        "patterns": [
            r"contributions?.{0,10}politiques?",
            r"financement.{0,10}(?:politique|partis?)",
            r"dépenses?.{0,10}lobbying",
            r"activités?.{0,10}lobbying",
            r"soutien.{0,10}partis?.{0,5}politiques?"
        ],
        "keywords": [
            "contributions politiques", "financement politique", "dépenses de lobbying",
            "activités de lobbying", "soutien aux partis politiques"
        ],
        "requires_value": False,
        "description": "Déclaration des contributions politiques et du lobbying"
    },

    "GRI 419": {
        "nom": "Conformité socio-économique",
        "dimension": "Gouvernance",
        "code_regex": r"(?:gri\s*419|419-\d)",
        "patterns": [
            r"amendes?.{0,15}(?:non.?conformité|réglementaire|significative)",
            r"sanctions?.{0,15}(?:financières?|non.?conformité|réglementaire)",
            r"non.?conformité.{0,15}(?:lois?|réglementation|légale)",
            r"litiges?.{0,10}réglementaires?"
        ],
        "keywords": [
            "amendes significatives", "sanctions réglementaires",
            "non-conformité socio-économique", "litiges réglementaires"
        ],
        "requires_value": False,
        "description": "Amendes et sanctions pour non-conformité socio-économique"
    }
}

# Seuils de conformité
CONFORMITY_THRESHOLDS = {
    "CONFORME":               80,   # score >= 80% → vert ✅
    "PARTIELLEMENT_CONFORME": 50,   # score >= 50% → orange ⚠️
    "NON_CONFORME":           0     # score < 50%  → rouge ❌
}
