"""
Official Command Line Interface (CLI) for Foq.
Available commands:
  foq serve        : Launch the local optimized System 1 server
  foq setup        : Download model (SHA-256 verified) and verify runtime
  foq benchmark    : Run the accuracy and latency benchmark
  foq inspect TEXT : Audit an input string against prompt injections
  foq demo         : Launch interactive System 1 decision demo
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
    """Launch the local Foq server."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cmd_file = os.path.join(base_dir, "start_foq_server.cmd")
    sh_file = os.path.join(base_dir, "start_foq_server.sh")

    if sys.platform == "win32" and os.path.exists(cmd_file):
        print(f"[*] Starting Foq server from: {cmd_file}")
        subprocess.run([cmd_file], shell=True)
    elif os.path.exists(sh_file):
        print(f"[*] Starting Foq server from: {sh_file}")
        subprocess.run(["bash", sh_file])
    else:
        print(f"[!] Server launcher script not found in: {base_dir}")


def cmd_benchmark(args):
    """Run full benchmark."""
    subprocess.run([sys.executable, "-m", "foq.bench"])


def cmd_inspect(args):
    """Inspect text in real time against threats."""
    text = " ".join(args.text)
    if not text.strip():
        print("[!] Error: No text provided to analyze.")
        return

    guard = FoqSecurityGuard()
    if not guard.engine.is_server_ready():
        print("[!] Foq server not running on http://127.0.0.1:8089.")
        return

    print(f"[*] Auditing input ({len(text)} characters)...")
    verdict = guard.inspect(text)
    status = "🟢 CLEAN" if verdict.is_safe else "🔴 THREAT DETECTED (BLOCKED)"
    print(f"\nVerdict     : {status}")
    print(f"Type        : {verdict.threat_type}")
    print(f"Confidence  : {verdict.confidence:.1%}")
    print(f"Latency     : {verdict.latency_ms:.1f} ms")
    print(f"Explanation : {verdict.reason}\n")


def cmd_demo(args):
    """Launch interactive demo."""
    subprocess.run([sys.executable, "-m", "foq.demo"])


