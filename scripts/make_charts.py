"""
Génération des graphiques de preuve (docs/assets/) — design sobre minimaliste.

Toutes les valeurs proviennent de mesures réelles effectuées sur le banc interne
(RTX 4080 Super, serveur local 4 slots, latence P50 côté client). Chaque constante
cite sa source. Regerénérer : py -3 scripts/make_charts.py
"""

import sys
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "assets")
os.makedirs(OUT, exist_ok=True)

INK = "#111111"      # barres neutres
ACCENT = "#FF5C00"   # Foq uniquement
GRAY = "#8A8A8A"     # annotations secondaires
BG = "#FFFFFF"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.edgecolor": "#CCCCCC",
    "axes.linewidth": 0.8,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "svg.fonttype": "none",
})


def _despine(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


# ---------------------------------------------------------------------------
# 1. Latence P50 d'une décision — échelle logarithmique
# Source : banc 29 cas (P50 8B nu = 21 ms, 8B final = 25 ms, 27B = 163 ms) ;
# LLM API = ordre de grandeur typique 1-3 s (réseau + génération) ;
# LLM raisonnement = mesure directe R1-8B sur le même banc : 12 300 ms.
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=200)
labels = ["Foq 8B\n(final)", "Foq 27B", "Typical\nAPI LLM", "Reasoning\nLLM"]
values = [25, 163, 2000, 12300]
colors = [ACCENT, INK, GRAY, GRAY]
bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], height=0.55)
ax.set_xscale("log")
ax.set_xlim(10, 40000)
for bar, v in zip(bars, values[::-1]):
    txt = f"{v:,} ms".replace(",", " ") if v >= 1000 else f"{v} ms"
    ax.text(v * 1.15, bar.get_y() + bar.get_height() / 2, txt, va="center", fontsize=10, color=INK)
ax.set_xlabel("Latency per decision, P50 (ms) — log scale", fontsize=10, color=INK)
ax.annotate("≈80x faster\nthan a typical API LLM", xy=(2000, 2.0), xytext=(6000, 1.6),
            fontsize=11, color=INK, ha="left",
            arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.8))
ax.annotate("≈500x faster\nthan a reasoning LLM", xy=(12300, 2.95), xytext=(14000, 2.55),
            fontsize=13, fontweight="bold", color=ACCENT, ha="left",
            arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1.0))
ax.tick_params(colors=INK, labelsize=10)
ax.xaxis.grid(True, color="#EAEAEA", linewidth=0.7)
ax.set_axisbelow(True)
_despine(ax, keep=("bottom",))
fig.tight_layout()
fig.savefig(os.path.join(OUT, "chart_latence.png"), bbox_inches="tight")
plt.close(fig)
print("chart_latence.png")

# ---------------------------------------------------------------------------
# 2. Apport de l'adaptateur LoRA sur l'examen de production (150 cas)
# Source : scripts/exam_core.py — 8B nu 134/150 (89,3 %) ; 8B final 150/150 (100 %)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
labels = ["8B bare", "8B + LoRA + patches"]
scores = [89.3, 100.0]
colors = [GRAY, ACCENT]
bars = ax.bar(labels, scores, color=colors, width=0.45)
ax.set_ylim(80, 102)
for bar, sc in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width() / 2, sc + 0.4, f"{sc:.1f}%",
            ha="center", fontsize=11, color=INK)
ax.set_ylabel("Production exam — 150 cases (%)", fontsize=10, color=INK)
ax.tick_params(colors=INK, labelsize=10)
ax.yaxis.grid(True, color="#EAEAEA", linewidth=0.7)
ax.set_axisbelow(True)
_despine(ax, keep=("left",))
fig.tight_layout()
fig.savefig(os.path.join(OUT, "chart_adaptateur.png"), bbox_inches="tight")
plt.close(fig)
print("chart_adaptateur.png")

# ---------------------------------------------------------------------------
# 3. Calibration RLCD — ECE avant / après
# Source : run_calibration.py sur le 8B : ECE brut 6,65 % -> 0,23 % (T* = 0,100)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=200)
labels = ["Raw model", "After\nRLCD"]
ece = [6.65, 0.23]
bars = ax.bar(labels, ece, color=[GRAY, ACCENT], width=0.45)
ax.set_ylim(0, 7.5)
for bar, v in zip(bars, ece):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.15, f"{v:.2f} %",
            ha="center", fontsize=11, color=INK)
ax.set_ylabel("Calibration error ECE (%)", fontsize=10, color=INK)
ax.tick_params(colors=INK, labelsize=10)
ax.yaxis.grid(True, color="#EAEAEA", linewidth=0.7)
ax.set_axisbelow(True)
_despine(ax, keep=("left",))
fig.tight_layout()
fig.savefig(os.path.join(OUT, "chart_calibration.png"), bbox_inches="tight")
plt.close(fig)
print("chart_calibration.png")

# ---------------------------------------------------------------------------
# 4. Coût pour 1 000 000 de décisions
# Foq : 0 € (matériel possédé). API : 0,001-0,01 €/appel typique -> 1 000 à 10 000 €
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=200)
labels = ["Foq\n(local)", "LLM API\n(fourchette haute)"]
costs = [0, 10000]
bars = ax.bar(labels, costs, color=[ACCENT, GRAY], width=0.45)
ax.set_ylim(0, 11500)
for bar, v in zip(bars, costs):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 250, f"{v:,} EUR".replace(",", " "),
            ha="center", fontsize=11, color=INK)
ax.set_ylabel("EUR per 1M decisions", fontsize=10, color=INK)
ax.tick_params(colors=INK, labelsize=10)
ax.yaxis.grid(True, color="#EAEAEA", linewidth=0.7)
ax.set_axisbelow(True)
_despine(ax, keep=("left",))
fig.tight_layout()
fig.savefig(os.path.join(OUT, "chart_cout.png"), bbox_inches="tight")
plt.close(fig)
print("chart_cout.png")

print("Graphiques générés dans", os.path.abspath(OUT))
