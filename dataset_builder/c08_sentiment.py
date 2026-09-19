# -*- coding: utf-8 -*-
"""
Catégorie 8 : sentiment (25 items)
Distribution : 8 index 0, 9 index 1, 8 index 2
"""

SENTIMENT_ITEMS = [
    # Index 0 (8 items)
    {
        "contexte": "Avis client : 'Le serveur a mis 45 minutes pour apporter une carafe d'eau tiède, une vraie prouesse d'efficacité !'",
        "question": "Quelle est la tonalité réelle de ce commentaire ?",
        "options": ["Très négatif et teinté d'une vive ironie", "Élogieux et enthousiaste sur le service", "Purement descriptif et neutre"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Message interne d'un chef de projet : 'Bravo pour la coupure de la base un vendredi à 18h, le week-end commence bien.'",
        "question": "Quel sentiment réel est exprimé par l'auteur ?",
        "options": ["Une forte exaspération ironique", "Une sincère reconnaissance", "Une totale satisfaction"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Avis sur un smartphone : 'La batterie tient à peine deux heures en veille, quel exploit technologique remarquable !'",
        "question": "Quelle est l'opinion réelle du client sur l'appareil ?",
        "options": ["Une grande insatisfaction exprimée avec sarcasme", "Une admiration sincère pour l'autonomie", "Un avis technique sans jugement"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Avis sur un hôtel : 'Une chambre avec vue imprenable sur un mur de briques à deux mètres, un vrai rêve de vacances.'",
        "question": "Quel est le ressenti réel du voyageur ?",
        "options": ["Une déception amère tournée en dérision", "Un émerveillement authentique", "Une recommandation chaleureuse"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Message d'un conducteur bloqué : 'Merci pour les travaux surprises non signalés à l'heure de pointe, un pur bonheur !'",
        "question": "Quelle émotion sous-tend ce message ?",
        "options": ["Un agacement profond formulé par antiphrase", "Une profonde gratitude envers les ouvriers", "Un calme serein et réjoui"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Avis sur un SAV : 'Trois semaines d'attente pour s'entendre dire de redémarrer la box, quel niveau de compétence éblouissant !'",
        "question": "Que pense réellement le client du service ?",
        "options": ["Il déplore une incompétence flagrante par sarcasme", "Il félicite sincèrement le technicien", "Il est indifférent au délai"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Avis d'un passager de train : 'Une heure de retard sans climatisation par 35°C, quel voyage idyllique !'",
        "question": "Quel est l'état d'esprit réel du voyageur ?",
        "options": ["Une vive colère manifestée par ironie", "Un ravissement total pour le trajet", "Un contentement paisible"],
        "index_correct": 0,
        "categorie": "sentiment"
    },
    {
        "contexte": "Avis sur une application : 'Elle se ferme toute seule à chaque ouverture, vraiment une merveille de stabilité !'",
        "question": "Que dénonce l'utilisateur dans ce message ?",
        "options": ["L'extrême instabilité de l'application avec ironie", "La grande fluidité du logiciel", "Le design graphique réussi"],
        "index_correct": 0,
        "categorie": "sentiment"
    },

    # Index 1 (9 items)
    {
        "contexte": "Commentaire d'un critique littéraire : 'Ce nouvel ouvrage n'est pas sans mérite et captive par sa rigueur.'",
        "question": "Quel sentiment général se dégage de cette appréciation ?",
        "options": ["Hostile et très défavorable", "Globalement favorable et appréciatif", "Totalement indifférent et froid"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Critique de spectacle : 'Sans être une merveille inoubliable, la pièce offre un moment de divertissement honorable.'",
        "question": "Quelle est la polarité globale de ce retour critique ?",
        "options": ["Franchement destructrice et négative", "Modérément positive avec un jugement nuancé", "Un éloge sans réserve"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Commentaire d'un enseignant : 'Le raisonnement n'est pas dénué d'intérêt malgré quelques erreurs de calcul.'",
        "question": "Quel jugement l'enseignant porte-t-il sur la démarche de l'élève ?",
        "options": ["Un rejet total du devoir", "Une appréciation encourageante et bienveillante", "Une note parfaite sans réserve"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Retour d'un testeur : 'L'application n'est pas exempte de défauts mineurs, mais la fluidité est très appréciable.'",
        "question": "Quelle est l'impression prédominante du testeur ?",
        "options": ["Un constat d'échec total", "Un avis favorable soulignant les atouts", "Un rejet complet du produit"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Critique de cinéma : 'Ce film d'auteur ne manque pas de charme et séduit par sa bande-son soignée.'",
        "question": "Quel est le positionnement du critique envers le long-métrage ?",
        "options": ["Une hostilité farouche", "Une appréciation positive et douce", "Une condamnation sans appel"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Évaluation d'un candidat : 'Le profil n'est pas inintéressant et présente des compétences solides pour le poste.'",
        "question": "Quelle est la recommandation implicite du recruteur ?",
        "options": ["Un refus catégorique de la candidature", "Un avis favorable pour continuer le recrutement", "Une réorientation immédiate"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Critique culinaire : 'Le plat n'est pas sans saveur et séduit par son équilibre d'épices bien dosé.'",
        "question": "Quel jugement le critique porte-t-il sur la recette ?",
        "options": ["Une détestation de l'assaisonnement", "Une opinion positive et gourmande", "Un rejet complet de la cuisine"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Rapport d'audit qualité : 'L'organisation n'est pas défaillante et respecte l'essentiel des critères requis.'",
        "question": "Quelle conclusion l'auditeur tire-t-il de sa visite ?",
        "options": ["Une fermeture administrative urgente", "Un constat globalement satisfaisant et rassurant", "Une sanction financière lourde"],
        "index_correct": 1,
        "categorie": "sentiment"
    },
    {
        "contexte": "Avis sur un cours en ligne : 'Ce module n'est pas inutile et apporte des éclairages pertinents.'",
        "question": "Quelle est la valeur perçue de cette formation ?",
        "options": ["Une perte de temps complète", "Une ressource utile et constructive", "Un contenu erroné et dangereux"],
        "index_correct": 1,
        "categorie": "sentiment"
    },

    # Index 2 (8 items)
    {
        "contexte": "Déclaration d'un communiqué financier : 'Le groupe a enregistré un chiffre d'affaires stable de 12 millions d'euros au T1.'",
        "question": "Quel est le ton dominant de cette publication ?",
        "options": ["Extrêmement alarmiste et pessimiste", "Triomphant et euphorique", "Factuel, objectif et neutre"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Rapport météo : 'Une dépression traversera le nord du pays demain avec des vents de 60 km/h.'",
        "question": "Quelle est la nature du sentiment transmis par ce bulletin ?",
        "options": ["Une panique face aux intempéries", "Une joie immense", "Une information technique et neutre"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Notice d'utilisation : 'Brancher le câble d'alimentation sur une prise murale standard de 230 volts.'",
        "question": "Quelle émotion ou polarité est véhiculée par cette consigne ?",
        "options": ["Une critique de l'installation", "Un enthousiasme commercial", "Une neutralité fonctionnelle absolue"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Procès-verbal de réunion : 'L'assemblée a voté à l'unanimité le renouvellement du mandat du trésorier pour 2 ans.'",
        "question": "Quelle est la tonalité rédactionnelle de cet extrait ?",
        "options": ["Une ironie envers le trésorier", "Une contestation virulente", "Une restitution administrative neutre"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Article encyclopédique : 'La photosynthèse est le processus bioénergétique permettant la synthèse de matière organique.'",
        "question": "Quel est le ton adopté par cet extrait ?",
        "options": ["Un éloge passionné", "Une satire de la nature", "Un exposé scientifique rigoureusement neutre"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Tableau de bord logistique : '150 colis ont été expédiés ce jour depuis l'entrepôt de Lyon.'",
        "question": "Quelle est la polarité de cette métrique opérationnelle ?",
        "options": ["Une vive inquiétude", "Une célébration triomphale", "Un compte-rendu d'activité purement factuel"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Bilan comptable : 'L'actif circulant s'élève à 450 000 euros au 31 décembre de l'exercice.'",
        "question": "Quel ton caractérise cette mention comptable ?",
        "options": ["Une fierté débordante", "Un dépit financier", "Une mention descriptive et neutre"],
        "index_correct": 2,
        "categorie": "sentiment"
    },
    {
        "contexte": "Fiche horaire de bus : 'Le premier départ de la ligne A s'effectue à 05h30 du lundi au samedi.'",
        "question": "Quelle est la tonalité du document ?",
        "options": ["Une critique des horaires", "Une publicité enjouée", "Une information horaire factuelle et neutre"],
        "index_correct": 2,
        "categorie": "sentiment"
    }
]
