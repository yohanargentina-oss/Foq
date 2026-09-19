"""
Script de Nettoyage Sécurisé Foq <-> Outlook.
Supprime vers la corbeille les spams et les emails à faible intérêt vieux de plus de 1 an.
Protège STRICTEMENT tous les emails importants, sensibles, factures, contrats, bancaires ou personnels.
"""

import os
import sys
import time
import argparse
import asyncio
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import warnings

warnings.filterwarnings("ignore")

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
import msal
from foq import FoqEngine, Choice, Noul

CACHE_FILE = Path(__file__).parent.parent / "data" / "outlook_token_cache.bin"
ENV_FILE = Path(__file__).parent.parent / ".env"
SCOPES = ["https://graph.microsoft.com/Mail.ReadWrite", "https://graph.microsoft.com/User.Read"]

CATEGORY_MAP = {
    "important": "Rouge",
    "faible_interet": "Bleu",
    "spam": "Orange",
}


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_token() -> str:
    cache = msal.SerializableTokenCache()
    if CACHE_FILE.exists():
        cache.deserialize(CACHE_FILE.read_text(encoding="utf-8"))
    client_id = os.getenv("AZURE_CLIENT_ID")
    app = msal.PublicClientApplication(
        client_id=client_id,
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache,
    )
    accounts = app.get_accounts()
    if accounts:
        res = app.acquire_token_silent(SCOPES, account=accounts[0])
        if res and "access_token" in res:
            return res["access_token"]
    raise RuntimeError("Session expirée. Relancez scripts/foq_outlook.py pour vous ré-authentifier.")


async def delete_message_graph(client: httpx.AsyncClient, token: str, msg_id: str) -> bool:
    """Déplace le message vers la corbeille (Éléments supprimés)."""
    url = f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = await client.delete(url, headers=headers, timeout=15.0)
        return resp.status_code in (200, 204)
    except Exception:
        return False


async def process_single_email(
    engine: FoqEngine,
    msg: Dict[str, Any],
    client_graph: httpx.AsyncClient,
    token: str,
    stats: Dict[str, int],
    min_days_old: int,
    dry_run: bool,
):
    from_dict = msg.get("from") or {}
    email_addr_dict = from_dict.get("emailAddress") or {}
    sender = str(email_addr_dict.get("address") or "Inconnu")
    sender_name = str(email_addr_dict.get("name") or "")
    subj = str(msg.get("subject") or "Sans objet")
    preview = str(msg.get("bodyPreview") or "")
    received_str = str(msg.get("receivedDateTime") or "")

    # Calcul de l'âge de l'email
    age_days = 0
    if received_str:
        try:
            received_dt = datetime.datetime.fromisoformat(received_str.replace("Z", "+00:00"))
            age_days = (datetime.datetime.now(datetime.timezone.utc) - received_dt).days
        except Exception:
            pass

    state_text = f"Expéditeur: {sender_name} <{sender}>\nDate: {received_str[:10]}\nObjet: {subj}\nExtrait: {preview[:450]}"

    # Double évaluation par Foq Système 1 :
    # 1. Détection stricte de données sensibles / importantes (factures, banque, travail, perso)
    # 2. Catégorie de contenu
    try:
        decision = await engine.system_one_async(
            state=state_text,
            questions={
                "est_sensible": Noul("Cet email contient-il une facture, document officiel, contrat, info bancaire, mot de passe ou message personnel important ?"),
                "categorie": Choice(
                    instructions="Sélectionnez la catégorie du message",
                    choices={
                        "spam": "Spam : publicité agressive, casino, démarchage non sollicité, arnaque",
                        "faible_interet": "Faible intérêt : newsletter, notification automatique, rappel d'agenda ancien, digest",
                        "important": "Important : facture, reçu, échange personnel ou professionnel, compte client",
                    },
                ),
            },
        )
        est_sensible = decision.est_sensible.answer
        categorie = decision.categorie.choice
        conf = decision.categorie.confidence
    except Exception:
        # En cas d'erreur ou d'incertitude : conservation par sécurité (fail-safe)
        est_sensible = True
        categorie = "important"
        conf = 1.0

    stats["total"] += 1

    # RÈGLES DE SÉCURITÉ STRICTES :
    # Si sensible ou important -> INTERDICTION DE SUPPRIMER
    if est_sensible or categorie == "important":
        stats["conserves_sensibles"] = stats.get("conserves_sensibles", 0) + 1
        print(f" 🛡️ [CONSERVÉ - IMPORTANT/SENSIBLE] De: {sender[:25]} | Date: {received_str[:10]} | Objet: {subj[:40]}")
        return

    # Si spam -> suppression
    if categorie == "spam":
        stats["spam"] += 1
        stats["deleted"] += 1
        if dry_run:
            print(f" ⚠️ [SIMULATION SUPPR SPAM ({conf*100:.0f}%)] De: {sender[:25]} | Date: {received_str[:10]} | Objet: {subj[:40]}")
        else:
            ok = await delete_message_graph(client_graph, token, msg["id"])
            st = "OK" if ok else "ERR"
            print(f" 🗑️ [SUPPRIMÉ SPAM - {st}] De: {sender[:25]} | Date: {received_str[:10]} | Objet: {subj[:40]}")
        return

    # Si faible intérêt (newsletter, rappel ancien, etc.) ET plus vieux que min_days_old -> suppression
    if categorie == "faible_interet" and age_days >= min_days_old:
        stats["faible_interet_vieux"] = stats.get("faible_interet_vieux", 0) + 1
        stats["deleted"] += 1
        if dry_run:
            print(f" 📦 [SIMULATION SUPPR VIEUX FAIBLE INTÉRÊT ({age_days}j)] De: {sender[:25]} | Date: {received_str[:10]} | Objet: {subj[:40]}")
        else:
            ok = await delete_message_graph(client_graph, token, msg["id"])
            st = "OK" if ok else "ERR"
            print(f" 🗑️ [SUPPRIMÉ VIEUX ({age_days}j) - {st}] De: {sender[:25]} | Date: {received_str[:10]} | Objet: {subj[:40]}")
        return

    # Faible intérêt mais récent (< 1 an) -> conservé
    stats["conserves_recents"] = stats.get("conserves_recents", 0) + 1
    print(f" ➡️ [CONSERVÉ - RÉCENT ({age_days}j)] De: {sender[:25]} | Date: {received_str[:10]} | Objet: {subj[:40]}")


