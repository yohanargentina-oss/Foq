"""
Analyse de la politique d'abstention (needs_review) sur 500 cas aveugles appariés.

Pour chaque seuil de confiance s :
  - autonomes : cas où conf(8B) >= s → réponse 8B
  - revues    : cas où conf(8B) <  s → montée au 27B (résultat mesuré du 27B sur CE cas)
  - justesse autonome, taux de revue, justesse cascade, latence moyenne pondérée.

Sortie : tableau + docs/assets/data_review_policy.json + graphique chart_review.png
"""

import sys
import os
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "docs", "assets")

d8 = json.load(open(os.path.join(ASSETS, "data_cases_8b.json"), encoding="utf-8"))
d27 = json.load(open(os.path.join(ASSETS, "data_cases_27b.json"), encoding="utf-8"))

p27 = {c["id"]: c for c in d27["cases"]}
paires = []
for c in d8["cases"]:
    o = p27.get(c["id"])
    if o:
        paires.append((c, o))
print(f"[*] {len(paires)} cas appariés (mêmes 500, mêmes ordres d'options).")

LAT8 = d8["latency_p50_ms"]     # ~42 ms
LAT27 = d27["latency_p50_ms"]   # ~242 ms

# Diagnostic : la confiance sépare-t-elle juste et faux ?
bons = [c["confidence"] for c, o in paires if c["correct"]]
faux = [c["confidence"] for c, o in paires if not c["correct"]]
conf_bin = [(c["confidence"], c["correct"]) for c, o in paires]
print(f"[*] Confiance moyenne : justes {sum(bons)/len(bons):.3f} vs faux {sum(faux)/len(faux):.3f}")

resultats = []
for seuil in [0.0, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.92, 0.95, 0.97, 0.99]:
    aut = [(c, o) for c, o in paires if c["confidence"] >= seuil]
    rev = [(c, o) for c, o in paires if c["confidence"] < seuil]
    if not aut:
        continue
    aut_ok = sum(1 for c, o in aut if c["correct"])
    cas_ok_aut = aut_ok
    cas_ok_rev = sum(1 for c, o in rev if o["correct"])
    cascade_ok = cas_ok_aut + cas_ok_rev
    n = len(paires)
    lat_moy = (len(aut) * LAT8 + len(rev) * LAT27) / n
    resultats.append({
        "seuil": seuil,
        "taux_autonome_pct": round(len(aut) / n * 100, 1),
        "taux_revue_pct": round(len(rev) / n * 100, 1),
        "justesse_autonome_pct": round(aut_ok / len(aut) * 100, 1) if aut else 0.0,
        "justesse_cascade_pct": round(cascade_ok / n * 100, 1),
        "latence_moyenne_ms": round(lat_moy),
    })

print("\nSeuil | Autonome | Revue | Just. autonome | Just. CASCADE | Latence moy.")
for r in resultats:
    print(f"{r['seuil']:.2f}  | {r['taux_autonome_pct']:5.1f} % | {r['taux_revue_pct']:4.1f} % | "
          f"{r['justesse_autonome_pct']:5.1f} %      | {r['justesse_cascade_pct']:5.1f} %      | {r['latence_moyenne_ms']} ms")

base27 = d27["score_pct"]
meilleur = max(resultats, key=lambda r: (r["justesse_cascade_pct"], -r["latence_moyenne_ms"]))
print(f"\n[*] Référence 27B seul : {base27} % à {LAT27:.0f} ms")
print(f"[*] Meilleure cascade : seuil {meilleur['seuil']} → {meilleur['justesse_cascade_pct']} % "
      f"à {meilleur['latence_moyenne_ms']} ms moyens ({meilleur['taux_revue_pct']} % en revue)")

with open(os.path.join(ASSETS, "data_review_policy.json"), "w", encoding="utf-8") as f:
    json.dump({"base_27b_pct": base27, "meilleur": meilleur, "courbe": resultats}, f, ensure_ascii=False, indent=2)
print("[+] data_review_policy.json écrit")

# Graphique : courbe cascade vs 27B seul
INK, ACCENT, GRAY = "#111111", "#FF5C00", "#8A8A8A"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#CCCCCC", "axes.linewidth": 0.8,
                     "figure.facecolor": "white", "axes.facecolor": "white"})
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200)
seuils = [r["seuil"] for r in resultats if r["seuil"] > 0]
casc = [r["justesse_cascade_pct"] for r in resultats if r["seuil"] > 0]
autn = [r["justesse_autonome_pct"] for r in resultats if r["seuil"] > 0]
rev = [r["taux_revue_pct"] for r in resultats if r["seuil"] > 0]
ax.plot(seuils, casc, color=ACCENT, lw=2.2, marker="o", ms=4, label="Cascade 8B→27B (needs_review)")
ax.plot(seuils, autn, color=GRAY, lw=1.4, marker=".", label="8B autonomous only")
ax.axhline(base27, color=INK, lw=1.2, ls="--", label=f"27B alone ({base27:.0f}%)")
ax.set_xlabel("Confidence threshold for needs_review", fontsize=10, color=INK)
ax.set_ylabel("Accuracy on 500 blind cases (%)", fontsize=10, color=INK)
ax2 = ax.twinx()
ax2.plot(seuils, rev, color="#BBBBBB", lw=1.0, ls=":", label="% escalated (right)")
ax2.set_ylabel("% escalated to 27B", fontsize=9, color=GRAY)
ax.tick_params(colors=INK, labelsize=10)
ax.grid(True, color="#EAEAEA", linewidth=0.7)
ax.set_axisbelow(True)
for side in ("top",):
    ax.spines[side].set_visible(False); ax2.spines[side].set_visible(False)
ax.legend(loc="lower left", frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(ASSETS, "chart_review.png"), bbox_inches="tight")
print("[+] chart_review.png")
