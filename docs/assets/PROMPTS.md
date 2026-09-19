# 🎨 Prompts de génération visuelle (Flow & équivalents)

Design system : fond blanc pur, sans-serif géométrique, un seul accent **#FF5C00**
(réservé à Foq), gris #8A8A8A pour les concurrents, marges généreuses, zéro décoration.

Règle d'or : chaque chiffre est écrit dans le prompt. Après génération, vérifier
chaque valeur contre `scripts/make_charts.py` — en cas d'écart, le PNG scripté
(`docs/assets/chart_*.png`) fait foi.

---

## Graphique 1 — Latence (le plus impactant)

```
Minimalist white-background horizontal bar chart, Swiss editorial style, thin gray grid.
Four horizontal bars with these EXACT values and labels, left side labels in clean 
geometric sans-serif:
- "Foq 8B (final)" : bar in vivid orange #FF5C00, value "25 ms"
- "Foq 27B" : bar in near-black, value "163 ms"
- "LLM API (typique)" : bar in gray #8A8A8A, value "2 000 ms"
- "LLM raisonnement" : bar in gray #8A8A8A, value "12 300 ms"
Each value printed at the end of its bar in black. Log-scale feel: each bar roughly 
8x shorter than the next. Title above: "Latence d'une décision (ms)". 
No other text, no decoration, no icons, generous white margins, crisp 2K resolution.
```

## Graphique 2 — Scores au banc (45 cas)

```
Minimalist white-background vertical bar chart, Swiss editorial style. Five vertical 
bars with these EXACT values and labels underneath:
- "Foq 8B final" : vivid orange #FF5C00, value "100,0 %"
- "Foq 27B" : near-black, value "100,0 %"
- "8B nu" : gray, value "97,8 %"
- "Foq 4B" : gray, value "91,1 %"
- "Foq 1.7B" : gray, value "86,7 %"
Y-axis starts at 80 and ends at 101, thin gray gridlines. Value printed on top of each 
bar in black. Title: "Score au banc d'examen — 45 cas (%)". No decoration, no icons, 
generous margins, crisp 2K resolution.
```

## Graphique 3 — Calibration ECE

```
Minimalist white-background two-bar chart. Left bar gray labeled "Brut", height "6,65 %" ; 
right bar vivid orange #FF5C00 labeled "Après RLCD", much shorter, height "0,23 %". 
Values printed above each bar in black. Title: "Calibration — écart entre confiance 
annoncée et réalité (%)". White background, thin gray gridlines, no icons, crisp 2K.
```

## Graphique 4 — Coût par million de décisions

```
Minimalist white-background two-bar chart. Left bar vivid orange #FF5C00 labeled "Foq (local)", 
height zero with the text "0 €" printed above it. Right bar gray labeled "LLM API (haut de 
fourchette)", very tall, value "10 000 €" printed above. Title: "Coût pour 1 000 000 de 
décisions (EUR)". White background, thin gray gridlines, no icons, crisp 2K.
```

## Bannière hero (16:9, sans texte)

```
Ultra-minimalist abstract visualization of speed: a single thin horizontal orange line 
crossing a dark charcoal frame in one straight instantaneous stroke, while four thick gray 
tangled lines trail far behind. Vast negative space, flat design, no text, no numbers, 
no letters, Swiss poster aesthetic.
```

## Restylage sans altérer les données (image-to-image)

```
Keep this exact chart — bars, labels and numbers perfectly unchanged. Restyle only: 
pure white background, single orange accent bar, thin gray axes, generous margins, 
Swiss minimalist editorial style, crisp 2x resolution. Do not redraw the data, 
do not alter any text or value.
```
*→ charger le PNG de référence `docs/assets/chart_*.png` comme image source, puis
revérifier chaque chiffre sur le rendu.*
