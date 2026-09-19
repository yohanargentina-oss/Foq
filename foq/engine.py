"""
Moteur principal Foq.
Interroge le serveur local en mode zéro-génération (1 seul token de sortie avec logprobs)
et applique la couche de calibration RLCD pour renvoyer des probabilités rigoureuses.
"""

import math
import os
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
import httpx
from concurrent.futures import ThreadPoolExecutor

from .calibration import TemperatureScaler, CalibrationProfile
from .schemas import DecisionSchema, Structure
from .patches import appliquer_correctifs

# Correctifs déterministes des défauts connus (foq/patches.py) : activés par défaut,
# désactivables via FoqEngine(patches=False) ou engine.patches_enabled = False.
PATCHES_PAR_DEFAUT = True

# Seuil d'abstention mesuré sur 500 cas aveugles (docs/BENCHMARKS.md) :
# conf >= 0.95 → 8B autonome fiable ; en dessous → needs_review (+5,6 pts mesurés).
SEUIL_REVIEW_MESURE = 0.95

# Profil de calibration par défaut : racine du dépôt, indépendante du répertoire de travail
_DEFAULT_PROFILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calibration_profile.json"
)


class FoqConnectionError(RuntimeError):
    """Élevée quand le serveur Foq est injoignable, timeout ou répond en erreur."""


class SystemOneResponse:
    """Objet réponse avec accès direct par attributs (dot-notation) haute fidélité."""

    def __init__(self, data: Dict[str, Any], latency_ms: float):
        self._data = data
        self.latency_ms = latency_ms
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, item):
        return self._data[item]

    def __repr__(self):
        fields = ", ".join(f"{k}={repr(v)}" for k, v in self._data.items())
        return f"SystemOneResponse({fields}, latency_ms={self.latency_ms:.1f}ms)"


