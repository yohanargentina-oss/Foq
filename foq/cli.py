"""
Interface en ligne de commande (CLI) officielle pour Foq.
Commandes disponibles :
  foq serve        : Lance le serveur local Système 1 optimisé
  foq benchmark    : Exécute le banc d'épreuve de précision et latence
  foq inspect TEXT : Audite une chaîne de caractères contre les injections
  foq demo         : Lance la démonstration interactive des primitives
"""

import sys
import os
import argparse
import subprocess

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .engine import FoqEngine
from .security import FoqSecurityGuard


def cmd_serve(args):
    """Lance le serveur local Foq."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cmd_file = os.path.join(base_dir, "start_foq_server.cmd")
    sh_file = os.path.join(base_dir, "start_foq_server.sh")

    if sys.platform == "win32" and os.path.exists(cmd_file):
        print(f"[*] Démarrage du serveur Foq depuis : {cmd_file}")
        subprocess.run([cmd_file], shell=True)
    elif os.path.exists(sh_file):
        print(f"[*] Démarrage du serveur Foq depuis : {sh_file}")
        subprocess.run(["bash", sh_file])
    else:
        print(f"[!] Fichier de démarrage introuvable dans : {base_dir}")


def cmd_benchmark(args):
    """Lance le banc d'épreuve complet."""
    subprocess.run([sys.executable, "-m", "foq.bench"])


def cmd_inspect(args):
    """Inspecte un texte en direct contre les menaces."""
    text = " ".join(args.text)
    if not text.strip():
        print("[!] Erreur : Aucun texte fourni à analyser.")
        return

    guard = FoqSecurityGuard()
    if not guard.engine.is_server_ready():
        print("[!] Serveur Foq non démarré sur http://127.0.0.1:8089.")
        return

    print(f"[*] Audit en cours ({len(text)} caractères)...")
    verdict = guard.inspect(text)
    status = "🟢 SAIN" if verdict.is_safe else "🔴 MENACE DÉTECTÉE (BLOQUÉ)"
    print(f"\nVerdict     : {status}")
    print(f"Type        : {verdict.threat_type}")
    print(f"Confiance   : {verdict.confidence:.1%}")
    print(f"Latence     : {verdict.latency_ms:.1f} ms")
    print(f"Explication : {verdict.reason}\n")


def cmd_demo(args):
    """Lance la démo interactive."""
    subprocess.run([sys.executable, "-m", "foq.demo"])


