"""
Script de Démonstration Interactive : Foq Browser Agent (Navigation Système 1).
Reproduit l'expérience de réservation et automatisation web réflexe en ~4-7 secondes.
"""

import os
import sys
import time
import argparse

# Configurer l'encodage console Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from foq import FoqEngine, FoqBrowserAgent


DEMO_BOOKING_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Foq Express Flight - Réservation Ultra-Rapide</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f172a;
            color: #f8fafc;
            padding: 40px;
            display: flex;
            justify-content: center;
        }
        .container {
            background: #1e293b;
            padding: 30px;
            border-radius: 12px;
            width: 520px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border: 1px solid #334155;
        }
        h1 { font-size: 24px; color: #38bdf8; margin-top: 0; }
        .badge {
            background: #0284c7;
            color: #fff;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            display: inline-block;
            margin-bottom: 20px;
        }
        label { display: block; margin-top: 15px; font-size: 14px; color: #94a3b8; }
        input[type="text"], input[type="date"] {
            width: 100%;
            padding: 10px 12px;
            margin-top: 6px;
            background: #0f172a;
            border: 1px solid #475569;
            border-radius: 6px;
            color: #fff;
            box-sizing: border-box;
            font-size: 15px;
        }
        input:focus { border-color: #38bdf8; outline: none; }
        button {
            width: 100%;
            padding: 12px;
            margin-top: 25px;
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover { background: #0369a1; }
        .success-panel {
            display: none;
            background: #064e3b;
            border: 1px solid #059669;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-top: 20px;
        }
        .success-panel h2 { color: #34d399; margin: 0 0 10px 0; }
        .ticket-info {
            background: #0f172a;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            text-align: left;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <span class="badge">⚡ Foq Browser Agent - Démo Système 1</span>
        <h1>Réservation de Billet d'Avion</h1>
        <p style="color: #94a3b8; font-size: 14px;">Test d'automatisation instantanée sans latence LLM générative.</p>

        <form id="flight-form" onsubmit="event.preventDefault(); triggerBooking();">
            <label for="aeroport_depart">Aéroport de départ</label>
            <input type="text" id="aeroport_depart" name="aeroport_depart" placeholder="Ex: Paris Charles de Gaulle (CDG)">

            <label for="destination">Destination</label>
            <input type="text" id="destination" name="destination" placeholder="Ex: Tokyo Haneda (HND)">

            <label for="date_depart">Date du départ</label>
            <input type="date" id="date_depart" name="date_depart">

            <button id="btn_reserver" type="button" onclick="triggerBooking()">Confirmer et Réserver le Vol</button>
        </form>

        <div id="success-view" class="success-panel">
            <h2>Vol Réservé avec Succès !</h2>
            <p style="color: #a7f3d0;">Confirmation de réservation générée instantanément.</p>
            <div class="ticket-info" id="ticket-summary">
                Passeport : Riley Brown<br>
                Trajet : Paris -> Tokyo<br>
                Date : 2026-10-15<br>
                Statut : CONFIRMÉ
            </div>
        </div>
    </div>

    <script>
        function triggerBooking() {
            const dep = document.getElementById('aeroport_depart').value;
            const dest = document.getElementById('destination').value;
            if (dep && dest) {
                document.getElementById('flight-form').style.display = 'none';
                document.getElementById('success-view').style.display = 'block';
                document.title = "Vol Confirmé : " + dep + " vers " + dest;
            }
        }
    </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Foq Browser Agent - Démonstration Système 1")
    parser.add_argument("--visible", action="store_true", default=True, help="Ouvrir le navigateur visible (défaut: True)")
    parser.add_argument("--headless", action="store_true", help="Lancer en arrière-plan sans fenêtre")
    parser.add_argument("--delay", type=int, default=150, help="Délai entre actions en ms pour observation visuelle (défaut: 150)")
    args = parser.parse_args()

    headless = False if not args.headless else True

    print("=" * 70)
    print("⚡ FOQ BROWSER AGENT - AUTOMATISATION WEB SYSTÈME 1")
    print(f"🚀 Moteur : Foq 27B Local (http://127.0.0.1:8089)")
    print(f"🖥️ Mode navigateur : {'Visible (Chromium)' if not headless else 'Headless'}")
    print("=" * 70)

    engine = FoqEngine()
    if not engine.is_server_ready():
        print("[ERREUR] Le serveur Foq n'est pas joignable sur le port 8089.")
        print("Vérifiez que start_foq_server.cmd est actif.")
        return 1

    agent = FoqBrowserAgent(
        engine=engine,
        headless=headless,
        max_steps=10,
        step_delay_ms=args.delay
    )

    print("\n[SCÉNARIO] : Réservation express de vol (Inspiré de la vidéo de Riley Brown)")
    goal = "Remplir le formulaire avec départ Paris, destination Tokyo, date 2026-10-15 et cliquer sur Confirmer pour réserver le vol"
    params = {
        "depart": "Paris CDG",
        "destination": "Tokyo HND",
        "date": "2026-10-15"
    }

    print(f"Objectif : {goal}")
    print("Démarrage de la navigation...\n")

    t0 = time.perf_counter()
    result = agent.run(
        goal=goal,
        start_url="about:blank",
        params=params,
        html_content=DEMO_BOOKING_HTML
    )
    total_time = time.perf_counter() - t0

    print(result.summary())
    print("\n" + "=" * 70)
    if result.success:
        print(f"🏆 MISSION RÉUSSIE EN {total_time:.2f} SECONDES !")
        print("Zéro token de texte généré - Décision pure Feed-Forward 1-Pass.")
    else:
        print("⚠️ Objectif partiellement atteint ou dépassé.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
