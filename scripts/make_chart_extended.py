"""
Graphique du bench étendu (500 cas adversariaux jamais entraînés) :
Foq 8B réflexe vs Foq 27B juge, par catégorie. Données : docs/assets/data_extended*.json.
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
OUT = os.path.join(HERE, "..", "docs", "assets")

d8 = json.load(open(os.path.join(OUT, "data_extended.json"), encoding="utf-8"))
d27 = json.load(open(os.path.join(OUT, "data_extended_27b.json"), encoding="utf-8"))

CAT_EN = {
    "course_position": "Overtaking / rank",
    "raisonnement_spatial": "Spatial reasoning",
    "enigme_linguistique": "Language riddles",
    "sens_commun": "Common sense",
    "maths_contre_intuitives": "Counter-intuitive math",
    "negations_multiples": "Multiple negations",
    "physiologie_contre_intuitive": "Counter-intuitive science",
    "raisonnement_temporel": "Temporal reasoning",
    "causalite_fallacie": "Causality fallacies",
    "securite_info": "IT security",
    "sentiment": "Sentiment",
    "routage": "Ticket routing",
    "triage": "Urgency triage",
}

cats = sorted(d8["per_category"])
vals8 = [d8["per_category"][c]["correct"] / d8["per_category"][c]["total"] * 100 for c in cats]
vals27 = [d27["per_category"][c]["correct"] / d27["per_category"][c]["total"] * 100 for c in cats]

ordre = sorted(range(len(cats)), key=lambda i: vals27[i])
cats = [cats[i] for i in ordre]
vals8 = [vals8[i] for i in ordre]
vals27 = [vals27[i] for i in ordre]

INK = "#111111"
ACCENT = "#FF5C00"
GRAY = "#8A8A8A"

plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#CCCCCC", "axes.linewidth": 0.8,
                     "figure.facecolor": "white", "axes.facecolor": "white"})

fig, ax = plt.subplots(figsize=(9, 7), dpi=200)
y = range(len(cats))
h = 0.38
b1 = ax.barh([i + h/2 for i in y], vals8, height=h, color=ACCENT, label="Foq 8B reflex (40 ms)")
b2 = ax.barh([i - h/2 for i in y], vals27, height=h, color=INK, label="Foq 27B judge (242 ms)")
ax.set_yticks(list(y))
ax.set_yticklabels([CAT_EN.get(c, c) for c in cats], fontsize=10)
ax.set_xlim(0, 108)
ax.set_xlabel("Accuracy on 500 blind adversarial cases (%) — never seen in training", fontsize=10, color=INK)
for bars, vals in ((b1, vals8), (b2, vals27)):
    for bar, v in zip(bars, vals):
        ax.text(v + 1.2, bar.get_y() + bar.get_height()/2, f"{v:.0f}", va="center", fontsize=9, color=INK)
ax.axvline(d8["score_pct"], color=ACCENT, lw=1, ls=":")
ax.axvline(d27["score_pct"], color=INK, lw=1, ls=":")
ax.text(d8["score_pct"]+0.8, len(cats)-0.1, f"8B overall {d8['score_pct']:.0f}%", fontsize=9, color=ACCENT)
ax.text(d27["score_pct"]+0.8, len(cats)-0.7, f"27B overall {d27['score_pct']:.0f}%", fontsize=9, color=INK)
ax.xaxis.grid(True, color="#EAEAEA", linewidth=0.7)
ax.set_axisbelow(True)
for side in ("top", "right", "left"):
    ax.spines[side].set_visible(False)
ax.legend(loc="lower right", frameon=False, fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "chart_extended.png"), bbox_inches="tight")
print("chart_extended.png OK")
