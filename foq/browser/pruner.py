"""
Élagueur de DOM intelligent (DOM Pruner) pour Foq Browser Agent.
Compresse une page web complexe en un ensemble épuré d'éléments interactifs
(200 à 400 tokens) pour respecter la fenêtre de contexte Système 1 de Foq.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class InteractiveElement:
    """Représente un élément interactif extrait du DOM."""
    foq_id: int
    letter: str
    tag: str
    element_type: str
    label: str
    placeholder: str
    current_value: str
    selector: str

    def to_summary(self) -> str:
        """Formate l'élément pour le prompt de décision Foq."""
        type_info = f":{self.element_type}" if self.element_type else ""
        val_info = f" [valeur actuelle: '{self.current_value}']" if self.current_value else " [vide]"
        ph_info = f" (placeholder: '{self.placeholder}')" if (self.placeholder and not self.label) else ""
        return f"[{self.letter}] <{self.tag}{type_info}> \"{self.label or self.placeholder or 'sans nom'}\"{ph_info}{val_info}"


# Script JavaScript injecté dans Playwright pour extraire et tagger les éléments
DOM_EXTRACTION_SCRIPT = """
(() => {
    document.querySelectorAll('[data-foq-id]').forEach(el => el.removeAttribute('data-foq-id'));

    // 1. Extraits textuels clés (titres, alertes, premier paragraphe)
    const keyNodes = Array.from(document.querySelectorAll('h1, h2, [role="alert"], .alert, .success-box, #bodyContent p, main p, article p'));
    const snippets = [];
    for (const node of keyNodes) {
        if (snippets.length >= 3) break;
        const rect = node.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;
        const style = window.getComputedStyle(node);
        if (style.visibility === 'hidden' || style.display === 'none') continue;
        const txt = node.innerText ? node.innerText.trim().replace(/\\s+/g, ' ').slice(0, 100) : '';
        if (txt && !snippets.includes(txt) && txt.length > 5) snippets.push(txt);
    }

    // 2. Champs de saisie, de formulaire et barres de recherche (jusqu'à 6)
    const formCandidates = Array.from(document.querySelectorAll(
        'input, select, textarea'
    )).filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none';
    }).slice(0, 6);

    // 3. Produits, articles et cartes du contenu central (jusqu'à 8)
    const productCandidates = Array.from(document.querySelectorAll(
        '.product_pod h3 a, article h2 a, article h3 a, .card a, #bodyContent p a[href], main p a[href], .mw-parser-output > p a[href]'
    )).slice(0, 8);

    // 4. Boutons d'action visibles (jusqu'à 4)
    const buttonCandidates = Array.from(document.querySelectorAll(
        'form button, button, [role="button"]'
    )).filter(b => {
        const rect = b.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && window.getComputedStyle(b).display !== 'none';
    }).slice(0, 4);

    // 5. Navigation et catégories (jusqu'à 5)
    const navCandidates = Array.from(document.querySelectorAll(
        'nav a[href], .side_categories a[href], aside a[href], .menu a[href]'
    )).slice(0, 5);

    // Combiner les catégories de manière équilibrée
    const allCandidates = Array.from(new Set([
        ...formCandidates,
        ...productCandidates,
        ...buttonCandidates,
        ...navCandidates
    ]));

    const ignorePatterns = [
        /^(modifier|modifier le code|modifier wikidata|voir l'historique|lire|discussion|article)$/i,
        /^(faire un don|créer un compte|se connecter|aide|accueil|contact|mentions légales)$/i,
        /^(politique de confidentialité|avertissements|version mobile|développeurs|statistiques)$/i,
        /^(aller au contenu|passer au contenu|sommaire|masquer|afficher)$/i,
    ];

    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const elements = [];
    let counter = 1;
    const seenLabels = new Set();

    for (const el of allCandidates) {
        if (elements.length >= 16) break;

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;

        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none' || parseFloat(style.opacity) < 0.1) continue;
        if (el.disabled || el.getAttribute('aria-disabled') === 'true') continue;

        let label = (
            el.getAttribute('title') ||
            el.getAttribute('aria-label') ||
            (el.id && document.querySelector(`label[for="${el.id}"]`)?.innerText) ||
            el.closest('label')?.innerText ||
            el.innerText ||
            el.getAttribute('placeholder') ||
            el.value ||
            ''
        ).trim();

        if (/^(add to basket|ajouter au panier|acheter|réserver|view|voir)$/i.test(label)) {
            const card = el.closest('.product_pod, .card, article, li');
            const titleEl = card ? card.querySelector('h1, h2, h3, h4, .title, a') : null;
            if (titleEl && (titleEl.title || titleEl.innerText)) {
                label = `${label} (${(titleEl.title || titleEl.innerText).trim()})`;
            }
        }

        label = label.replace(/\\s+/g, ' ').slice(0, 45);
        if (!label || label.length < 2) continue;
        if (ignorePatterns.some(p => p.test(label))) continue;
        if (seenLabels.has(label)) continue;
        seenLabels.add(label);

        const foqId = counter++;
        el.setAttribute('data-foq-id', String(foqId));
        const letter = alphabet[elements.length];

        elements.push({
            foq_id: foqId,
            letter: letter,
            tag: el.tagName.toLowerCase(),
            element_type: (el.getAttribute('type') || '').toLowerCase(),
            label: label,
            placeholder: (el.getAttribute('placeholder') || '').slice(0, 30),
            current_value: (el.value || '').slice(0, 30),
            selector: `[data-foq-id="${foqId}"]`
        });
    }

    return {
        elements: elements,
        page_snippets: snippets.join(" | ")
    };
})()
"""


