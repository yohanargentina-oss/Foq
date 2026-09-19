# -*- coding: utf-8 -*-
"""
Catégorie 5 : negations_multiples (30 items)
Distribution : 10 index 0, 10 index 1, 10 index 2
"""

NEGATIONS_ITEMS = [
    # Index 0 (10 items)
    {
        "contexte": "Le bail stipule : 'Il n'est pas interdit au preneur de ne pas repeindre les boiseries à la sortie'.",
        "question": "Le locataire a-t-il l'obligation légale de repeindre les boiseries avant de quitter les lieux ?",
        "options": ["Non, il est libre de s'en abstenir", "Oui, c'est obligatoire", "Uniquement en cas de dégradation"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "La note de service annonce qu'il n'est nullement exclu de ne pas reconduire l'expérimentation du télétravail.",
        "question": "L'arrêt de l'expérimentation du télétravail est-il envisageable selon ce document ?",
        "options": ["Oui, c'est une éventualité possible", "Non, la reconduction est obligatoire", "Le télétravail est déjà annulé"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Les conditions d'assurance prévoient : 'Ne sont pas exclues les réparations ne résultant pas d'une usure normale'.",
        "question": "Une panne soudaine et imprévisible non liée à l'usure normale est-elle couverte ?",
        "options": ["Oui, elle est couverte par la garantie", "Non, elle fait l'objet d'une exclusion", "Seulement après décision judiciaire"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "La convention collective indique : 'L'employeur ne peut pas ne pas indemniser les astreintes de nuit'.",
        "question": "L'employeur est-il contraint de rémunérer les salariés effectuant des astreintes de nuit ?",
        "options": ["Oui, l'indemnisation est obligatoire", "Non, un simple repos suffit", "Uniquement si le salarié le réclame"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Un contrat prévoit : 'Le prestataire ne garantit pas l'absence d'interruptions non programmées de service'.",
        "question": "Le client peut-il exiger une disponibilité absolue sans aucune coupure imprévue ?",
        "options": ["Non, le prestataire a exclu cet engagement", "Oui, la continuité totale est garantie", "Uniquement les jours ouvrés"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le compromis énonce : 'L'acquéreur ne peut renoncer à son dépôt s'il ne subit aucun refus de prêt'.",
        "question": "L'acheteur qui obtient son crédit peut-il annuler la vente sans indemnité de dédit ?",
        "options": ["Non, il est engagé à finaliser l'achat", "Oui, il dispose d'un droit discrétionnaire", "Seulement avec l'accord bancaire"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le règlement mentionne : 'Aucun dossier ne sera rejeté pour le motif qu'il ne comporte aucun logo'.",
        "question": "Un candidat peut-il soumettre un dossier neutre sans aucun logo sans être disqualifié ?",
        "options": ["Oui, son dossier sera accepté", "Non, un logo commercial est requis", "Il recevra une pénalité de points"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le code de procédure énonce : 'Il n'est pas défendu aux parties de ne pas conclure de conciliation'.",
        "question": "Les deux parties en litige ont-elles le droit de refuser la conciliation pour aller au procès ?",
        "options": ["Oui, le recours direct au juge est permis", "Non, l'accord amiable est forcé", "Uniquement devant le tribunal de commerce"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le règlement de copropriété dispose : 'Il n'est pas prohibé de ne point installer de paillasson'.",
        "question": "Un résident sans paillasson devant sa porte enfreint-il le règlement de l'immeuble ?",
        "options": ["Non, l'installation n'est pas obligatoire", "Oui, c'est une infraction aux règles", "Seulement au rez-de-chaussée"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "L'avenant au contrat dispose : 'Les parties ne sauraient prétendre qu'aucun préavis n'était requis'.",
        "question": "Un préavis était-il formellement exigé selon ce texte contractuel ?",
        "options": ["Oui, un préavis était bien requis", "Non, aucun délai n'était prévu", "Le préavis était purement facultatif"],
        "index_correct": 0,
        "categorie": "negations_multiples"
    },

    # Index 1 (10 items)
    {
        "contexte": "Le règlement dispose : 'Nul ne peut prétendre ne pas ignorer les consignes sans validation de formation'.",
        "question": "Un salarié sans formation validée peut-il prétendre connaître les consignes ?",
        "options": ["Oui, sans condition préalable", "Non, le texte lui interdit cette prétention", "Seulement avec 5 ans d'ancienneté"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le texte fiscal dispose : 'Il n'est pas illégal de ne point déclarer les gratifications sous le seuil'.",
        "question": "Un contribuable commet-il une fraude en omettant un don conforme au seuil ?",
        "options": ["Oui, toute somme est taxable", "Non, aucune infraction n'est commise", "Oui, si c'est du liquide"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Un accord stipule : 'Le fournisseur ne saurait refuser la livraison dès lors que le paiement n'est pas en défaut'.",
        "question": "Le fournisseur peut-il bloquer la commande d'un client dont le paiement est honoré ?",
        "options": ["Oui, selon sa convenance commerciale", "Non, il a l'obligation de livrer", "Uniquement en période de congés"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le règlement de l'immeuble stipule : 'Il n'est pas interdit aux résidents de ne pas assister à l'assemblée'.",
        "question": "Un copropriétaire est-il légalement obligé de se déplacer à l'assemblée générale ?",
        "options": ["Oui, sous peine d'amende", "Non, il peut s'abstenir ou mandater un tiers", "Uniquement s'il a plus de 10 %"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "La directive précise : 'Les banques ne sauraient omettre de ne pas transférer de fonds sans vérification'.",
        "question": "Les banques sont-elles tenues de vérifier l'identité avant de transférer les fonds ?",
        "options": ["Non, les vérifications sont optionnelles", "Oui, le contrôle préalable est obligatoire", "Seulement pour les virements internationaux"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le guide de sécurité stipule : 'Il n'est pas permis de ne pas verrouiller les accès le soir venu'.",
        "question": "Le personnel doit-il verrouiller les accès de secours lors de la fermeture nocturne ?",
        "options": ["C'est une recommandation sans contrainte", "Oui, le verrouillage est strictement obligatoire", "Non, les issues restent ouvertes"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le contrat de maintenance prévoit : 'Le technicien ne manquera pas d'intervenir si l'incident n'est pas résolu'.",
        "question": "Une intervention sur site est-elle prévue si le problème technique persiste ?",
        "options": ["Non, aucune visite n'est due", "Oui, le technicien est tenu d'intervenir", "Uniquement si le client paie un surplus"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le bail énonce : 'Le bailleur ne saurait méconnaître son devoir de ne pas troubler la jouissance des lieux'.",
        "question": "Le propriétaire a-t-il le droit de perturber délibérément l'exploitation du commerce ?",
        "options": ["Oui, pour des travaux personnels", "Non, il a l'obligation de respecter la quiétude", "Uniquement en journée"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le contrat de travail stipule : 'L'employé ne peut refuser de ne pas divulguer les secrets de l'entreprise'.",
        "question": "L'employé est-il tenu de garder les secrets industriels confidentiels ?",
        "options": ["Non, il est libéré du secret", "Oui, l'obligation de confidentialité s'impose", "Uniquement pendant la période d'essai"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le code d'urbanisme précise : 'Il n'est pas exigé de ne pas conserver les arbres remarquables'.",
        "question": "Les propriétaires sont-ils autorisés à préserver les arbres remarquables classés ?",
        "options": ["Non, l'abattage est rendu systématique", "Oui, la préservation des arbres est autorisée", "Seulement pour les terrains agricoles"],
        "index_correct": 1,
        "categorie": "negations_multiples"
    },

    # Index 2 (10 items)
    {
        "contexte": "La clause précise : 'Aucun refus de garantie ne sera opposé aux clients n'ayant commis aucune négligence'.",
        "question": "Un client diligent sans aucune faute reprochable peut-il bénéficier de la garantie ?",
        "options": ["Non, la garantie est systématiquement rejetée", "Uniquement avec franchise majorée", "Oui, la garantie lui est accordée"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le protocole mentionne : 'La direction ne refuse pas d'examiner les dossiers ne manquant pas de justificatifs'.",
        "question": "Une demande accompagnée de tous les justificatifs requis sera-t-elle étudiée ?",
        "options": ["Non, elle sera classée sans suite", "Uniquement au trimestre suivant", "Oui, la direction accepte de l'examiner"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le code d'éthique énonce : 'Il n'est pas toléré de ne point signaler un conflit d'intérêts avéré'.",
        "question": "Un employé est-il dans l'obligation de déclarer un conflit d'intérêts avéré ?",
        "options": ["Non, la déclaration reste facultative", "Seulement s'il implique un cadre", "Oui, le signalement est obligatoire"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Une charte informatique indique : 'Aucun utilisateur ne doit négliger de ne pas divulguer ses identifiants'.",
        "question": "Les utilisateurs ont-ils le devoir de garder leurs identifiants strictement confidentiels ?",
        "options": ["Non, le partage est toléré", "Uniquement auprès de collègues directs", "Oui, ils doivent préserver le secret"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "L'article dispose : 'N'est pas punissable la personne qui n'a pas agi sans contrainte irrésistible'.",
        "question": "Une personne ayant agi sous contrainte irrésistible encourt-elle une sanction pénale ?",
        "options": ["Oui, la peine maximale s'applique", "Une sanction financière minimale", "Non, elle bénéficie d'une irresponsabilité"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Une clause précise : 'Il n'est pas défendu au salarié d'exercer dans un secteur non concurrentiel'.",
        "question": "L'ancien salarié peut-il travailler dans une entreprise d'un secteur totalement différent ?",
        "options": ["Non, il doit attendre 2 ans", "Uniquement avec accord écrit", "Oui, cette activité lui est autorisée"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "La police d'assurance indique : 'Ne sont pas non garantis les dommages n'impliquant aucune faute intentionnelle'.",
        "question": "Un sinistre purement accidentel sans intention frauduleuse de l'assuré est-il indemnisé ?",
        "options": ["Non, tous les sinistres sont exclus", "Uniquement si un tiers est responsable", "Oui, le sinistre fait l'objet d'une prise en charge"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "La convention énonce : 'Il n'est pas interdit à l'étudiant de refuser les tâches n'ayant aucun lien avec sa formation'.",
        "question": "Le stagiaire peut-il légitimement décliner une tâche sans rapport avec son cursus ?",
        "options": ["Non, il doit exécuter tous les ordres", "Uniquement après accord du tuteur", "Oui, il a le droit de refuser ces tâches"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Le protocole médical indique : 'Le praticien ne saurait s'abstenir de ne pas délivrer une information loyale'.",
        "question": "Le médecin a-t-il le devoir de fournir une information claire et loyale à son patient ?",
        "options": ["Non, l'information reste discrétionnaire", "Uniquement si la famille le demande", "Oui, le médecin a cette obligation déontologique"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    },
    {
        "contexte": "Les conditions mentionnent : 'Aucun membre ne sera privé de vote sous prétexte qu'il ne verse aucun don'.",
        "question": "Un membre n'ayant versé aucun don volontaire a-t-il le droit de voter à l'assemblée ?",
        "options": ["Non, son droit de vote est suspendu", "Il a seulement une voix consultative", "Oui, il conserve pleinement son droit de vote"],
        "index_correct": 2,
        "categorie": "negations_multiples"
    }
]
