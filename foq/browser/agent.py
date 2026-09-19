"""
Agent Navigateur Web Système 1 pour Foq.
Pilote Chromium via Playwright à haute cadence (sans latence LLM générative)
grâce aux décisions en 1 passe de FoqEngine.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..engine import FoqEngine
from ..schemas import Noul, Choice
from .pruner import DOMPruner, InteractiveElement


@dataclass
class BrowserStep:
    """Représente une étape de navigation exécutée."""
    step_index: int
    page_url: str
    page_title: str
    target_element: Optional[InteractiveElement]
    action_type: str
    value_filled: Optional[str]
    foq_confidence: float
    foq_latency_ms: float
    exec_latency_ms: float
    total_step_latency_ms: float
    feedback: str


@dataclass
class BrowserRunResult:
    """Résultat complet d'une exécution de l'agent navigateur."""
    goal: str
    success: bool
    final_url: str
    final_title: str
    total_latency_ms: float
    average_step_ms: float
    steps: List[BrowserStep] = field(default_factory=list)
    error_message: Optional[str] = None

    def summary(self) -> str:
        status = "[SUCCES]" if self.success else "[NON TERMINE]"
        lines = [
            f"=== Rapport Foq Browser Agent ({status}) ===",
            f"Objectif : {self.goal}",
            f"Temps total : {self.total_latency_ms / 1000:.2f} s ({len(self.steps)} étapes, moyenne {self.average_step_ms:.1f} ms/étape)",
            f"URL Finale : {self.final_url} (Titre: {self.final_title})",
            "--- Déroulé des actions ---",
        ]
        for step in self.steps:
            val_str = f" ('{step.value_filled}')" if step.value_filled else ""
            el_str = f" sur [{step.target_element.letter}] {step.target_element.label}" if step.target_element else ""
            lines.append(
                f"  [{step.step_index}] {step.action_type.upper()}{val_str}{el_str} "
                f"(Confiance: {step.foq_confidence:.0%}, Décision Foq: {step.foq_latency_ms:.0f}ms, Exécution: {step.exec_latency_ms:.0f}ms)"
            )
        return "\n".join(lines)


class FoqBrowserAgent:
    """Agent autonome de navigation web ultra-rapide piloté par Foq."""

    def __init__(
        self,
        engine: Optional[FoqEngine] = None,
        headless: bool = True,
        max_steps: int = 12,
        step_delay_ms: int = 80,
    ):
        self.engine = engine or FoqEngine()
        self.headless = headless
        self.max_steps = max_steps
        self.step_delay_ms = step_delay_ms

    def _resolve_fill_value(
        self,
        element: InteractiveElement,
        goal: str,
        params: Optional[Dict[str, str]] = None
    ) -> str:
        """Détermine la valeur textuelle à injecter dans un champ input."""
        params = params or {}
        el_text = f"{element.label} {element.placeholder} {element.element_type}".lower()

        # 1. Recherche par correspondance directe de clé dans les paramètres
        for k, v in params.items():
            k_lower = k.lower()
            if k_lower in el_text or any(part in el_text for part in k_lower.split("_")):
                return str(v)

        # 2. Heuristiques courantes
        if any(w in el_text for w in ["départ", "depart", "from", "origine"]):
            return params.get("depart", params.get("from", params.get("ville_depart", "Paris")))
        if any(w in el_text for w in ["destination", "vers", "to", "arrivée", "arrivee"]):
            return params.get("destination", params.get("to", params.get("ville_arrivee", "Tokyo")))
        if "date" in el_text:
            return params.get("date", "2026-10-15")
        if any(w in el_text for w in ["nom", "name", "prenom"]):
            return params.get("nom", params.get("name", "Riley Brown"))
        if any(w in el_text for w in ["mail", "courriel"]):
            return params.get("email", "contact@foq.local")

        # 3. Première valeur disponible dans params ou extraction simple
        if params:
            return next(iter(params.values()))
        return "Test Foq"

    def run(
        self,
        goal: str,
        start_url: str,
        params: Optional[Dict[str, str]] = None,
        html_content: Optional[str] = None,
    ) -> BrowserRunResult:
        """
        Exécute la navigation web vers l'objectif donné.
        Si html_content est fourni, charge directement le contenu HTML local.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise ImportError(
                "Playwright est requis pour FoqBrowserAgent. "
                "Installez-le avec : pip install playwright && playwright install chromium"
            ) from e

        t_start = time.perf_counter()
        steps: List[BrowserStep] = []
        last_feedback: Optional[str] = None
        success = False
        error_msg = None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            if html_content:
                page.set_content(html_content)
                page.wait_for_load_state("domcontentloaded")
            else:
                page.goto(start_url)
                page.wait_for_load_state("domcontentloaded")

            for step_idx in range(1, self.max_steps + 1):
                # 1. Élagage du DOM et extraction des extraits clés
                elements, snippets = DOMPruner.extract_page_state(page)
                current_url = page.url
                page_title = page.title() or "Page Web"

                state_text = DOMPruner.format_state(
                    goal=goal,
                    current_url=current_url,
                    page_title=page_title,
                    elements=elements,
                    page_snippets=snippets,
                    last_action_feedback=last_feedback,
                )

                # 2. Évaluation Système 1 Foq : L'objectif est-il déjà atteint ?
                t_decide_0 = time.perf_counter()
                completion_check = self.engine.system_one(
                    state=state_text,
                    questions={
                        "is_done": Noul(f"L'objectif suivant est-il pleinement atteint et terminé avec succès : '{goal}' ?")
                    }
                )
                t_decide_foq = (time.perf_counter() - t_decide_0) * 1000

                if completion_check.is_done.answer and completion_check.is_done.confidence >= 0.75:
                    success = True
                    break

                if not elements:
                    last_feedback = "Aucun élément interactif restant sur la page."
                    break

                # 3. Prise de décision de l'action à mener (Choix de l'élément)
                choices_dict = {
                    el.letter: f"{el.tag} \"{el.label or el.placeholder}\""
                    for el in elements
                }

                t_decide_0 = time.perf_counter()
                action_decision = self.engine.system_one(
                    state=state_text,
                    questions={
                        "element": Choice(
                            instructions=f"Quel élément interactif faut-il cibler maintenant pour progresser vers l'objectif : '{goal}' ?",
                            choices=choices_dict
                        )
                    }
                )
                foq_latency_ms = (time.perf_counter() - t_decide_0) * 1000

                chosen_letter = action_decision.element.choice
                confidence = action_decision.element.confidence

                # Trouver l'élément sélectionné
                target_el = next((e for e in elements if e.letter == chosen_letter), elements[0])

                # Déterminer la nature de l'action selon le composant cible
                if target_el.tag in ["button", "a"] or target_el.element_type in ["submit", "button"]:
                    chosen_action = "click"
                elif target_el.tag in ["input", "textarea"] and target_el.element_type in [
                    "text", "password", "email", "number", "tel", "url", "search", "date", ""
                ]:
                    chosen_action = "fill"
                else:
                    chosen_action = "click"

                # 4. Exécution Playwright
                t_exec_0 = time.perf_counter()
                value_filled = None

                try:
                    locator = page.locator(target_el.selector).first
                    if chosen_action == "fill":
                        value_filled = self._resolve_fill_value(target_el, goal, params)
                        locator.fill(value_filled)
                        last_feedback = f"Saisie de '{value_filled}' dans [{target_el.letter}] {target_el.label}"
                        # Déclenchement automatique de la recherche pour les champs de recherche
                        is_search = target_el.element_type == "search" or any(
                            w in f"{target_el.label} {target_el.placeholder}".lower() for w in ["search", "recherch"]
                        )
                        if is_search:
                            locator.press("Enter")
                            last_feedback += " + Entrée"
                    elif chosen_action == "click":
                        try:
                            locator.click(timeout=2500)
                            last_feedback = f"Clic sur [{target_el.letter}] {target_el.label}"
                        except Exception:
                            try:
                                locator.click(force=True, timeout=1500)
                                last_feedback = f"Clic forcé sur [{target_el.letter}] {target_el.label}"
                            except Exception:
                                locator.dispatch_event("click")
                                last_feedback = f"Clic événementiel sur [{target_el.letter}] {target_el.label}"

                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=2500)
                    except Exception:
                        pass
                    page.wait_for_timeout(self.step_delay_ms)
                except Exception as e:
                    last_feedback = f"Erreur lors de l'action sur {target_el.selector} : {str(e)[:80]}"

                exec_latency_ms = (time.perf_counter() - t_exec_0) * 1000
                total_step_ms = foq_latency_ms + exec_latency_ms

                steps.append(BrowserStep(
                    step_index=step_idx,
                    page_url=current_url,
                    page_title=page_title,
                    target_element=target_el,
                    action_type=chosen_action,
                    value_filled=value_filled,
                    foq_confidence=confidence,
                    foq_latency_ms=foq_latency_ms,
                    exec_latency_ms=exec_latency_ms,
                    total_step_latency_ms=total_step_ms,
                    feedback=last_feedback,
                ))

            final_url = page.url
            final_title = page.title() or ""
            browser.close()

        total_latency_ms = (time.perf_counter() - t_start) * 1000
        avg_step_ms = (total_latency_ms / len(steps)) if steps else 0.0

        return BrowserRunResult(
            goal=goal,
            success=success,
            final_url=final_url,
            final_title=final_title,
            total_latency_ms=total_latency_ms,
            average_step_ms=avg_step_ms,
            steps=steps,
            error_message=error_msg,
        )
