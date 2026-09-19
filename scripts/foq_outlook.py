"""
Module d'intégration Foq <-> Outlook (Microsoft Graph API).
Analyse et classe les emails de la boîte de réception avec le moteur Système 1 Foq.
"""

import os
import sys
import json
import time
import warnings
from typing import Dict, Any, List, Optional
from pathlib import Path

warnings.filterwarnings("ignore")

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ajouter le répertoire racine au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx

try:
    import msal
except ImportError:
    msal = None

from foq import FoqEngine, Noul, Choice, Score

# Configuration par défaut
CACHE_FILE = Path(__file__).parent.parent / "data" / "outlook_token_cache.bin"
ENV_FILE = Path(__file__).parent.parent / ".env"

SCOPES = [
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/User.Read",
]


def load_env():
    """Charge les variables d'environnement depuis le fichier .env si présent."""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def build_msal_app(client_id: str, cache: msal.SerializableTokenCache) -> msal.PublicClientApplication:
    """Construit l'application client public MSAL pour comptes personnels."""
    return msal.PublicClientApplication(
        client_id=client_id,
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache,
    )


def get_graph_token(client_id: str) -> Optional[str]:
    """Récupère un token d'accès Graph via cache local ou Device Code Flow."""
    if not msal:
        print("[ERREUR] Le package msal n'est pas installé. Exécutez : py -3 -m pip install msal")
        return None

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache = msal.SerializableTokenCache()
    if CACHE_FILE.exists():
        cache.deserialize(CACHE_FILE.read_text(encoding="utf-8"))

    app = build_msal_app(client_id, cache)
    accounts = app.get_accounts()

    # Tentative en cache silencieux
    if accounts:
        res = app.acquire_token_silent(SCOPES, account=accounts[0])
        if res and "access_token" in res:
            return res["access_token"]

    # Device Code Flow interactif
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print(f"[ERREUR] Impossible d'initier le Device Code Flow : {flow.get('error_description', flow)}", flush=True)
        return None

    print("\n" + "=" * 60, flush=True)
    print("🔑 AUTHENTIFICATION OUTLOOK REQUISE", flush=True)
    print("=" * 60, flush=True)
    print(f"1. Ouvrez ce lien dans votre navigateur : {flow['verification_uri']}", flush=True)
    print(f"2. Saisissez ce code de validation      : {flow['user_code']}", flush=True)
    print(f"3. Connectez-vous avec                 : {os.getenv('USER_EMAIL', 'votre adresse Outlook')}", flush=True)
    print("=" * 60 + "\n", flush=True)

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        CACHE_FILE.write_text(cache.serialize(), encoding="utf-8")
        print(" Connexion réussie et session enregistrée localement !\n", flush=True)
        return result["access_token"]
    else:
        print(f"[ERREUR] Échec de l'authentification : {result.get('error_description', result)}", flush=True)
        return None


