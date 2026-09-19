# 📚 Complete Foq API Reference

This document details every class, function, method and data structure of the Python `foq` package.

---

## 1. `foq.engine` Module

### `class FoqEngine`
The main entry point for talking to the local Foq inference server (port 8089).

#### Constructor
```python
FoqEngine(
    base_url: str = "http://127.0.0.1:8089",
    profile_path: Optional[str] = None,
    timeout_seconds: float = 10.0,
)
```
* `base_url`: address of the local `llama-server`.
* `profile_path`: path to the calibration JSON file (by default, `calibration_profile.json` is looked up at the repository root, regardless of the working directory).
* `timeout_seconds`: maximum HTTP timeout per request.

The engine supports context management (`with FoqEngine() as engine:`) and a `close()` method to release the HTTP client cleanly.

#### Health-Check Methods
* `is_server_ready() -> bool`: synchronously checks whether the server answers on `/health` or `/props`.
* `async is_server_ready_async() -> bool`: non-blocking asynchronous version of the health check.

#### System 1 Decision Methods (Primitives & Schemas)
* `system_one(state: Union[str, Dict[str, Any]], questions: Dict[str, Any], calibrate: bool = True, max_workers: int = 4) -> SystemOneResponse`
  Simultaneously evaluates a set of primitives (`Boolean`, `Choice`, `Score`, `Structure`) on the same context via a thread pool.
* `async system_one_async(state: Union[str, Dict[str, Any]], questions: Dict[str, Any], calibrate: bool = True) -> SystemOneResponse`
  Native asynchronous version (`asyncio.gather`) processing all questions concurrently.
* `decide(context: str, schema: DecisionSchema, calibrate: bool = True) -> Dict[str, Any]`
  Takes a single synchronous decision on a given schema in one logit pass (`n_predict=1`).
* `async decide_async(context: str, schema: DecisionSchema, calibrate: bool = True) -> Dict[str, Any]`
  Asynchronous version of `decide()`.
* `decide_multi(context: str, schemas: List[DecisionSchema], calibrate: bool = True, max_workers: int = 4) -> Dict[str, Any]`
  Evaluates a list of schemas in parallel on the same context.
* `async decide_multi_async(context: str, schemas: List[DecisionSchema], calibrate: bool = True) -> Dict[str, Any]`
  Asynchronous version of `decide_multi()`.

#### Hierarchical Extraction Methods (Pydantic / GBNF)
* `extract(state: Union[str, Dict[str, Any]], schema: Union[Structure, Any], instructions: Optional[str] = None, max_tokens: int = 500) -> Any`
  Extracts a Pydantic-validated object or a JSON-Schema-conformant value by applying a strict grammar.
* `async extract_async(state: Union[str, Dict[str, Any]], schema: Union[Structure, Any], instructions: Optional[str] = None, max_tokens: int = 500) -> Any`
  Asynchronous version of `extract()`.

#### Error Handling
`system_one()`, `system_one_async()`, `extract()` and `extract_async()` raise a `FoqConnectionError` if the server is unreachable, times out or answers with an error: no default answer is ever invented. `decide()` and `decide_async()` instead return an `{"success": False, "error": ...}` dictionary.

#### Honest Abstention (`min_confidence`)
All decision methods accept an optional `min_confidence` parameter (e.g. `0.8`):
* `decide()` / `decide_async()` then add `"needs_review": true|false` to the returned dictionary.
* `system_one()` / `system_one_async()` attach a `needs_review` attribute to every result and expose `response.needs_review`: the list of keys whose calibrated confidence is below the threshold.
* Without the parameter, no flag is emitted (behavior unchanged).

```python
resp = engine.system_one(state=email, questions={
    "urgent": Boolean("Is this email critical?"),
}, min_confidence=0.8)
for key in resp.needs_review:      # confidence < 80% -> human review queue
    route_to_human(key, resp[key])
```

---

### `class SystemOneResponse`
Container object returned by `system_one()` and `system_one_async()`.

#### Attributes
* Direct dot access: `response.<question_key>` returns the typed result of the matching question (`BooleanResult`, `ChoiceResult`, `ScoreResult` or a Pydantic instance).
* `latency_ms: float`: total request duration in milliseconds.
* Also supports dictionary-style access: `response["key"]`.

---

## 2. `foq.schemas` Module