def cmd_setup(args):
    """Prépare la machine : modèle (SHA-256 vérifié), serveur llama, adaptateur optionnel."""
    import hashlib
    import shutil as _shutil
    import httpx as _httpx

    MODELE_URL = "https://huggingface.co/Yoedi/foq-reflex-8b-gguf/resolve/main/foq-reflex-8b-pq2_0.gguf"
    MODELE_SHA = "59a08216ee6065f7a8bfe2442d528065283f6f137af6f7fa4e0f0224f5d4909e"
    MODELE_TAILLE = 2182184640
    ADAPTER_URL = "https://huggingface.co/Yoedi/foq-reflex-8b-gguf/resolve/main/foq_decision_8b.gguf"

    home = os.path.expanduser("~")
    dest_dir = os.path.join(home, ".models", "foq")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "foq-reflex-8b-pq2_0.gguf")

    def sha256_fichier(chemin):
        h = hashlib.sha256()
        with open(chemin, "rb") as f:
            for bloc in iter(lambda: f.read(1 << 22), b""):
                h.update(bloc)
        return h.hexdigest()

    print("=" * 62)
    print("  FOQ SETUP — préparation de la machine")
    print("=" * 62)

    # 1. Modèle de décision
    if os.path.exists(dest) and os.path.getsize(dest) == MODELE_TAILLE:
        print("[1/3] Modèle déjà présent — vérification du hash...")
        if sha256_fichier(dest) == MODELE_SHA:
            print("      OK — hash conforme, aucun téléchargement nécessaire.")
        else:
            print("      ! Hash non conforme — re-téléchargement.")
            os.remove(dest)
    if not os.path.exists(dest):
        print(f"[1/3] Téléchargement du modèle (2,2 Go) depuis Hugging Face...")
        print(f"      {MODELE_URL}")
        tempo = dest + ".part"
        with _httpx.Client(timeout=None, follow_redirects=True) as client:
            with client.stream("GET", MODELE_URL) as resp:
                resp.raise_for_status()
                fait = 0
                with open(tempo, "wb") as f:
                    for bloc in resp.iter_bytes(1 << 22):
                        f.write(bloc)
                        fait += len(bloc)
                        if fait % (200 << 20) < (1 << 22):
                            print(f"      {fait / (1<<30):.1f} Go / {MODELE_TAILLE / (1<<30):.1f} Go", flush=True)
        if fait != MODELE_TAILLE:
            os.remove(tempo)
            print("      [ERREUR] Taille inattendue — téléchargement interrompu ? Relancez foq setup.")
            return
        print("      Vérification SHA-256...")
        if sha256_fichier(tempo) != MODELE_SHA:
            os.remove(tempo)
            print("      [ERREUR] Hash non conforme — fichier corrompu. Relancez foq setup.")
            return
        os.replace(tempo, dest)
        print("      OK — modèle installé et vérifié :", dest)

    # 2. Serveur llama — le format PQ2_0 exige la build llama.cpp Foq
    print("[2/3] Détection du serveur d'inférence (llama-server)...")
    print("      NB : les poids Foq utilisent le format ternaire PQ2_0, lisible")
    print("      uniquement par la build llama.cpp Foq. Les builds officielles")
    print("      ggml-org rejettent le fichier (type de tenseur inconnu).")

    RELEASES_URL = "https://github.com/yohanargentina-oss/Foq/releases"
    foq_llama_dir = os.path.join(home, ".local", "bin", "foq-llama")

    def _banniere_llama(exe):
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
            return r.stdout + r.stderr
        except Exception:
            return ""

    candidats = []
    if os.environ.get("LLAMA_SERVER"):
        candidats.append(os.environ["LLAMA_SERVER"])
    for nom in ("llama-server.exe", "llama-server"):
        p = os.path.join(foq_llama_dir, nom)
        if os.path.exists(p):
            candidats.append(p)
            break
    candidats.append(_shutil.which("llama-server"))
    llama = next((c for c in candidats if c), None)

    if llama:
        print("      Trouvé —", llama)
        banniere = _banniere_llama(llama)
        # Une build est reconnue Foq par son emplacement d'installation, une
        # mention PQ2_0/Foq dans sa bannière, la build de référence 10685, ou
        # la ligne de version du fork (« 0.2.0-dev » ; l'officiel ggml-org est
        # sur « 0.4.x-dev »). Tout le reste est prévenu : rejet garanti du
        # type de tenseur 142.
        est_build_foq = (
            llama.lower().startswith(foq_llama_dir.lower())
            or "pq2_0" in banniere.lower()
            or "foq" in banniere.lower()
            or "build 10685" in banniere
            or "0.2.0-dev" in banniere
        )
        if est_build_foq:
            print("      OK — build Foq compatible PQ2_0.")
        else:
            if banniere.strip():
                print("      [!] Build llama.cpp NON Foq détectée (officielle ggml-org ou")
                print("          inconnue) : elle ne peut PAS charger le format PQ2_0")
                print("          (erreur « invalid ggml type 142 » au chargement).")
            else:
                print("      [!] Bannière --version illisible — build non identifiable :")
                print("          si le serveur refuse le modèle, c'est qu'elle n'est pas Foq.")
            print("          Installez la build Foq :")
            print(f"          {RELEASES_URL}  ->  ~/.local/bin/foq-llama/")
    else:
        print("      [À FAIRE] llama-server introuvable.")
        print("      Installez la build llama.cpp Foq (support PQ2_0) depuis :")
        print(f"          {RELEASES_URL}")
        print("      puis décompressez-la dans ~/.local/bin/foq-llama/.")
        print("      Les lanceurs Foq la trouveront là (ou via la variable LLAMA_SERVER).")

    # 3. Adaptateur décision (optionnel)
    print("[3/3] Adaptateur LoRA décision (optionnel, +10,7 pts mesurés)...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    adapter_local = os.path.join(base_dir, "adapters", "foq_decision_8b", "foq_decision_8b.gguf")
    if os.path.exists(adapter_local):
        print("      OK — déjà présent :", adapter_local)
    else:
        try:
            r = _httpx.head(ADAPTER_URL, follow_redirects=True, timeout=15)
            if r.status_code == 200:
                print(f"      Téléchargement (61 Mo)...")
                with _httpx.Client(timeout=None, follow_redirects=True) as client:
                    with client.stream("GET", ADAPTER_URL) as resp:
                        resp.raise_for_status()
                        os.makedirs(os.path.dirname(adapter_local), exist_ok=True)
                        with open(adapter_local + ".part", "wb") as f:
                            for bloc in resp.iter_bytes(1 << 20):
                                f.write(bloc)
                os.replace(adapter_local + ".part", adapter_local)
                print("      OK —", adapter_local)
            else:
                print(f"      Indisponible (release non publiée) — Foq fonctionne sans,")
                print("      l'adaptateur sera récupérable depuis la page Releases du dépôt.")
        except Exception:
            print("      Téléchargement impossible (dépôt privé ou hors ligne) — Foq")
            print("      fonctionne sans adaptateur ; le lanceur le chargera s'il est présent.")

    print("\n[✓] Setup terminé. Prochaine étape : start_foq_server.sh (ou .cmd), puis : foq demo")


def main():
    parser = argparse.ArgumentParser(
        prog="foq",
        description="⚡ Foq - Moteur de Décision Système 1 Haute Performance (100% Local)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # foq serve
    parser_serve = subparsers.add_parser("serve", help="Démarrer le serveur d'inférence Foq")
    parser_serve.set_defaults(func=cmd_serve)

    # foq setup
    parser_setup = subparsers.add_parser("setup", help="Télécharger le modèle (SHA-256 vérifié) et préparer la machine")
    parser_setup.set_defaults(func=cmd_setup)

    # foq benchmark
    parser_bench = subparsers.add_parser("benchmark", help="Lancer le benchmark de performance")
    parser_bench.set_defaults(func=cmd_benchmark)

    # foq inspect
    parser_inspect = subparsers.add_parser("inspect", help="Auditer un texte en temps réel")
    parser_inspect.add_argument("text", nargs="+", help="Texte ou payload à analyser")
    parser_inspect.set_defaults(func=cmd_inspect)

    # foq demo
    parser_demo = subparsers.add_parser("demo", help="Lancer la démonstration interactive")
    parser_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
