"""
Script de Triage Massif Haute Performance Foq <-> Outlook.
Traite les emails non lus par paquets concurrents (4 slots GPU).
"""

import os
import sys
import time
import asyncio
import warnings
from pathlib import Path
from typing import Dict, Any, List

warnings.filterwarnings("ignore")

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
import msal
from foq import FoqEngine, Choice

CACHE_FILE = Path(__file__).parent.parent / "data" / "outlook_token_cache.bin"
ENV_FILE = Path(__file__).parent.parent / ".env"
SCOPES = ["https://graph.microsoft.com/Mail.ReadWrite", "https://graph.microsoft.com/User.Read"]

CATEGORY_MAP = {
    "urgent": "Rouge",
    "a_traiter": "Jaune",
    "archive": "Bleu",
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


async def patch_message_graph(client: httpx.AsyncClient, token: str, msg_id: str, action: str):
    """Met à jour l'email dans Outlook (Catégorie + Statut lu/non lu)."""
    mark_read = action in ["archive", "spam"]
    url = f"https://graph.microsoft.com/v1.0/me/messages/{msg_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "categories": [CATEGORY_MAP.get(action, "Vert")],
        "isRead": mark_read,
    }
    try:
        await client.patch(url, headers=headers, json=payload, timeout=15.0)
    except Exception:
        pass


async def classify_single_email(
    engine: FoqEngine,
    msg: Dict[str, Any],
    client_graph: httpx.AsyncClient,
    token: str,
    choice_schema: Choice,
    stats: Dict[str, int],
) -> str:
    """Classifie un email avec Foq en asynchrone et met à jour Outlook."""
    sender = msg.get("from", {}).get("emailAddress", {}).get("address", "")
    subj = msg.get("subject", "Sans objet")
    preview = msg.get("bodyPreview", "")
    state_text = f"Expéditeur: {sender}\nObjet: {subj}\nExtrait: {preview[:400]}"

    try:
        raw_res = await engine.decide_async(state_text, choice_schema)
        parsed = choice_schema.parse_result(raw_res)
        action = parsed.choice
    except Exception:
        action = "archive"

    stats[action] = stats.get(action, 0) + 1
    stats["total_done"] += 1

    await patch_message_graph(client_graph, token, msg["id"], action)
    return action


async def run_bulk(limit: int = 0):
    load_env()
    token = get_token()

    engine = FoqEngine()
    if not engine.is_server_ready():
        print("[ERREUR] Le serveur Foq n'est pas actif.", flush=True)
        sys.exit(1)

    choice_schema = Choice(
        instructions="Classer cet email",
        choices={
            "urgent": "Urgent : nécessite une intervention rapide",
            "a_traiter": "À traiter : email nécessitant une réponse ultérieure",
            "archive": "Archive : notification, newsletter ou reçu",
            "spam": "Spam : publicité non sollicitée ou démarchage",
        },
    )

    stats = {"urgent": 0, "a_traiter": 0, "archive": 0, "spam": 0, "total_done": 0}
    t0 = time.time()

    async with httpx.AsyncClient(timeout=30.0) as graph_client:
        info_resp = await graph_client.get(
            "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox",
            headers={"Authorization": f"Bearer {token}"},
        )
        total_unread = info_resp.json().get("unreadItemCount", 0)
        target_count = min(total_unread, limit) if limit > 0 else total_unread

        print(f"Total non lus restants : {total_unread}", flush=True)
        print(f"Cible : {target_count} emails", flush=True)
        print("-" * 65, flush=True)

        processed = 0
        next_url = (
            f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages"
            f"?$filter=isRead eq false&$select=id,subject,from,bodyPreview,categories&$top=50"
        )

        while next_url and (limit == 0 or processed < limit):
            try:
                token = get_token()
            except Exception:
                pass

            try:
                resp = await graph_client.get(next_url, headers={"Authorization": f"Bearer {token}"})
            except Exception as e:
                await asyncio.sleep(3)
                continue

            if resp.status_code == 401:
                token = get_token()
                continue

            if resp.status_code != 200:
                break

            data = resp.json()
            raw_messages = data.get("value", [])
            if not raw_messages:
                break

            messages = [m for m in raw_messages if not m.get("categories")]
            if not messages:
                next_url = data.get("@odata.nextLink")
                continue

            batch_size = 4
            for i in range(0, len(messages), batch_size):
                chunk = messages[i : i + batch_size]
                if limit > 0 and processed + len(chunk) > limit:
                    chunk = chunk[: limit - processed]

                tasks = [
                    classify_single_email(engine, msg, graph_client, token, choice_schema, stats)
                    for msg in chunk
                ]
                await asyncio.gather(*tasks)
                processed += len(chunk)

                elapsed = time.time() - t0
                speed = processed / elapsed if elapsed > 0 else 0
                pct = (processed / target_count * 100) if target_count > 0 else 0

                msg_line = (
                    f"Progression : [{processed}/{target_count}] {pct:.1f}% | "
                    f"Spam: {stats['spam']} | Archive: {stats['archive']} | "
                    f"A traiter: {stats['a_traiter']} | Urgent: {stats['urgent']} | "
                    f"{speed:.1f} mails/s"
                )
                if processed % 20 == 0 or processed == target_count:
                    print(msg_line, flush=True)
                else:
                    print(f"\r{msg_line}", end="", flush=True)

                if limit > 0 and processed >= limit:
                    break

            next_url = data.get("@odata.nextLink")

    print("\n" + "=" * 65, flush=True)
    print("TRI TERMINE !", flush=True)
    print(f"Total traites : {stats['total_done']} emails en {time.time() - t0:.1f}s")
    print(f"  - Spams     : {stats['spam']}")
    print(f"  - Archives  : {stats['archive']}")
    print(f"  - A traiter : {stats['a_traiter']}")
    print(f"  - Urgents   : {stats['urgent']}")
    print("=" * 65, flush=True)


if __name__ == "__main__":
    count_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    asyncio.run(run_bulk(count_limit))