### The Official Primitives

#### `class Boolean(instructions: str)` (aliases `Bool`, `Noul`)
Primitive for boolean decisions (Yes / No, True / False).
* **Input**: instructions or a binary question.
* **Produced result**: `BooleanResult` (aliases `BoolResult`, `NoulResult`)
  * `answer: bool`: `True` for Yes/True, `False` for No/False.
  * `confidence: float`: calibrated probability of the retained choice (between 0.0 and 1.0).
  * `probabilities: Dict[str, float]`: distributed probabilities `{"yes": p1, "no": p2}`.
  * `latency_ms: float`: decision time.

#### `class Choice(instructions: str, choices: Dict[str, str])`
Primitive for exclusive selection among a set of typed options.
* **Input**: a dictionary mapping a technical identifier to its description, e.g. `{"db": "Database", "web": "Web Server"}`.
* **Produced result**: `ChoiceResult`
  * `choice: str`: identifier of the winning key (e.g. `"db"`).
  * `label: str`: textual label of the option.
  * `confidence: float`: calibrated probability of the winning option.
  * `probabilities: Dict[str, float]`: calibrated probabilities for every key.
  * `latency_ms: float`: decision time.

#### `class Score(instructions: str, levels: Dict[str, str])`
Primitive for rating on a discrete or ordered scale.
* **Input**: a dictionary mapping a level to its meaning, e.g. `{"1": "Low", "2": "Medium", "3": "Critical"}`.
* **Produced result**: `ScoreResult`
  * `score: Union[float, str]`: weighted continuous mathematical expectation if the keys are numeric (e.g. `2.78`), otherwise the best level key.
  * `level: str`: discrete level that received the highest probability (e.g. `"3"`).
  * `confidence: float`: calibrated probability of the best level.
  * `probabilities: Dict[str, float]`: distribution over all levels.
  * `latency_ms: float`: decision time.

#### `class Structure(target: Any, instructions: Optional[str] = None)`
Structured-extraction primitive for Pydantic v2 models or JSON Schema dictionaries.
* `target`: a class inheriting from `pydantic.BaseModel`, or a JSON Schema `dict`.
* `instructions`: extraction-specific instructions.

---

## 3. `foq.security` Module

### `class FoqSecurityGuard`
Autonomous System 1 guard auditing text streams against application threats in ~100 ms.

#### Methods
* `inspect(text: str) -> SecurityVerdict`: synchronous audit of the text.
* `async inspect_async(text: str) -> SecurityVerdict`: non-blocking asynchronous audit of the text.

### `class SecurityVerdict`
* `is_safe: bool`: `True` if no threat is detected.
* `threat_type: str`: `"CLEAN"`, `"PROMPT_INJECTION"`, `"MALICIOUS_PAYLOAD"` or `"ENGINE_UNAVAILABLE"` (fail-closed guard: if the Foq engine is unreachable, the request is considered unsafe and blocked).
* `confidence: float`: calibrated certainty score (0.0 to 1.0).
* `latency_ms: float`: analysis time in milliseconds.
* `reason: str`: explanation of the retained verdict.

### `class FoqSecurityMiddleware`
Ready-to-use ASGI middleware for web frameworks (FastAPI, Starlette).

---

## 4. `foq.browser` Module

### `class FoqBrowserAgent`
Autonomous web navigation agent driven by Playwright and FoqEngine.

#### Main Method
* `run(goal: str, start_url: str, params: Optional[Dict[str, str]] = None, html_content: Optional[str] = None) -> BrowserRunResult`

### `class DOMPruner`
Smart DOM-pruning module that reduces a web page to 200-400 exploitable tokens.

---

## 5. `foq.calibration` Module

* `class TemperatureScaler(temperature: float = 1.0)`
* `class ExpectedCalibrationError(n_bins: int = 10)`
* `class BrierScore`
* `class CalibrationProfile(filepath: str = "calibration_profile.json")`

---

## 6. CLI Interface (`foq`)

| Command | Action |
|---|---|
| `foq serve` | Starts the local `llama-server.exe` on port 8089 with llama.cpp. |
| `foq demo` | Launches the interactive demo with probability bar visualization. |
| `foq benchmark` | Runs the full latency and throughput benchmark suite. |
| `foq inspect "<text>"` | Analyzes a text or payload with the AI WAF and prints the live verdict. |
