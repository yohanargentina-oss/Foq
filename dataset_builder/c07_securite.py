# -*- coding: utf-8 -*-
"""
Catégorie 7 : securite_info (25 items)
Distribution : 9 index 0, 8 index 1, 8 index 2
"""

SECURITE_ITEMS = [
    # Index 0 (9 items)
    {
        "contexte": "Un administrateur exécute la commande de maintenance : 'rm -rf /var/cache/apt/archives/*'.",
        "question": "Quel est le résultat effectif de cette commande ?",
        "options": ["Purge des paquets téléchargés en cache", "Suppression de tout le système", "Arrêt forcé immédiat du serveur"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Dans un formulaire web, un champ 'identifiant' reçoit la chaîne : 'admin' --'.",
        "question": "À quel vecteur d'attaque cela correspond-il ?",
        "options": ["Une tentative d'injection SQL d'authentification", "Un débordement de mémoire tampon", "Une attaque par déni de service"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un script Python contient : 'os.system(\"ping -c 1 \" + user_ip)' où user_ip n'est pas assaini.",
        "question": "Quelle faille majeure cela introduit-il ?",
        "options": ["Une injection de commande système", "Une vulnérabilité Cross-Site Scripting", "Une fuite de certificat SSL"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un script de sauvegarde contient 'tar -czf backup.tar.gz *' dans un dossier partagé en écriture.",
        "question": "Quelle technique d'exploitation locale est envisageable ?",
        "options": ["Une injection d'options par wildcard tar", "Une corruption du disque dur", "Une coupure du port SSH"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un courriel bancaire urgent pointe vers 'https://connexion-securisee.banque.fr.secure-login-39.com'.",
        "question": "Quel indice prouve qu'il s'agit d'un phishing malveillant ?",
        "options": ["Le domaine réel est secure-login-39.com", "L'emploi du protocole HTTPS", "Les tirets dans l'adresse"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un système stocke les mots de passe sous forme de hash MD5 sans sel (salt).",
        "question": "Quelle attaque permet de retrouver rapidement les mots de passe courants ?",
        "options": ["Une attaque par tables arc-en-ciel", "Une injection de trames ARP", "Un détournement de session TCP"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Une réponse HTTP contient l'en-tête 'Strict-Transport-Security: max-age=31536000'.",
        "question": "Quel mécanisme de protection ce paramètre HSTS applique-t-il ?",
        "options": ["Forcer les connexions futures en HTTPS", "Bloquer les requêtes de l'étranger", "Désactiver le JavaScript client"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un développeur place par mégarde une clé d'API secrète dans un commit git public.",
        "question": "Quelle action urgente doit-il effectuer en priorité ?",
        "options": ["Révoquer immédiatement la clé secrète", "Supprimer le fichier du dépôt local", "Renommer la clé dans le code"],
        "index_correct": 0,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un scan réseau montre que le protocole Telnet (port 23) est actif pour administrer des switchs.",
        "question": "Pourquoi l'usage de Telnet est-il proscrit en sécurité moderne ?",
        "options": ["Il transmet identifiants et données en clair", "Il est incompatible avec IPv4", "Il consomme trop de bande passante"],
        "index_correct": 0,
        "categorie": "securite_info"
    },

    # Index 1 (8 items)
    {
        "contexte": "Une application web affiche le prénom directement sans échappement avec '<script>alert(1)</script>'.",
        "question": "Quelle vulnérabilité critique est exploitée ?",
        "options": ["Un déni de service mémoire", "Une faille Cross-Site Scripting (XSS)", "Une injection LDAP distante"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un attaquant transmet '../../../../etc/passwd' dans le paramètre 'fichier' d'une URL de téléchargement.",
        "question": "Quel type d'attaque web ce paramètre caractérise-t-il ?",
        "options": ["Une injection de code PHP", "Une traversée de répertoires (Path Traversal)", "Un empoisonnement de cache DNS"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un attaquant envoie des requêtes UDP avec une adresse IP source falsifiée pour inonder une cible.",
        "question": "Quel type de cyberattaque cette technique représente-t-elle ?",
        "options": ["Une injection SQL aveugle", "Une attaque DDoS par amplification et usurpation", "Un cheval de Troie polymorphe"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un document bureautique reçu par courriel demande d'activer les 'macros VBA' pour voir le texte.",
        "question": "Quelle est la recommandation impérative face à cette demande ?",
        "options": ["Activer pour vérifier", "Refuser l'activation et supprimer le fichier", "Imprimer le fichier sans l'ouvrir"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Une application web accepte des fichiers XML externes contenant une balise '<!ENTITY xxe SYSTEM \"file:///etc/shadow\">'.",
        "question": "Quel nom porte cette vulnérabilité majeure ?",
        "options": ["Une injection SQL au second degré", "Une vulnérabilité XXE (XML External Entity)", "Une faille CSRF"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un pirate intercepte et altère les communications entre un client et un serveur en se faisant passer pour chacun.",
        "question": "Comment qualifie-t-on formellement cette attaque réseau ?",
        "options": ["Une attaque par déni de service", "Une attaque de l'homme du milieu (MitM)", "Une injection de DLL"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un attaquant piège un utilisateur connecté pour lui faire exécuter un virement via une balise <img> cachée.",
        "question": "Quel type de faille de sécurité ce scénario illustre-t-il ?",
        "options": ["Une injection SQL classique", "Une attaque Cross-Site Request Forgery (CSRF)", "Une fuite de mémoire tampon"],
        "index_correct": 1,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un ransomware chiffre les fichiers partagés de l'entreprise et exige un paiement.",
        "question": "Quelle mesure préventive permet de restaurer l'activité sans rançon ?",
        "options": ["Payer la moitié de la somme", "Avoir des sauvegardes régulières testées et hors-ligne", "Redémarrer les postes de travail"],
        "index_correct": 1,
        "categorie": "securite_info"
    },

    # Index 2 (8 items)
    {
        "contexte": "Une clé USB d'origine inconnue est trouvée sur le parking de la société par un collaborateur.",
        "question": "Quelle est la consigne immédiate de sécurité à appliquer ?",
        "options": ["La brancher pour voir à qui elle est", "La formater sur son poste de travail", "La remettre à la sécurité sans la brancher"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un accès SSH est configuré avec une clé RSA 4096 bits et les mots de passe sont désactivés.",
        "question": "Quel est le niveau de robustesse contre les attaques par dictionnaire ?",
        "options": ["Vulnérable aux attaques rapides", "Faible sur le port 22", "Extrêmement robuste face au brute force"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un internaute consulte ses comptes bancaires depuis un réseau Wi-Fi public sans mot de passe.",
        "question": "Quelle précaution garantit le chiffrement de l'ensemble de son trafic ?",
        "options": ["Utiliser la navigation privée", "Changer son mot de passe", "Utiliser un tunnel VPN chiffré"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Une entreprise met en place une authentification multifacteur (MFA) via une application TOTP.",
        "question": "Quel risque cette mesure permet-elle d'éliminer quasi-totalement ?",
        "options": ["Les pannes matérielles de disque", "Les attaques par injection SQL", "L'usurpation par simple fuite de mot de passe"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un serveur web renvoie l'en-tête de réponse 'X-Frame-Options: DENY'.",
        "question": "Contre quelle attaque ce paramètre protège-t-il les utilisateurs ?",
        "options": ["Les injections SQL aveugles", "Le vol de mot de passe réseau", "Le détournement de clic (Clickjacking)"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un attaquant écrit plus de données qu'alloué dans un tableau en langage C pour écraser l'adresse de retour.",
        "question": "Quelle est la dénomination technique de cette vulnérabilité ?",
        "options": ["Une mauvaise configuration DNS", "Une faille de script JavaScript", "Un débordement de tampon sur la pile (Buffer Overflow)"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un système applique rigoureusement le principe du moindre privilège aux employés.",
        "question": "En quoi consiste concrètement ce principe ?",
        "options": ["Donner tous les accès à la direction", "Changer les identifiants chaque heure", "Accorder seulement les accès strictement nécessaires"],
        "index_correct": 2,
        "categorie": "securite_info"
    },
    {
        "contexte": "Un fichier exécutable téléchargé porte le nom 'rapport.pdf.exe' sous Windows.",
        "question": "Quelle technique trompeuse est employée par l'auteur ?",
        "options": ["Un chiffrement symétrique", "Une modification matérielle", "Une double extension masquant le format exécutable"],
        "index_correct": 2,
        "categorie": "securite_info"
    }
]
