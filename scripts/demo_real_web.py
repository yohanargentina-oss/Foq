"""
Démonstration en direct sur le Vrai Web : Foq Browser Agent (Navigation Système 1).
Exécute des scénarios multi-étapes réels sur Wikipédia ou un e-commerce avec Chromium visible.
"""

import os
import sys
import time
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq import FoqEngine, FoqBrowserAgent


def main():
    parser = argparse.ArgumentParser(description="Preuve de fonctionnement de Foq sur le Vrai Web")
    parser.add_argument("--site", choices=["wiki", "store"], default="wiki", help="Site cible : wiki (Wikipédia) ou store (E-commerce)")
    parser.add_argument("--headless", action="store_true", help="Lancer en arrière-plan sans ouvrir la fenêtre Chromium")
    parser.add_argument("--delay", type=int, default=300, help="Délai en ms entre les étapes pour observer visuellement")
    args = parser.parse_args()

    engine = FoqEngine()
    if not engine.is_server_ready():
        print("[ERREUR] Le serveur Foq n'est pas joignable sur le port 8089.")
        return 1

    agent = FoqBrowserAgent(
        engine=engine,
        headless=args.headless,
        max_steps=6,
        step_delay_ms=args.delay
    )

    print("=" * 75)
    print("🌐 PREUVE DE NAVIGATION SYSTÈME 1 SUR LE VRAI WEB AVEC FOQ")
    print(f"🖥️ Mode navigateur : {'Headless (invisible)' if args.headless else 'Visible (Chromium)'}")
    print("=" * 75)

    if args.site == "wiki":
        print("\n[SCÉNARIO WIKIPÉDIA] :")
        print("1. Recherche de 'Intelligence artificielle' depuis la page d'accueil")
        print("2. Navigation au sein de l'article vers 'Intelligence artificielle générale'")
        goal = "Sur la page d accueil de Wikipedia, rechercher Intelligence artificielle, puis dans l article cliquer sur le lien Intelligence artificielle generale"
        start_url = "https://fr.wikipedia.org"
        params = {"search": "Intelligence artificielle"}
    else:
        print("\n[SCÉNARIO E-COMMERCE / CATALOGUE] :")
        print("1. Accès au catalogue complet sur Books to Scrape")
        print("2. Clic sur la catégorie 'Travel' dans la navigation latérale")
        print("3. Ouverture de la fiche détaillée du livre 'It's Only the Himalayas'")
        goal = "Sur la librairie en ligne, cliquer sur la categorie Travel, puis cliquer sur le livre It s Only the Himalayas pour ouvrir sa fiche detaillee"
        start_url = "http://books.toscrape.com"
        params = {}

    print(f"🎯 Objectif : {goal}")
    print(f"📍 URL de départ : {start_url}")
    print("Démarrage de la navigation...\n")

    t0 = time.perf_counter()
    result = agent.run(goal=goal, start_url=start_url, params=params)
    total_time = time.perf_counter() - t0

    print(result.summary())
    print("\n" + "=" * 75)
    if result.success:
        print(f"🏆 PREUVE ÉTABLIE : Navigation réussie en {total_time:.2f} s !")
        print(f"🌐 Page finale atteinte : {result.final_url}")
    else:
        print("⚠️ Parcours partiel ou non terminé.")
    print("=" * 75)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