class FoqEngine:
    """Moteur de décision ultra-rapide Foq (System 1)."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8089",
        profile_path: Optional[str] = None,
        timeout_seconds: float = 10.0,
        patches: bool = PATCHES_PAR_DEFAUT,
        min_confidence: Optional[float] = SEUIL_REVIEW_MESURE,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout_seconds)
        self.patches_enabled = patches
        self.min_confidence = min_confidence

        # Charger profil de calibration si existant
        self.profile = CalibrationProfile(profile_path or _DEFAULT_PROFILE_PATH)
        self.profile.load()
        self.scaler = TemperatureScaler(temperature=self.profile.temperature)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        """Ferme le client HTTP sous-jacent."""
        self.client.close()

    def is_server_ready(self) -> bool:
        """Vérifie si le serveur Foq est actif."""
        try:
            res = self.client.get("/health", timeout=1.0)
            return res.status_code == 200
        except Exception:
            try:
                res = self.client.get("/props", timeout=1.0)
                return res.status_code == 200
            except Exception:
                return False

    async def is_server_ready_async(self) -> bool:
        """Vérifie de manière asynchrone si le serveur Foq est actif."""
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=1.0) as client:
                res = await client.get("/health")
                return res.status_code == 200
        except Exception:
            try:
                async with httpx.AsyncClient(base_url=self.base_url, timeout=1.0) as client:
                    res = await client.get("/props")
                    return res.status_code == 200
            except Exception:
                return False

    def _parse_completion_response(
        self,
        data: Dict[str, Any],
        schema: DecisionSchema,
        calibrate: bool,
        latency_ms: float
    ) -> Dict[str, Any]:
        """Extrait et calibre les probabilités à partir de la réponse du serveur."""
        valid_keys = schema.get_keys()
        completion_probs = data.get("completion_probabilities", [])
        raw_logprobs_map: Dict[str, float] = {k: -25.0 for k in valid_keys}

        if completion_probs and len(completion_probs) > 0:
            top_list = completion_probs[0].get("top_logprobs", [])
            for item in top_list:
                tok_str = item.get("token", "").strip().strip("[]()").upper()
                lp = item.get("logprob", -25.0)
                if tok_str in raw_logprobs_map:
                    if lp > raw_logprobs_map[tok_str]:
                        raw_logprobs_map[tok_str] = lp

        max_lp = max(raw_logprobs_map.values())
        raw_exps = {k: math.exp(v - max_lp) for k, v in raw_logprobs_map.items()}
        sum_exps = sum(raw_exps.values())
        raw_probs = {k: v / sum_exps for k, v in raw_exps.items()}

        if calibrate and self.scaler.temperature != 1.0:
            calibrated_probs = self.scaler.scale_probabilities(raw_logprobs_map)
        else:
            calibrated_probs = raw_probs.copy()

        best_key = max(calibrated_probs.keys(), key=lambda k: calibrated_probs[k])
        best_opt = next((opt for opt in schema.options if opt.key == best_key), None)

        return {
            "success": True,
            "decision_key": best_key,
            "decision_label": best_opt.label if best_opt else best_key,
            "confidence": round(calibrated_probs[best_key], 4),
            "calibrated_probabilities": {k: round(v, 4) for k, v in calibrated_probs.items()},
            "raw_probabilities": {k: round(v, 4) for k, v in raw_probs.items()},
            "temperature_used": round(self.scaler.temperature, 3),
            "latency_ms": round(latency_ms, 2),
            "tokens_predicted": data.get("tokens_predicted", 1),
            "tokens_evaluated": data.get("tokens_evaluated", 0),
        }

    def decide(
        self,
        context: str,
        schema: DecisionSchema,
        calibrate: bool = True,
        min_confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Prend une décision synchrone en une seule passe sans génération de texte.

        Avec min_confidence (ex. 0.8), la réponse porte en plus un drapeau
        "needs_review": True quand la confiance calibrée passe sous le seuil —
        le moteur avoue ainsi son incertitude au lieu de répondre avec assurance.
        """
        prompt = schema.format_prompt(context)
        payload = {
            "prompt": prompt,
            "n_predict": 1,
            "n_probs": 25,
            "temperature": 0.0,
            "cache_prompt": True,
        }
        t0 = time.perf_counter()
        try:
            response = self.client.post("/completion", json=payload)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur de communication avec le serveur Foq: {str(e)}",
                "latency_ms": (time.perf_counter() - t0) * 1000,
            }
        latency_ms = (time.perf_counter() - t0) * 1000
        result = self._parse_completion_response(data, schema, calibrate, latency_ms)
        if self.patches_enabled:
            result = appliquer_correctifs(context, question=schema.question, schema=schema, resultat=result)
        seuil = min_confidence if min_confidence is not None else self.min_confidence
        if seuil is not None and result.get("success"):
            result["needs_review"] = result["confidence"] < seuil
        return result

    async def decide_async(
        self,
        context: str,
        schema: DecisionSchema,
        calibrate: bool = True,
        min_confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Prend une décision asynchrone ultra-rapide sans bloquer le thread principal."""
        prompt = schema.format_prompt(context)
        payload = {
            "prompt": prompt,
            "n_predict": 1,
            "n_probs": 25,
            "temperature": 0.0,
            "cache_prompt": True,
        }
        t0 = time.perf_counter()
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            try:
                response = await client.post("/completion", json=payload)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Erreur de communication avec le serveur Foq: {str(e)}",
                    "latency_ms": (time.perf_counter() - t0) * 1000,
                }
        latency_ms = (time.perf_counter() - t0) * 1000
        result = self._parse_completion_response(data, schema, calibrate, latency_ms)
        if self.patches_enabled:
            result = appliquer_correctifs(context, question=schema.question, schema=schema, resultat=result)
        seuil = min_confidence if min_confidence is not None else self.min_confidence
        if seuil is not None and result.get("success"):
            result["needs_review"] = result["confidence"] < seuil
        return result

    def decide_multi(
        self,
        context: str,
        schemas: List[DecisionSchema],
        calibrate: bool = True,
        max_workers: int = 4,
    ) -> Dict[str, Any]:
        """Évalue plusieurs questions/schémas en parallèle sur le même contexte (Synchrone)."""
        t0 = time.perf_counter()
        results: Dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                schema.name: executor.submit(self.decide, context, schema, calibrate)
                for schema in schemas
            }
            for name, future in futures.items():
                results[name] = future.result()

        total_latency_ms = (time.perf_counter() - t0) * 1000
        structured_output = {
            name: {
                "choice": res.get("decision_label"),
                "confidence": res.get("confidence"),
                "key": res.get("decision_key"),
            }
            for name, res in results.items()
            if res.get("success")
        }
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "structured_output": structured_output,
            "details": results,
            "total_latency_ms": round(total_latency_ms, 2),
        }

    async def decide_multi_async(
        self,
        context: str,
        schemas: List[DecisionSchema],
        calibrate: bool = True,
    ) -> Dict[str, Any]:
        """Évalue plusieurs questions en concurrence asyncio native."""
        t0 = time.perf_counter()
        tasks = [self.decide_async(context, schema, calibrate) for schema in schemas]
        raw_results = await asyncio.gather(*tasks)
        results = {schema.name: res for schema, res in zip(schemas, raw_results)}
        total_latency_ms = (time.perf_counter() - t0) * 1000
        structured_output = {
            name: {
                "choice": res.get("decision_label"),
                "confidence": res.get("confidence"),
                "key": res.get("decision_key"),
            }
            for name, res in results.items()
            if res.get("success")
        }
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "structured_output": structured_output,
            "details": results,
            "total_latency_ms": round(total_latency_ms, 2),
        }

    def extract(
        self,
        state: Union[str, Dict[str, Any]],
        schema: Union[Structure, Any],
        instructions: Optional[str] = None,
        max_tokens: int = 500,
    ) -> Any:
        """
        Extrait un objet JSON hiérarchique complexe (arborescence, listes, sous-objets imbriqués)
        garanti 100% conforme au schéma Pydantic ou JSON Schema fourni via grammaire contrainte.
        """
        if not isinstance(schema, Structure):
            schema_obj = Structure(target=schema, instructions=instructions)
        else:
            schema_obj = schema

        import json
        context_str = json.dumps(state, indent=2, ensure_ascii=False) if isinstance(state, dict) else str(state)
        prompt = schema_obj.format_prompt(context_str)

        payload = {
            "prompt": prompt,
            "json_schema": schema_obj.json_schema,
            "temperature": 0.0,
            "n_predict": max_tokens,
            "cache_prompt": True,
        }

        try:
            response = self.client.post("/completion", json=payload)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise FoqConnectionError(f"Erreur de communication avec le serveur Foq : {e}") from e
        content = data.get("content", "").strip()
        return schema_obj.parse_result(content)

    async def extract_async(
        self,
        state: Union[str, Dict[str, Any]],
        schema: Union[Structure, Any],
        instructions: Optional[str] = None,
        max_tokens: int = 500,
    ) -> Any:
        """Version asynchrone non-bloquante de extract()."""
        if not isinstance(schema, Structure):
            schema_obj = Structure(target=schema, instructions=instructions)
        else:
            schema_obj = schema

        import json
        context_str = json.dumps(state, indent=2, ensure_ascii=False) if isinstance(state, dict) else str(state)
        prompt = schema_obj.format_prompt(context_str)

        payload = {
            "prompt": prompt,
            "json_schema": schema_obj.json_schema,
            "temperature": 0.0,
            "n_predict": max_tokens,
            "cache_prompt": True,
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_seconds) as client:
            try:
                response = await client.post("/completion", json=payload)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                raise FoqConnectionError(f"Erreur de communication avec le serveur Foq : {e}") from e
        content = data.get("content", "").strip()
        return schema_obj.parse_result(content)

    def system_one(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Dict[str, Any],
        calibrate: bool = True,
        max_workers: int = 4,
        min_confidence: Optional[float] = None,
    ) -> SystemOneResponse:
        """
        Interface unifiée Système 1 compatible Foq (Synchrone).
        Supporte à la fois les primitives de décision scalaires (Noul, Choice, Score)
        et les schémas hiérarchiques complexes Pydantic / Structure en parallèle.

        Avec min_confidence, chaque résultat porte un attribut needs_review (bool)
        et response.needs_review liste les clés dont la confiance est sous le seuil :
        l'application peut alors router ces cas vers un humain ou une API.
        """
        import json
        if isinstance(state, dict):
            context_str = json.dumps(state, indent=2, ensure_ascii=False)
        else:
            context_str = str(state)

        t0 = time.perf_counter()
        parsed_results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_key = {}
            for key, item in questions.items():
                if isinstance(item, Structure) or hasattr(item, "model_json_schema"):
                    future_to_key[key] = (executor.submit(self.extract, context_str, item), item, True)
                else:
                    future_to_key[key] = (executor.submit(self.decide, context_str, item, calibrate), item, False)

            for key, (future, schema, is_struct) in future_to_key.items():
                if is_struct:
                    parsed_results[key] = future.result()
                else:
                    raw_res = future.result()
                    if not raw_res.get("success", False):
                        raise FoqConnectionError(
                            f"Question '{key}' : {raw_res.get('error', 'réponse invalide du serveur Foq')}"
                        )
                    parsed_results[key] = schema.parse_result(raw_res)

        if min_confidence is not None:
            for key, res in parsed_results.items():
                raw_conf = getattr(res, "confidence", None)
                if raw_conf is not None:
                    res.needs_review = raw_conf < min_confidence

        total_latency = (time.perf_counter() - t0) * 1000
        response = SystemOneResponse(parsed_results, latency_ms=total_latency)
        if min_confidence is not None:
            response.needs_review = [
                k for k, res in parsed_results.items() if getattr(res, "needs_review", False)
            ]
        return response

    async def system_one_async(
        self,
        state: Union[str, Dict[str, Any]],
        questions: Dict[str, Any],
        calibrate: bool = True,
        min_confidence: Optional[float] = None,
    ) -> SystemOneResponse:
        """
        Interface unifiée Système 1 compatible Foq (Asynchrone native).
        Supporte à la fois les primitives de décision scalaires (Noul, Choice, Score)
        et les schémas hiérarchiques complexes Pydantic / Structure en concurrence asyncio.

        Avec min_confidence, chaque résultat porte un attribut needs_review (bool)
        et response.needs_review liste les clés dont la confiance est sous le seuil.
        """
        import json
        if isinstance(state, dict):
            context_str = json.dumps(state, indent=2, ensure_ascii=False)
        else:
            context_str = str(state)

        t0 = time.perf_counter()
        tasks = []
        keys = []
        is_struct_list = []
        schema_list = []

        for key, item in questions.items():
            keys.append(key)
            schema_list.append(item)
            if isinstance(item, Structure) or hasattr(item, "model_json_schema"):
                tasks.append(self.extract_async(context_str, item))
                is_struct_list.append(True)
            else:
                tasks.append(self.decide_async(context_str, item, calibrate))
                is_struct_list.append(False)

        raw_results = await asyncio.gather(*tasks)
        parsed_results = {}
        for key, schema, is_struct, raw_res in zip(keys, schema_list, is_struct_list, raw_results):
            if is_struct:
                parsed_results[key] = raw_res
            else:
                if not raw_res.get("success", False):
                    raise FoqConnectionError(
                        f"Question '{key}' : {raw_res.get('error', 'réponse invalide du serveur Foq')}"
                    )
                parsed_results[key] = schema.parse_result(raw_res)

        if min_confidence is not None:
            for key, res in parsed_results.items():
                raw_conf = getattr(res, "confidence", None)
                if raw_conf is not None:
                    res.needs_review = raw_conf < min_confidence

        total_latency = (time.perf_counter() - t0) * 1000
        response = SystemOneResponse(parsed_results, latency_ms=total_latency)
        if min_confidence is not None:
            response.needs_review = [
                k for k, res in parsed_results.items() if getattr(res, "needs_review", False)
            ]
        return response


