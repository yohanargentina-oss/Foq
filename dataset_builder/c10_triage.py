# -*- coding: utf-8 -*-
"""
Catégorie 10 : triage (25 items)
Distribution : 8 index 0, 8 index 1, 9 index 2
"""

TRIAGE_ITEMS = [
    # Index 0 (8 items)
    {
        "contexte": "Un homme de 60 ans ressent une vive douleur thoracique irradiant dans la mâchoire avec sueurs froides depuis 15 min.",
        "question": "Quelle décision de régulation médicale immédiate s'impose ?",
        "options": ["Envoi immédiat du SAMU en urgence vitale", "Rendez-vous médical sous 48 heures", "Surveillance calme à domicile"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Le serveur de base de données de production d'un site e-commerce mondial ne répond plus le jour du lancement des soldes.",
        "question": "Quel niveau de sévérité informatique (ITIL) doit être déclenché ?",
        "options": ["Incident majeur P1 (astreinte immédiate)", "Ticket mineur P4 pour la semaine suivante", "Demande d'évolution fonctionnelle P3"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Une personne est retrouvée inconsciente au sol, ne réagit à aucun stimulus et ne respire plus du tout.",
        "question": "Quelle action de secours prioritaire absolue doit être entreprise ?",
        "options": ["Alerte SAMU et massage cardiaque continu", "Placer la victime assise sur une chaise", "Lui faire boire de l'eau fraîche"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Toutes les liaisons télécoms et réseaux d'un hôpital universitaire sont brutalement coupées par une cyberattaque.",
        "question": "Quel niveau d'alerte opérationnelle la direction doit-elle activer ?",
        "options": ["Plan blanc et cellule de crise maximale", "Signalement au prochain comité trimestriel", "Attente passive du redémarrage"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Une panne électrique totale paralyse le système de ventilation des couveuses en service de néonatalogie.",
        "question": "Quelle décision technique et humaine doit être appliquée immédiatement ?",
        "options": ["Basculement d'urgence sur les générateurs de secours", "Attente du technicien le lendemain", "Ouverture des fenêtres de la maternité"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Une rupture de canalisation d'eau inonde la salle technique principale des commutateurs d'une banque.",
        "question": "Quelle action d'urgence matérielle est requise sur le champ ?",
        "options": ["Coupure électrique d'urgence et arrêt sécurisé", "Programmation d'une visite la semaine prochaine", "Mise en place d'une simple serpillière"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Un incendie se déclare dans un entrepôt de stockage de produits chimiques avec un fort dégagement toxique.",
        "question": "Quelle est la première consigne prioritaire ?",
        "options": ["Évacuation immédiate et appel des pompiers", "Fermer les portes et rester à l'intérieur", "Ranger les cartons restants"],
        "index_correct": 0,
        "categorie": "triage"
    },
    {
        "contexte": "Une rupture de digue fluviale menace d'inonder un bourg résidentiel dans l'heure qui vient.",
        "question": "Quelle décision de sécurité civile doit être promulguée immédiatement ?",
        "options": ["Ordre d'évacuation préventive d'urgence", "Attente passive de la décrue", "Rénovation de la digue au budget prochain"],
        "index_correct": 0,
        "categorie": "triage"
    },

    # Index 1 (8 items)
    {
        "contexte": "Une employée signale qu'une ampoule d'un couloir secondaire clignote de temps en temps sans gêner le passage.",
        "question": "Quel niveau de priorité d'intervention technique convient-il d'affecter ?",
        "options": ["Urgence critique avec coupure générale", "Priorité basse (intervention de routine planifiée)", "Évacuation immédiate du bâtiment"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un patient adulte consulte pour un rhume léger avec écoulement nasal clair sans fièvre depuis 24 heures.",
        "question": "Quel niveau de prise en charge médicale est approprié ?",
        "options": ["Appel des urgences réanimation", "Consultation de médecine générale de routine", "Hospitalisation en soins intensifs"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un collaborateur signale que l'horloge murale de la cafétéria retarde de 3 minutes.",
        "question": "Quelle priorité attribuer à ce ticket de maintenance des locaux ?",
        "options": ["Urgence prioritaire P1", "Priorité minimale P4 (non bloquante)", "Intervention nocturne d'astreinte"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un utilisateur constate qu'un texte d'aide dans l'application contient une coquille sans gêner l'usage.",
        "question": "Comment classifier cette anomalie dans le backlog produit ?",
        "options": ["Incident bloquant critique", "Ticket de correction cosmétique de basse priorité", "Refonte intégrale de l'application"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un utilisateur demande à changer la couleur de fond de son interface personnelle pour le confort visuel.",
        "question": "Quelle priorité d'assistance informatique correspond à cette demande ?",
        "options": ["Urgence bloquante P1", "Demande de confort de faible priorité", "Intervention en astreinte week-end"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un patient se présente pour le renouvellement annuel de son ordonnance de lunettes sans trouble visuel aigu.",
        "question": "Dans quelle filière de soins doit-il être orienté ?",
        "options": ["Urgences ophtalmologiques chirurgicales", "Consultation programmée d'ophtalmologie de routine", "Appel du 15 pour ambulance"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un collaborateur signale que la molette de sa souris d'ordinateur grince légèrement sans bloquer le défilement.",
        "question": "Quel niveau de priorité informatique faut-il attribuer à cette requête ?",
        "options": ["Incident majeur bloquant l'entreprise", "Priorité très basse (remplacement de routine)", "Arrêt des serveurs centraux"],
        "index_correct": 1,
        "categorie": "triage"
    },
    {
        "contexte": "Un client remarque que le curseur change d'apparence lors du survol d'une icône dans son espace client.",
        "question": "Comment classifier cette observation fonctionnelle ?",
        "options": ["Urgence de sécurité maximale", "Comportement normal sans gravité", "Panne matérielle du système"],
        "index_correct": 1,
        "categorie": "triage"
    },

    # Index 2 (9 items)
    {
        "contexte": "Un nourrisson de 18 mois a avalé une pile bouton au lithium il y a 20 minutes sous les yeux de ses parents.",
        "question": "Quelle est la conduite de triage hospitalier indispensable ?",
        "options": ["Attendre 48h l'évacuation dans les selles", "Donner un verre de lait et surveiller", "Urgence endoscopique ou chirurgicale absolue immédiate"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Dans une usine chimique, une alarme de fuite de gaz toxique chlore se déclenche sur les cuves.",
        "question": "Quel protocole d'urgence doit être exécuté immédiatement ?",
        "options": ["Envoi d'un courriel pour la réunion du lendemain", "Attente de la fin de journée", "Déclenchement du plan d'évacuation d'urgence du site"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Une cycliste fait une chute, présente une fracture ouverte du membre inférieur avec saignement artériel pulsatile.",
        "question": "Quelle mesure d'urgence vitale précède toute autre action ?",
        "options": ["Lui donner à manger pour reprendre des forces", "L'aider à se relever pour marcher", "Compression immédiate de l'artère ou pose de garrot"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Un ouvrier fait une chute de 4 mètres de hauteur avec perte de connaissance et suspicion de traumatisme rachidien.",
        "question": "Quel degré de priorité médicale s'impose pour sa prise en charge ?",
        "options": ["Retour à domicile en bus", "Rendez-vous chez le médecin demain", "Urgence absolue avec immobilisation rachidienne et SMUR"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Une femme de 28 ans fait un choc anaphylactique brutal après piqûre de guêpe avec détresse respiratoire aiguë.",
        "question": "Quel traitement d'urgence extrême doit être administré sans aucun délai ?",
        "options": ["Un verre d'eau tiède apaisant", "Un comprimé de paracétamol", "Une injection intramusculaire d'adrénaline (épinéphrine)"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Un enfant de 3 ans inhale une cacahuète et présente une suffocation brutale, aphone, devenant cyanosé.",
        "question": "Quel geste de secours d'urgence doit être effectué sans attendre ?",
        "options": ["Lui donner de grandes gorgées d'eau", "L'allonger sur le dos et attendre", "Manœuvre de désobstruction d'urgence (claques dorsales adaptées)"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Un automobiliste victime d'un choc frontal violent est incarcéré avec suspicion d'hémorragie interne grave.",
        "question": "Quel type de secours spécialisé doit être mobilisé immédiatement ?",
        "options": ["Remorquage du véhicule sans soin", "Visite médicale de routine dans un mois", "Désincarcération par sapeurs-pompiers et équipe médicale SMUR"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Le système radar d'un grand aéroport international subit une perte totale d'affichage en plein trafic aérien dense.",
        "question": "Quelle mesure de sécurité aérienne d'urgence critique doit être prise ?",
        "options": ["Poursuite des vols sans consigne", "Publication d'un communiqué sur les réseaux", "Suspension immédiate des décollages et mise en attente sécurisée des vols"],
        "index_correct": 2,
        "categorie": "triage"
    },
    {
        "contexte": "Un homme de 45 ans présente une hémiplégie faciale et brachiale brutale avec trouble soudain de la parole (AVC).",
        "question": "Quelle réaction d'urgence médicale doit être enclenchée à la minute ?",
        "options": ["Le laisser se reposer quelques heures", "Lui donner de l'aspirine sans avis médical", "Appel immédiat du SAMU (15) pour prise en charge en filière AVC"],
        "index_correct": 2,
        "categorie": "triage"
    }
]
