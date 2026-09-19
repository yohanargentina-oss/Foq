# -*- coding: utf-8 -*-
"""
Catégorie 9 : routage (25 items)
Distribution : 8 index 0, 8 index 1, 9 index 2
"""

ROUTAGE_ITEMS = [
    # Index 0 (8 items)
    {
        "contexte": "Un client écrit : 'L'ergonomie du site est superbe, mais mon compte a été débité deux fois pour la commande #4582.'",
        "question": "Vers quel service ce ticket doit-il être orienté en priorité ?",
        "options": ["Service Comptabilité et Facturation", "Équipe Design et Graphisme", "Service Marketing relationnel"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket utilisateur : 'J'adore vos produits, mais je n'arrive plus à réinitialiser mon mot de passe de compte.'",
        "question": "Vers quelle équipe orienter ce blocage d'accès ?",
        "options": ["Support Authentification et Accès", "Service Logistique et Livraisons", "Service Achats Fournisseurs"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Courriel client : 'Merci pour vos vœux. Pouvez-vous m'adresser la facture acquittée avec TVA de mon dernier achat ?'",
        "question": "Quel service gère l'émission et l'envoi de ce justificatif ?",
        "options": ["Service Facturation et Comptabilité", "Équipe Événementiel", "Service Sécurité des Systèmes"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket d'un abonné : 'Mon prélèvement a échoué car ma carte est expirée, comment mettre à jour mes coordonnées bancaires ?'",
        "question": "Quel service est habilité à traiter la mise à jour bancaire ?",
        "options": ["Service Gestion des Abonnements et Paiements", "Service Recherche et Développement", "Pôle Partenariats"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket d'un client B2B : 'Notre entreprise souhaite équiper 200 salariés de votre logiciel avec un contrat annuel.'",
        "question": "Vers quel pôle ce prospect grand compte doit-il être dirigé ?",
        "options": ["Pôle Ventes Grands Comptes et Commercial B2B", "Service Réclamations Particuliers", "Service Maintenance des Locaux"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket d'un acheteur : 'Le transporteur indique que mon colis est livré, mais ma boîte aux lettres est vide.'",
        "question": "Vers quel service réclamation acheminer cette avarie de transport ?",
        "options": ["Service Suivi de Livraison et Litiges Transport", "Équipe Design Produit", "Service Relations Investisseurs"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket utilisateur : 'Je reçois vos newsletters trois fois par semaine et le lien de désinscription est brisé.'",
        "question": "Vers quelle équipe ce problème de campagne marketing doit-il aller ?",
        "options": ["Équipe Marketing Digital et CRM", "Service Logistique Entrepôt", "Direction Financière"],
        "index_correct": 0,
        "categorie": "routage"
    },
    {
        "contexte": "Demande d'un client pro : 'Nous avons besoin d'une attestation fiscale à jour pour notre dossier fournisseur.'",
        "question": "Vers quel service orienter cette demande administrative ?",
        "options": ["Service Administratif et Comptabilité Fournisseurs", "Pôle Développement Mobile", "Service SAV Matériel"],
        "index_correct": 0,
        "categorie": "routage"
    },

    # Index 1 (8 items)
    {
        "contexte": "Message utilisateur : 'J'ai bien reçu vos tutoriels vidéo, en revanche l'application crash sur iOS 17.'",
        "question": "Quel pôle technique doit prendre en charge cette demande ?",
        "options": ["Pôle Marketing de contenu", "Équipe Support Technique et Mobile", "Service Commercial Abonnements"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Message reçu : 'Votre livreur était à l'heure, malheureusement le colis contenait un écran brisé.'",
        "question": "Vers quel département ce dossier de réclamation doit-il être routé ?",
        "options": ["Pôle Communication Interne", "Service Après-Vente et Retours", "Service Juridique Droit des Sociétés"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Signalement client : 'Le produit est parfait, cependant la notice d'utilisation en français est absente du carton.'",
        "question": "Vers quel service orienter cette demande de documentation manquante ?",
        "options": ["Service Juridique Contentieux", "Service Documentation et Support Produit", "Service Trésorerie"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Signalement : 'Le bouton d'accueil est mal aligné sur navigateur Safari, bien que les achats fonctionnent.'",
        "question": "À qui transmettre ce retour d'anomalie d'affichage mineure ?",
        "options": ["Service Comptabilité Générale", "Équipe Développement Front-End et UI", "Service Ressources Humaines"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Message reçu : 'J'ai repéré une faille dans votre API REST permettant d'énumérer les profils sans jeton.'",
        "question": "Quel pôle spécialisé doit être immédiatement alerté ?",
        "options": ["Service Facturation et Litiges", "Équipe Cybersécurité et CERT Interne", "Service Communication Réseaux"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Message client : 'Vos vêtements sont superbes mais j'ai reçu une taille M au lieu de la taille XL commandée.'",
        "question": "Vers quel service orienter cette erreur de préparation de colis ?",
        "options": ["Pôle Sécurité Informatique", "Service Échanges, Retours et SAV", "Service Juridique Contrats"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Message : 'Notre cabinet d'avocats met en demeure votre société pour contrefaçon de marque déposée.'",
        "question": "Quel département doit impérativement instruire cette mise en demeure ?",
        "options": ["Pôle Accueil Téléphonique", "Direction des Affaires Juridiques", "Service Technique Front-Office"],
        "index_correct": 1,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket client : 'Le code promo 'SUMMER' reçu par SMS ne s'applique pas lors de la validation du panier.'",
        "question": "Quel service gère les anomalies des offres commerciales web ?",
        "options": ["Direction des Ressources Humaines", "Support Commercial et E-commerce", "Service Maintenance Serveurs"],
        "index_correct": 1,
        "categorie": "routage"
    },

    # Index 2 (9 items)
    {
        "contexte": "Demande client : 'Votre conseiller a été très aimable, mais je souhaite exercer mon droit de rétractation sous 14 jours.'",
        "question": "Quel service compétent doit traiter cette démarche légale ?",
        "options": ["Pôle Recrutement et Formation", "Service Support Informatique", "Service Relation Client et Rétractations"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Demande d'un ancien usager : 'Je souhaite recevoir l'ensemble de mes données personnelles conformément au RGPD.'",
        "question": "À quelle entité de l'entreprise ce courriel doit-il être transmis ?",
        "options": ["Pôle Relations Presse", "Service Commercial Entreprises", "Délégué à la Protection des Données (DPO)"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Message d'un candidat : 'J'ai vu votre offre d'emploi de développeur Python sur les réseaux et je joins mon CV.'",
        "question": "Vers quel département interne faut-il transférer ce message ?",
        "options": ["Pôle Ventes et Négociation", "Service Informatique Réseau", "Département Ressources Humaines et Recrutement"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Message d'un journaliste : 'Je prépare un reportage économique et sollicite une interview avec la direction.'",
        "question": "Vers quelle équipe ce contact média doit-il être acheminé ?",
        "options": ["Support Technique Utilisateurs", "Service Expéditions Entrepôt", "Pôle Relations Presse et Médias"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Demande client : 'J'ai changé de domicile suite à un déménagement, pouvez-vous mettre à jour mon adresse postale ?'",
        "question": "Quel service doit prendre en charge la modification des coordonnées ?",
        "options": ["Pôle Développement Logiciel", "Service Recrutement Stagiaires", "Service Client et Gestion des Profils"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Courriel d'un prestataire : 'Nous vous transmettons notre devis pour le renouvellement du parc d'imprimantes.'",
        "question": "À quel service ce devis d'équipement interne doit-il être adressé ?",
        "options": ["Support Client Utilisateurs", "Service Expédition Marchandises", "Service Achats et Moyens Généraux"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket utilisateur : 'Mon compte est bloqué pour activité inhabituelle alors que je suis en déplacement professionnel.'",
        "question": "Quel pôle doit vérifier le compte et lever la restriction de sécurité ?",
        "options": ["Service Achats Mobiliers", "Équipe Graphisme et Logos", "Support Gestion des Comptes et Sécurité Utilisateur"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Message d'un institut scientifique : 'Nous proposons une collaboration de recherche sur vos algorithmes d'IA.'",
        "question": "Vers quel service interne transférer cette proposition partenariale ?",
        "options": ["Service Facturation Réclamations", "Pôle Logistique Réception", "Direction Scientifique et R&D"],
        "index_correct": 2,
        "categorie": "routage"
    },
    {
        "contexte": "Ticket utilisateur : 'L'option de paiement en 3 fois sans frais est grisée lors de mon achat de 500 euros.'",
        "question": "Vers quelle équipe orienter cette anomalie sur le module bancaire ?",
        "options": ["Pôle Recrutement Cadres", "Service Relations Presse", "Service Support Paiement et Crédit Client"],
        "index_correct": 2,
        "categorie": "routage"
    }
]