def fetch_unread_emails_graph(access_token: str, max_count: int = 5) -> List[Dict[str, Any]]:
    """Récupère les emails non lus via Microsoft Graph API."""
    url = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
    params = {
        "$filter": "isRead eq false",
        "$top": str(max_count),
        "$select": "id,subject,from,receivedDateTime,bodyPreview",
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    resp = httpx.get(url, headers=headers, params=params, timeout=15.0)
    if resp.status_code == 200:
        return resp.json().get("value", [])
    else:
        print(f"[ERREUR Graph API] Code {resp.status_code}: {resp.text}")
        return []


def update_email_graph(access_token: str, message_id: str, action: str, mark_as_read: bool = False):
    """Applique une catégorie ou marque comme lu sur Graph API."""
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    category_map = {
        "urgent": "Rouge",
        "a_traiter": "Jaune",
        "archive": "Bleu",
        "spam": "Orange",
    }
    category = category_map.get(action, "Vert")
    payload = {
        "categories": [category],
        "isRead": mark_as_read,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    httpx.patch(url, headers=headers, json=payload, timeout=10.0)


def classify_with_foq(engine: FoqEngine, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """Interroge Foq pour décider de l'action à mener sur l'email."""
    sender = email_data.get("from", {}).get("emailAddress", {}).get("address", "Inconnu")
    sender_name = email_data.get("from", {}).get("emailAddress", {}).get("name", "")
    subject = email_data.get("subject", "Sans objet")
    preview = email_data.get("bodyPreview", "")

    state_text = f"Expéditeur: {sender_name} <{sender}>\nObjet: {subject}\nCorps du message: {preview[:600]}"

    decision = engine.system_one(
        state=state_text,
        questions={
            "action": Choice(
                instructions="Sélectionnez l'action appropriée pour cet email",
                choices={
                    "urgent": "Urgent : nécessite une intervention rapide",
                    "a_traiter": "À traiter : email normal nécessitant action ultérieure",
                    "archive": "Archive : informatif, notification ou newsletter",
                    "spam": "Spam : publicité non sollicitée ou démarchage",
                },
            ),
            "reponse_requise": Noul("Cet email attend-il une réponse rédigée ?"),
            "gravite": Score(
                instructions="Niveau d'importance de 1 à 4",
                levels={"1": "Mineur", "2": "Normal", "3": "Important", "4": "Critique"},
            ),
        },
    )

    return {
        "action": decision.action.choice,
        "action_conf": decision.action.confidence,
        "reponse_requise": decision.reponse_requise.answer,
        "gravite_score": getattr(decision.gravite, "score", 1.0),
        "latency_ms": decision.latency_ms,
    }


def main():
    load_env()
    print("⚡ Démarrage du Triage Intelligent Outlook avec Foq...")

    # Vérification du serveur Foq
    engine = FoqEngine()
    if not engine.is_server_ready():
        print("[ERREUR] Le serveur Foq n'est pas démarré sur http://127.0.0.1:8089.")
        print("Lancez d'abord dans un terminal : start_foq_server.cmd (ou start_foq_server.sh)")
        sys.exit(1)

    print(" Serveur Foq connecté (Système 1)")

    client_id = os.getenv("AZURE_CLIENT_ID")
    if not client_id:
        print("\n" + "!" * 60)
        print("ℹ️ ID CLIENT MICROSOFT REQUIS")
        print("!" * 60)
        print("Renseignez-le dans le fichier .env (AZURE_CLIENT_ID=...)")
        print("ou passez-le en argument : py -3 scripts/foq_outlook.py <CLIENT_ID>")
        print("!" * 60 + "\n")
        if len(sys.argv) > 1:
            client_id = sys.argv[1]
        else:
            client_id = input("Collez votre Client ID Microsoft (ou tapez Entrée pour quitter) : ").strip()
            if not client_id:
                sys.exit(0)

    token = get_graph_token(client_id)
    if not token:
        sys.exit(1)

    print(f"\n📥 Récupération des emails non lus pour {os.getenv('USER_EMAIL', 'votre boîte Outlook')}...")
    emails = fetch_unread_emails_graph(token, max_count=5)

    if not emails:
        print("📭 Aucun email non lu trouvé dans la boîte de réception.")
        return

    print(f"👉 {len(emails)} email(s) à classifier :\n")

    for i, msg in enumerate(emails, 1):
        subj = msg.get("subject", "Sans objet")
        sender = msg.get("from", {}).get("emailAddress", {}).get("address", "Inconnu")

        res = classify_with_foq(engine, msg)

        print(f"--- [Mail #{i}] ---")
        print(f" De        : {sender}")
        print(f" Objet     : {subj}")
        print(f" Verdict   : {res['action'].upper()} (Confiance: {res['action_conf']*100:.1f}%)")
        print(f" Réponse ? : {'OUI' if res['reponse_requise'] else 'NON'}")
        print(f" Gravité   : {res['gravite_score']:.1f}/4.0")
        print(f" Vitesse   : {res['latency_ms']:.1f} ms")

        # Mise à jour dans Outlook
        mark_read = res["action"] in ["archive", "spam"]
        update_email_graph(token, msg["id"], res["action"], mark_as_read=mark_read)
        print(f" Catégorie appliquée dans Outlook (Marqué lu: {mark_read})\n")

    print("🎉 Traitement terminé !")


if __name__ == "__main__":
    main()