async def main():
    parser = argparse.ArgumentParser(description="Nettoyage ultra-sécurisé des emails Outlook avec Foq")
    parser.add_argument("--limit", type=int, default=500, help="Nombre max d'emails à traiter (défaut: 500)")
    parser.add_argument("--days-old", type=int, default=365, help="Seuil d'ancienneté en jours (défaut: 365 = 1 an)")
    parser.add_argument("--apply", action="store_true", help="Exécuter réellement les suppressions vers la corbeille")

    args = parser.parse_args()
    dry_run = not args.apply

    load_env()
    token = get_token()

    engine = FoqEngine()
    if not engine.is_server_ready():
        print("[ERREUR] Le serveur Foq n'est pas actif sur http://127.0.0.1:8089.", flush=True)
        sys.exit(1)

    print("=" * 75)
    print(f"⚡ NETTOYAGE SÉCURISÉ FOQ <-> OUTLOOK ({'MODE RÉEL EFFECTIF' if not dry_run else 'MODE SIMULATION DRY-RUN'})")
    print(f"  - Critère de suppression 1 : SPAM non sollicité (pub agressive, casino)")
    print(f"  - Critère de suppression 2 : Faible intérêt & Ancienneté > {args.days_old} jours (1 an)")
    print(f"  - Bouclier de protection   : Mails sensibles, importants, factures, contrats STRICTEMENT CONSERVÉS")
    print(f"  - Limite d'analyse         : {args.limit if args.limit > 0 else 'Tout le dossier'}")
    print("=" * 75)

    stats = {
        "total": 0,
        "deleted": 0,
        "spam": 0,
        "faible_interet_vieux": 0,
        "conserves_sensibles": 0,
        "conserves_recents": 0,
    }
    t0 = time.time()

    cutoff_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=args.days_old)).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(timeout=30.0) as graph_client:
        next_url = (
            f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
            f"?$filter=receivedDateTime lt {cutoff_date}"
            f"&$select=id,subject,from,bodyPreview,receivedDateTime,categories"
            f"&$top=50"
        )

        processed = 0
        while next_url and (args.limit == 0 or processed < args.limit):
            try:
                token = get_token()
                resp = await graph_client.get(next_url, headers={"Authorization": f"Bearer {token}"})
            except Exception:
                await asyncio.sleep(2)
                continue

            if resp.status_code == 401:
                token = get_token()
                continue
            if resp.status_code != 200:
                print(f"[ERREUR Graph API] Code {resp.status_code}: {resp.text}")
                break

            data = resp.json()
            messages = data.get("value", [])
            if not messages:
                break

            batch_size = 4
            for i in range(0, len(messages), batch_size):
                chunk = messages[i : i + batch_size]
                if args.limit > 0 and processed + len(chunk) > args.limit:
                    chunk = chunk[: args.limit - processed]

                tasks = [
                    process_single_email(
                        engine=engine,
                        msg=msg,
                        client_graph=graph_client,
                        token=token,
                        stats=stats,
                        min_days_old=args.days_old,
                        dry_run=dry_run,
                    )
                    for msg in chunk
                ]
                await asyncio.gather(*tasks)
                processed += len(chunk)

                if processed % 50 == 0:
                    print(f"--- Progression : {processed}/{args.limit} emails traités ({stats['deleted']} mis en corbeille, {stats['conserves_sensibles']} protégés) ---")

                if args.limit > 0 and processed >= args.limit:
                    break

            next_url = data.get("@odata.nextLink")

    elapsed = time.time() - t0
    print("\n" + "=" * 75)
    print("BILAN DU TRAITEMENT EFFECTUÉ :")
    print(f"  - Total analysé                   : {stats['total']} emails en {elapsed:.1f}s")
    print(f"  - Mis en corbeille                : {stats['deleted']} emails")
    print(f"    * dont Spams                    : {stats['spam']}")
    print(f"    * dont Faible intérêt > 1 an    : {stats['faible_interet_vieux']}")
    print(f"  - STRICTEMENT CONSERVÉS           : {stats['conserves_sensibles'] + stats['conserves_recents']} emails")
    print(f"    * Protégés (Sensibles / Facture): {stats['conserves_sensibles']}")
    print(f"    * Conservés (Récents < 1 an)    : {stats['conserves_recents']}")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(main())