def cmd_setup(args):
    """Prepare environment: model (SHA-256 verified), llama runtime, optional adapter."""
    import hashlib
    import shutil as _shutil
    import httpx as _httpx

    MODEL_URL = "https://huggingface.co/Yoedi/foq-reflex-8b-gguf/resolve/main/foq-reflex-8b-pq2_0.gguf"
    MODEL_SHA = "59a08216ee6065f7a8bfe2442d528065283f6f137af6f7fa4e0f0224f5d4909e"
    MODEL_SIZE = 2182184640
    ADAPTER_URL = "https://huggingface.co/Yoedi/foq-reflex-8b-gguf/resolve/main/foq_decision_8b.gguf"

    home = os.path.expanduser("~")
    dest_dir = os.path.join(home, ".models", "foq")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, "foq-reflex-8b-pq2_0.gguf")

    def sha256_file(path):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                h.update(chunk)
        return h.hexdigest()

    print("=" * 62)
    print("  FOQ SETUP — Environment Preparation")
    print("=" * 62)

    # 1. Decision model
    if os.path.exists(dest) and os.path.getsize(dest) == MODEL_SIZE:
        print("[1/3] Model already present — verifying hash...")
        if sha256_file(dest) == MODEL_SHA:
            print("      OK — valid hash, no download required.")
        else:
            print("      ! Hash mismatch — re-downloading.")
            os.remove(dest)
    if not os.path.exists(dest):
        print(f"[1/3] Downloading model (2.2 GB) from Hugging Face...")
        print(f"      {MODEL_URL}")
        tmp = dest + ".part"
        with _httpx.Client(timeout=None, follow_redirects=True) as client:
            with client.stream("GET", MODEL_URL) as resp:
                resp.raise_for_status()
                done = 0
                with open(tmp, "wb") as f:
                    for chunk in resp.iter_bytes(1 << 22):
                        f.write(chunk)
                        done += len(chunk)
                        if done % (200 << 20) < (1 << 22):
                            print(f"      {done / (1<<30):.1f} GB / {MODEL_SIZE / (1<<30):.1f} GB", flush=True)
        if done != MODEL_SIZE:
            os.remove(tmp)
            print("      [ERROR] Unexpected file size — download interrupted? Rerun foq setup.")
            return
        print("      Verifying SHA-256...")
        if sha256_file(tmp) != MODEL_SHA:
            os.remove(tmp)
            print("      [ERROR] Hash mismatch — corrupted file. Rerun foq setup.")
            return
        os.replace(tmp, dest)
        print("      OK — model installed and verified:", dest)

    # 2. Llama server — PQ2_0 format requires Foq llama.cpp build
    print("[2/3] Detecting inference runtime (llama-server)...")
    print("      Note: Foq weights use the ternary PQ2_0 format, supported")
    print("      exclusively by the Foq llama.cpp build. Official ggml-org builds")
    print("      reject the weights (unknown tensor type 142 error).")

    RELEASES_URL = "https://github.com/yohanargentina-oss/Foq/releases"
    foq_llama_dir = os.path.join(home, ".local", "bin", "foq-llama")

    def _llama_banner(exe):
        try:
            r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
            return r.stdout + r.stderr
        except Exception:
            return ""

    candidates = []
    if os.environ.get("LLAMA_SERVER"):
        candidates.append(os.environ["LLAMA_SERVER"])
    for name in ("llama-server.exe", "llama-server"):
        p = os.path.join(foq_llama_dir, name)
        if os.path.exists(p):
            candidates.append(p)
            break
    candidates.append(_shutil.which("llama-server"))
    llama = next((c for c in candidates if c), None)

    if llama:
        print("      Found —", llama)
        banner = _llama_banner(llama)
        is_foq_build = (
            llama.lower().startswith(foq_llama_dir.lower())
            or "pq2_0" in banner.lower()
            or "foq" in banner.lower()
            or "build 10685" in banner
            or "0.2.0-dev" in banner
        )
        if is_foq_build:
            print("      OK — PQ2_0 compatible Foq build.")
        else:
            if banner.strip():
                print("      [!] Non-Foq llama.cpp build detected (official ggml-org or")
                print("          unknown): cannot load PQ2_0 weights")
                print("          ('invalid ggml type 142' error at load).")
            else:
                print("      [!] Unable to read --version banner — unverified build:")
                print("          if server fails to load weights, it is not a Foq build.")
            print("          Install the Foq build:")
            print(f"          {RELEASES_URL}  ->  ~/.local/bin/foq-llama/")
    else:
        print("      [TODO] llama-server not found.")
        print("      Install the Foq llama.cpp build (PQ2_0 support) from:")
        print(f"          {RELEASES_URL}")
        print("      then unpack it to ~/.local/bin/foq-llama/.")
        print("      Foq launchers will locate it automatically (or via LLAMA_SERVER env var).")

    # 3. Decision adapter (optional)
    print("[3/3] LoRA decision adapter (optional, +10.7 pts measured)...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    adapter_local = os.path.join(base_dir, "adapters", "foq_decision_8b", "foq_decision_8b.gguf")
    if os.path.exists(adapter_local):
        print("      OK — already present:", adapter_local)
    else:
        try:
            r = _httpx.head(ADAPTER_URL, follow_redirects=True, timeout=15)
            if r.status_code == 200:
                print(f"      Downloading (61 MB)...")
                with _httpx.Client(timeout=None, follow_redirects=True) as client:
                    with client.stream("GET", ADAPTER_URL) as resp:
                        resp.raise_for_status()
                        os.makedirs(os.path.dirname(adapter_local), exist_ok=True)
                        with open(adapter_local + ".part", "wb") as f:
                            for chunk in resp.iter_bytes(1 << 20):
                                f.write(chunk)
                os.replace(adapter_local + ".part", adapter_local)
                print("      OK —", adapter_local)
            else:
                print(f"      Unavailable (release pending) — Foq operates without it,")
                print("      adapter will be downloadable from repository Releases page.")
        except Exception:
            print("      Download unavailable — Foq operates without adapter;")
            print("      launcher loads it automatically if present.")

    print("\n[✓] Setup complete. Next step: start_foq_server.cmd (or .sh), then: foq demo")


def main():
    parser = argparse.ArgumentParser(
        prog="foq",
        description="⚡ Foq - High-Performance System 1 Decision Engine (100% Local)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # foq serve
    parser_serve = subparsers.add_parser("serve", help="Start the local Foq inference server")
    parser_serve.set_defaults(func=cmd_serve)

    # foq setup
    parser_setup = subparsers.add_parser("setup", help="Download model (SHA-256 verified) and verify runtime")
    parser_setup.set_defaults(func=cmd_setup)

    # foq benchmark
    parser_bench = subparsers.add_parser("benchmark", help="Run latency and accuracy benchmark")
    parser_bench.set_defaults(func=cmd_benchmark)

    # foq inspect
    parser_inspect = subparsers.add_parser("inspect", help="Audit text in real time against injections")
    parser_inspect.add_argument("text", nargs="+", help="Text or payload to analyze")
    parser_inspect.set_defaults(func=cmd_inspect)

    # foq demo
    parser_demo = subparsers.add_parser("demo", help="Launch interactive decision demo")
    parser_demo.set_defaults(func=cmd_demo)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