class DOMPruner:
    """Gestionnaire d'élagage du DOM pour Playwright."""

    @staticmethod
    def extract_interactive_elements(page) -> List[InteractiveElement]:
        """Extrait uniquement les éléments interactifs."""
        elements, _ = DOMPruner.extract_page_state(page)
        return elements

    @staticmethod
    def extract_page_state(page) -> Tuple[List[InteractiveElement], str]:
        """Exécute le script d'extraction dans la page Playwright et renvoie (éléments, snippets)."""
        raw = page.evaluate(DOM_EXTRACTION_SCRIPT)
        raw_elements = raw.get("elements", [])
        snippets = raw.get("page_snippets", "")
        elements = []
        for item in raw_elements:
            elements.append(InteractiveElement(
                foq_id=item["foq_id"],
                letter=item["letter"],
                tag=item["tag"],
                element_type=item["element_type"],
                label=item["label"],
                placeholder=item["placeholder"],
                current_value=item["current_value"],
                selector=item["selector"],
            ))
        return elements, snippets

    @staticmethod
    def format_state(
        goal: str,
        current_url: str,
        page_title: str,
        elements: List[InteractiveElement],
        page_snippets: Optional[str] = None,
        last_action_feedback: Optional[str] = None,
    ) -> str:
        """Produit un état textuel ultra-compact pour Foq (150 à 400 tokens)."""
        lines = [
            f"[OBJECTIF ACTUEL] : {goal}",
            f"[PAGE ACTUELLE] : {page_title} (URL: {current_url})",
        ]
        if page_snippets:
            lines.append(f"[CONTENU CLÉ VISIBLE] : {page_snippets}")
        if last_action_feedback:
            lines.append(f"[DERNIÈRE ACTION RÉALISÉE] : {last_action_feedback}")

        lines.append("\n[ÉLÉMENTS INTERACTIFS DISPONIBLES] :")
        if not elements:
            lines.append("(Aucun élément interactif détecté sur cette page)")
        else:
            for el in elements:
                lines.append(f"  {el.to_summary()}")

        return "\n".join(lines)
