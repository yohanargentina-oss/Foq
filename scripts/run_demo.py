"""
Script de démonstration interactif pour Foq.
Montre des prises de décision instantanées avec scores de probabilité calibrés.
"""

import sys
import os

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq.engine import FoqEngine
from foq.schemas import BinaryChoice, ClassificationChoice, Boolean, Choice, Score


def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def format_bar(prob: float, length: int = 25) -> str:
    filled = int(round(prob * length))
    return "█" * filled + "░" * (length - filled)


def main():
    print_separator("⚡ FOQ SYSTEM 1 ENGINE - DEMONSTRATION")
    engine = FoqEngine(base_url="http://127.0.0.1:8089")

    if not engine.is_server_ready():
        print("[!] Le serveur Foq n'est pas démarré sur http://127.0.0.1:8089.")
        print("[>] Lancez d'abord le script : start_foq_server.cmd")
        return

    print("[+] Connecté au serveur Foq avec succès.")
    print(f"[*] Température de calibration active : T = {engine.scaler.temperature:.3f}")

    # Test 1 : Détection Binaire Rapide
    print_separator("Test 1 : Détection Spam / Hameçonnage (Binaire)")
    text_1 = "URGENT : Votre carte bancaire a été suspendue. Cliquez ici immédiatement pour valider vos identifiants : http://bit.ly/secure-fake"
    schema_1 = BinaryChoice(
        name="is_phishing",
        question="Ce message est-il une tentative d'hameçonnage (phishing / arnaque) ?",
        true_label="Hameçonnage / Arnaque",
        false_label="Message légitime",
    )
    print(f"Texte analysé :\n\"{text_1}\"")
    res_1 = engine.decide(text_1, schema_1)

    print(f"\nVerdict : {res_1['decision_label']} ({res_1['confidence'] * 100:.1f}%)")
    print(f"Latence : {res_1['latency_ms']:.1f} ms | Tokens générés : {res_1['tokens_predicted']}")
    print("Distribution calibrée :")
    for k, p in res_1["calibrated_probabilities"].items():
        lbl = next(opt.label for opt in schema_1.options if opt.key == k)
        print(f"  [{k}] {lbl:<25} : {p*100:5.1f}% |{format_bar(p)}|")

    # Test 2 : Routage Multi-classes
    print_separator("Test 2 : Routage Automatique de Ticket Support")
    text_2 = "Bonjour, j'ai été débité deux fois pour ma facture du mois de septembre, numéro de commande #84920. Pouvez-vous me rembourser le trop-perçu ?"
    schema_2 = ClassificationChoice(
        name="ticket_category",
        question="Dans quel département ce ticket doit-il être dirigé ?",
        categories=["Facturation & Remboursement", "Support Technique Bug", "Vente & Commercial", "Autre"],
    )
    print(f"Ticket :\n\"{text_2}\"")
    res_2 = engine.decide(text_2, schema_2)

    print(f"\nAiguillage retenu : {res_2['decision_label']} ({res_2['confidence'] * 100:.1f}%)")
    print(f"Latence : {res_2['latency_ms']:.1f} ms")
    for k, p in res_2["calibrated_probabilities"].items():
        lbl = next(opt.label for opt in schema_2.options if opt.key == k)
        print(f"  [{k}] {lbl:<30} : {p*100:5.1f}% |{format_bar(p)}|")

    # Test 3 : Décision Multi-champs en parallèle (Système 1 Complet)
    print_separator("Test 3 : Évaluation Multi-champs Simultanée (Schéma JSON)")
    text_3 = "Notre serveur de production est tombé en panne ! Aucun client ne peut se connecter depuis 10 minutes !"
    schemas_multi = [
        ClassificationChoice(
            name="urgence",
            question="Quel est le niveau de gravité ?",
            categories=["Critique (P0)", "Élevé (P1)", "Moyen (P2)", "Faible (P3)"],
        ),
        ClassificationChoice(
            name="service_impacte",
            question="Quel domaine est concerné ?",
            categories=["Infrastructure / Serveurs", "Design / CSS", "Facturation", "Ressources Humaines"],
        ),
        BinaryChoice(
            name="alerte_oncall",
            question="Faut-il réveiller l'ingénieur d'astreinte immédiatement ?",
            true_label="Oui, réveil immédiat",
            false_label="Non, attendre les heures ouvrées",
        ),
    ]

    print(f"Incident :\n\"{text_3}\"")
    res_multi = engine.decide_multi(text_3, schemas_multi)

    print(f"\nTemps d'exécution total (3 décisions résolues) : {res_multi['total_latency_ms']:.1f} ms")
    print("Sortie typée extraite :")
    import json
    print(json.dumps(res_multi["structured_output"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
