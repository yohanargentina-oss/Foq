# Foq API Reference

Technical reference for the `foq` Python package and command-line interface.

All classes, methods, and functions documented below reflect the codebase in `foq/`.

---

## Table of Contents

1. [Engine (`foq.engine`)](#1-engine-foqengine)
   - [`FoqEngine`](#foqengine)
   - [`FoqConnectionError`](#foqconnectionerror)
   - [`SystemOneResponse`](#systemoneresponse)
2. [Decision Primitives and Schemas (`foq.schemas`)](#2-decision-primitives-and-schemas-foqschemas)
   - [`DecisionSchema`](#decisionschema)
   - [`DecisionOption`](#decisionoption)
   - [`Boolean`, `Bool`, `Noul`](#boolean-bool-noul)
   - [`BooleanResult`, `BoolResult`, `NoulResult`](#booleanresult-boolresult-noulresult)
   - [`Choice`](#choice)
   - [`ChoiceResult`](#choiceresult)
   - [`Score`](#score)
   - [`ScoreResult`](#scoreresult)
   - [`BinaryChoice`](#binarychoice)
   - [`ClassificationChoice`](#classificationchoice)
   - [`Structure`](#structure)
3. [Security Guard and Middleware (`foq.security`)](#3-security-guard-and-middleware-foqsecurity)
   - [`FoqSecurityGuard`](#foqsecurityguard)
   - [`SecurityVerdict`](#securityverdict)
   - [`FoqSecurityMiddleware`](#foqsecuritymiddleware)
4. [Calibration (`foq.calibration`)](#4-calibration-foqcalibration)
   - [`TemperatureScaler`](#temperaturescaler)
   - [`ExpectedCalibrationError`](#expectedcalibrationerror)
   - [`BrierScore`](#brierscore)
   - [`CalibrationProfile`](#calibrationprofile)
5. [Browser Automation (`foq.browser`)](#5-browser-automation-foqbrowser)
   - [`FoqBrowserAgent`](#foqbrowseragent)
   - [`DOMPruner`](#dompruner)
   - [Supporting Dataclasses (`BrowserStep`, `BrowserRunResult`, `InteractiveElement`)](#supporting-browser-dataclasses)
6. [Command-Line Interface (`foq` CLI)](#6-command-line-interface-foq-cli)
7. [`needs_review` Threshold Mechanics](#7-needs_review-threshold-mechanics)
8. [Sources](#8-sources)

---

## 1. Engine (`foq.engine`)

### `FoqEngine`

Primary client class responsible for dispatching inference requests to the local HTTP server, parsing log probabilities, and returning calibrated decision outputs or structured data.

*Definition*: [`foq/engine.py:56`](../foq/engine.py#L56)

#### Constructor

```python
def __init__(
    self,
    base_url: str = "http://127.0.0.1:8089",
    profile_path: Optional[str] = None,
    timeout_seconds: float = 10.0,
    min_confidence: Optional[float] = SEUIL_REVIEW_MESURE,
    patches: bool = False,
)
```

*Definition*: [`foq/engine.py:59-66`](../foq/engine.py#L59-L66)

- `base_url`: Base URL of the local inference server endpoint.
- `profile_path`: Filesystem path to a JSON calibration profile. If omitted (`None`), automatically resolves to the bundled profile matching the server configuration (`_DEFAULT_PROFILE_PATH` or `_BARE_PROFILE_PATH`).
- `timeout_seconds`: HTTP client timeout for server communication.
- `min_confidence`: Confidence threshold used to flag uncertain decisions (`needs_review`). Defaults to `SEUIL_REVIEW_MESURE` (`0.8`, defined at [`foq/engine.py:21`](../foq/engine.py#L21)).
- `patches`: Reserved configuration flag.

#### Context Management and Teardown

```python
def __enter__(self) -> "FoqEngine"
def __exit__(self, exc_type, exc_val, exc_tb) -> None
def close(self) -> None
```

*Definition*: [`foq/engine.py:100-108`](../foq/engine.py#L100-L108)

Closes the underlying `httpx.Client` session. Supports the standard Python context manager pattern (`with FoqEngine() as engine:`).

#### `is_server_ready`

```python
def is_server_ready(self) -> bool
```

*Definition*: [`foq/engine.py:110`](../foq/engine.py#L110)

Performs a synchronous health check against `/health` or `/props` to verify server availability.

#### `is_server_ready_async`

```python
async def is_server_ready_async(self) -> bool
```

*Definition*: [`foq/engine.py:122`](../foq/engine.py#L122)

Asynchronous non-blocking variant of `is_server_ready`.

#### `decide`

```python
def decide(
    self,
    context: str,
    schema: DecisionSchema,
    calibrate: bool = True,
    min_confidence: Optional[float] = None,
) -> Dict[str, Any]
```

*Definition*: [`foq/engine.py:183-189`](../foq/engine.py#L183-L189)

Executes a synchronous single-pass decision on `context` using `schema`. Sends a completion request with `n_predict=1` and `n_probs=25`, extracting and scaling option log probabilities.

Returns a dictionary containing:
- `"success"`: `bool`
- `"decision_key"`: Selected option key (e.g., `"A"`, `"B"`)
- `"decision_label"`: Text label of the selected option
- `"confidence"`: Calibrated probability associated with the selected key
- `"calibrated_probabilities"`: Dictionary mapping option keys to calibrated probabilities
- `"raw_probabilities"`: Dictionary mapping option keys to uncalibrated normalized probabilities
- `"temperature_used"`: Temperature scaling factor applied
- `"latency_ms"`: Measured round-trip elapsed time in milliseconds
- `"tokens_predicted"`: Number of generated tokens (typically `1`)
- `"tokens_evaluated"`: Number of prompt tokens evaluated by the server
- `"needs_review"`: `bool`, set when `min_confidence` or `self.min_confidence` is active and `confidence < threshold`

#### `decide_async`

```python
async def decide_async(
    self,
    context: str,
    schema: DecisionSchema,
    calibrate: bool = True,
    min_confidence: Optional[float] = None,
) -> Dict[str, Any]
```

*Definition*: [`foq/engine.py:222-228`](../foq/engine.py#L222-L228)

Asynchronous non-blocking variant of `decide`.

#### `decide_multi`

```python
def decide_multi(
    self,
    context: str,
    schemas: List[DecisionSchema],
    calibrate: bool = True,
    max_workers: int = 4,
) -> Dict[str, Any]
```

*Definition*: [`foq/engine.py:257-263`](../foq/engine.py#L257-L263)

Evaluates multiple decision schemas concurrently over the same context string using a thread pool.

Returns a dictionary containing:
- `"success"`: `bool` (indicates whether all schema decisions succeeded)
- `"structured_output"`: Mapping of schema names to simplified decision summaries
- `"details"`: Mapping of schema names to complete `decide` result dictionaries
- `"total_latency_ms"`: Total elapsed duration in milliseconds

#### `decide_multi_async`

```python
async def decide_multi_async(
    self,
    context: str,
    schemas: List[DecisionSchema],
    calibrate: bool = True,
) -> Dict[str, Any]
```

*Definition*: [`foq/engine.py:292-297`](../foq/engine.py#L292-L297)

Asynchronous variant of `decide_multi` using native `asyncio.gather`.

#### `extract`

```python
def extract(
    self,
    state: Union[str, Dict[str, Any]],
    schema: Union[Structure, Any],
    instructions: Optional[str] = None,
    max_tokens: int = 500,
) -> Any
```

*Definition*: [`foq/engine.py:320-326`](../foq/engine.py#L320-L326)

Extracts structured data conforming to a Pydantic `BaseModel` class or JSON Schema dictionary using grammar-constrained generation. When LoRA adapters are present, adapter weights are temporarily scaled to zero during extraction (`_adapters_off`) to preserve generation fidelity.

Returns a validated Pydantic model instance or parsed JSON dictionary.

#### `extract_async`

```python
async def extract_async(
    self,
    state: Union[str, Dict[str, Any]],
    schema: Union[Structure, Any],
    instructions: Optional[str] = None,
    max_tokens: int = 500,
) -> Any
```

*Definition*: [`foq/engine.py:360-366`](../foq/engine.py#L360-L366)

Asynchronous non-blocking variant of `extract`.

#### `system_one`

```python
def system_one(
    self,
    state: Union[str, Dict[str, Any]],
    questions: Dict[str, Any],
    calibrate: bool = True,
    max_workers: int = 4,
    min_confidence: Optional[float] = None,
) -> SystemOneResponse
```

*Definition*: [`foq/engine.py:398-405`](../foq/engine.py#L398-L405)

High-level interface supporting both scalar primitives (`Boolean`, `Choice`, `Score`) and hierarchical `Structure` schemas in a single call. Primitives are parsed into typed result dataclasses and attached to a returned `SystemOneResponse` object.

When `min_confidence` is explicitly provided, each primitive result receives a `needs_review: bool` attribute, and `response.needs_review` lists all question keys below the threshold.

#### `system_one_async`

```python
async def system_one_async(
    self,
    state: Union[str, Dict[str, Any]],
    questions: Dict[str, Any],
    calibrate: bool = True,
    min_confidence: Optional[float] = None,
) -> SystemOneResponse
```

*Definition*: [`foq/engine.py:456-462`](../foq/engine.py#L456-L462)

Asynchronous non-blocking variant of `system_one` using `asyncio.gather`.

---

### `FoqConnectionError`

```python
class FoqConnectionError(RuntimeError):
```

*Definition*: [`foq/engine.py:35`](../foq/engine.py#L35)

Exception raised when the inference server cannot be contacted, times out, or returns an unrecoverable HTTP status.

---

### `SystemOneResponse`

Container for responses returned by `system_one` and `system_one_async`.

*Definition*: [`foq/engine.py:39`](../foq/engine.py#L39)

#### Constructor

```python
def __init__(self, data: Dict[str, Any], latency_ms: float)
```

*Definition*: [`foq/engine.py:42-46`](../foq/engine.py#L42-L46)

#### Attributes and Methods

- `latency_ms`: Total execution duration in milliseconds.
- Dynamic attributes: Each entry in `data` is mapped directly as an attribute (dot notation) and accessible via indexing (`response[key]`).
- `needs_review`: `List[str]`, present when `min_confidence` was specified during the `system_one` call.
- `__getitem__(self, item: str) -> Any`: Key-based access to results.

---

## 2. Decision Primitives and Schemas (`foq.schemas`)

### `DecisionOption`

```python
@dataclass
class DecisionOption:
    key: str
    label: str
    description: Optional[str] = None
```

*Definition*: [`foq/schemas.py:12-15`](../foq/schemas.py#L12-L15)

Data structure representing an individual choice presented to the model.

---

### `DecisionSchema`

Base class for all discrete decision schemas.

*Definition*: [`foq/schemas.py:60`](../foq/schemas.py#L60)

#### Constructor

```python
def __init__(self, name: str, question: str, options: List[DecisionOption])
```

*Definition*: [`foq/schemas.py:63-66`](../foq/schemas.py#L63-L66)

#### Methods

- `format_prompt(self, context: str) -> str`: Formats ChatML system/user prompts and appends the assistant generation prefix (`[`). Strips internal control tags from `context`. ([`foq/schemas.py:68`](../foq/schemas.py#L68))
- `get_keys(self) -> List[str]`: Returns option identifiers. ([`foq/schemas.py:98`](../foq/schemas.py#L98))
- `parse_result(self, raw_result: Dict[str, Any]) -> Any`: Transforms raw output into schema-specific representations. Subclasses override this method. ([`foq/schemas.py:101`](../foq/schemas.py#L101))

---

### `Boolean`, `Bool`, `Noul`

Boolean decision primitive mapping to a binary true/false choice.

*Definition*: [`foq/schemas.py:105`](../foq/schemas.py#L105) (aliases `Bool` at [`foq/schemas.py:130`](../foq/schemas.py#L130), `Noul` at [`foq/schemas.py:131`](../foq/schemas.py#L131)).

#### Constructor

```python
def __init__(self, instructions: str)
```

*Definition*: [`foq/schemas.py:111-116`](../foq/schemas.py#L111-L116)

Sets option `"A"` to `"Oui / Vrai"` and option `"B"` to `"Non / Faux"`.

#### Methods

- `parse_result(self, raw_result: Dict[str, Any]) -> BooleanResult`: Returns a typed `BooleanResult`. ([`foq/schemas.py:118`](../foq/schemas.py#L118))

---

### `BooleanResult`, `BoolResult`, `NoulResult`

```python
@dataclass
class BooleanResult:
    answer: bool
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
```

*Definition*: [`foq/schemas.py:19-24`](../foq/schemas.py#L19-L24) (aliases `BoolResult` at [`foq/schemas.py:30`](../foq/schemas.py#L30), `NoulResult` at [`foq/schemas.py:31`](../foq/schemas.py#L31)).

- `answer`: Boolean verdict (`True` if option `"A"` selected, `False` otherwise).
- `confidence`: Calibrated probability associated with `answer`.
- `probabilities`: Mapping containing `"yes"` and `"no"` probability values.
- `latency_ms`: Round-trip duration in milliseconds.

---

### `Choice`

Categorical decision primitive selecting an option from a dictionary of choices.

*Definition*: [`foq/schemas.py:134`](../foq/schemas.py#L134)

#### Constructor

```python
def __init__(self, instructions: str, choices: Dict[str, str])
```

*Definition*: [`foq/schemas.py:141-151`](../foq/schemas.py#L141-L151)

- `instructions`: Question or prompt directive.
- `choices`: Mapping of categorical identifiers to descriptive labels, e.g. `{"billing": "Billing issue", "tech": "Technical support"}`. Automatically assigned letter keys (`A`, `B`, ...).

#### Methods

- `parse_result(self, raw_result: Dict[str, Any]) -> ChoiceResult`: Maps selected letter back to user choice key and returns a `ChoiceResult`. ([`foq/schemas.py:153`](../foq/schemas.py#L153))

---

### `ChoiceResult`

```python
@dataclass
class ChoiceResult:
    choice: str
    label: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
```

*Definition*: [`foq/schemas.py:35-41`](../foq/schemas.py#L35-L41)

- `choice`: Selected choice key from the input dictionary.
- `label`: Label corresponding to `choice`.
- `confidence`: Calibrated probability of the selected choice.
- `probabilities`: Probability distribution mapped to choice keys.
- `latency_ms`: Elapsed duration in milliseconds.

---

### `Score`

Ordinal or numeric evaluation primitive over an ordered dictionary of levels.

*Definition*: [`foq/schemas.py:167`](../foq/schemas.py#L167)

#### Constructor

```python
def __init__(self, instructions: str, levels: Dict[str, str])
```

*Definition*: [`foq/schemas.py:174-183`](../foq/schemas.py#L174-L183)

- `instructions`: Evaluation directive.
- `levels`: Ordered mapping of level identifiers to descriptions (e.g., `{"1": "Calm", "2": "Irritated", "3": "Angry"}`).

#### Methods

- `parse_result(self, raw_result: Dict[str, Any]) -> ScoreResult`: Computes expected score if keys are numeric (probability-weighted sum) or returns the modal level. ([`foq/schemas.py:185`](../foq/schemas.py#L185))

---

### `ScoreResult`

```python
@dataclass
class ScoreResult:
    score: Union[float, str]
    level: str
    confidence: float
    probabilities: Dict[str, float]
    latency_ms: float
```

*Definition*: [`foq/schemas.py:48-54`](../foq/schemas.py#L48-L54)

- `score`: Expected value (`float`) when levels are numeric strings, or the chosen level identifier (`str`).
- `level`: Level identifier having the highest probability.
- `confidence`: Confidence of the selected level.
- `probabilities`: Probability distribution across level keys.
- `latency_ms`: Elapsed duration in milliseconds.

---

### `BinaryChoice`

```python
def __init__(
    self,
    name: str,
    question: str,
    true_label: str = "Oui",
    false_label: str = "Non",
)
```

*Definition*: [`foq/schemas.py:204-212`](../foq/schemas.py#L204-L212)

Constructs a `DecisionSchema` with two options (`A` mapped to `true_label`, `B` mapped to `false_label`).

---

### `ClassificationChoice`

```python
def __init__(self, name: str, question: str, categories: List[str])
```

*Definition*: [`foq/schemas.py:215-224`](../foq/schemas.py#L215-L224)

Constructs a `DecisionSchema` assigning options (`A` through `J`) to elements in `categories` (truncated to 10 elements).

---

### `Structure`

Structured extraction primitive supporting Pydantic models and raw JSON Schema dictionaries.

*Definition*: [`foq/schemas.py:227`](../foq/schemas.py#L227)

#### Constructor

```python
def __init__(self, target: Any, instructions: Optional[str] = None)
```

*Definition*: [`foq/schemas.py:234-245`](../foq/schemas.py#L234-L245)

- `target`: Pydantic `BaseModel` class (exposing `.model_json_schema()`) or raw JSON Schema `dict`.
- `instructions`: System instruction directive. Defaults to `"Extrais les informations sous forme JSON strict."`.

#### Methods

- `format_prompt(self, context: str) -> str`: Formats ChatML prompt with system directive and user data tags. ([`foq/schemas.py:247`](../foq/schemas.py#L247))
- `parse_result(self, raw_json_str: str) -> Any`: Validates JSON string via Pydantic (`target.model_validate(data)`) or returns parsed `dict`. ([`foq/schemas.py:264`](../foq/schemas.py#L264))

---

## 3. Security Guard and Middleware (`foq.security`)

### `SecurityVerdict`

```python
@dataclass
class SecurityVerdict:
    is_safe: bool
    threat_type: str
    confidence: float
    latency_ms: float
    reason: str

    def to_dict(self) -> Dict[str, Any]
```

*Definition*: [`foq/security.py:16-31`](../foq/security.py#L16-L31)

- `is_safe`: `True` if classified as benign (`CLEAN`), `False` otherwise.
- `threat_type`: Categorization: `"CLEAN"`, `"PROMPT_INJECTION"`, `"MALICIOUS_PAYLOAD"`, or `"ENGINE_UNAVAILABLE"`.
- `confidence`: Decision confidence value.
- `latency_ms`: Elapsed execution time in milliseconds.
- `reason`: Classification label or error message.

---

### `FoqSecurityGuard`

Security auditor classifying incoming text payloads against prompt injection, jailbreaks, and exploits.

*Definition*: [`foq/security.py:34`](../foq/security.py#L34)

#### Constructor

```python
def __init__(self, engine: Optional[FoqEngine] = None)
```

*Definition*: [`foq/security.py:37-47`](../foq/security.py#L37-L47)

Initializes guard with an existing or default `FoqEngine` and prepares an internal `ClassificationChoice` audit schema.

#### Methods

```python
def inspect(self, text: str) -> SecurityVerdict
async def inspect_async(self, text: str) -> SecurityVerdict
```

*Definition*: [`foq/security.py:49-78`](../foq/security.py#L49-L78) (`inspect`), [`foq/security.py:80-109`](../foq/security.py#L80-L109) (`inspect_async`).

Audits input text. Implements a fail-closed strategy: if the engine is unreachable, returns `is_safe=False` with `threat_type="ENGINE_UNAVAILABLE"`.

---

### `FoqSecurityMiddleware`

ASGI middleware for FastAPI and Starlette applications.

*Definition*: [`foq/security.py:112`](../foq/security.py#L112)

#### Constructor

```python
def __init__(
    self,
    app,
    guard: Optional[FoqSecurityGuard] = None,
    block_threats: bool = True,
)
```

*Definition*: [`foq/security.py:119-122`](../foq/security.py#L119-L122)

- `app`: ASGI application instance.
- `guard`: Optional `FoqSecurityGuard` instance (defaults to a fresh instance).
- `block_threats`: When `True`, returns HTTP 403 Forbidden on unsafe POST/PUT/PATCH bodies.

#### Invocation

```python
async def __call__(self, scope, receive, send)
```

*Definition*: [`foq/security.py:124-172`](../foq/security.py#L124-L172)

---

## 4. Calibration (`foq.calibration`)

### `TemperatureScaler`

Implements temperature scaling (Platt scaling) to scale logit distributions prior to normalization.

*Definition*: [`foq/calibration.py:88`](../foq/calibration.py#L88)

#### Constructor

```python
def __init__(self, temperature: float = 1.0)
```

*Definition*: [`foq/calibration.py:94-95`](../foq/calibration.py#L94-L95)

#### Methods

- `scale_logits(self, logits: Dict[str, float]) -> Dict[str, float]`: Divides logits by `temperature`. ([`foq/calibration.py:97`](../foq/calibration.py#L97))
- `scale_probabilities(self, logprobs: Dict[str, float]) -> Dict[str, float]`: Converts log probabilities to temperature-scaled, softmax-normalized probabilities. ([`foq/calibration.py:103`](../foq/calibration.py#L103))
- `fit(self, dataset: List[Dict[str, Any]]) -> float`: Optimizes temperature parameter on a calibration dataset to minimize negative log-likelihood (NLL). ([`foq/calibration.py:118`](../foq/calibration.py#L118))

---

### `ExpectedCalibrationError`

Computes Expected Calibration Error (ECE) across confidence partitions.

*Definition*: [`foq/calibration.py:31`](../foq/calibration.py#L31)

#### Constructor

```python
def __init__(self, n_bins: int = 10)
```

*Definition*: [`foq/calibration.py:38-39`](../foq/calibration.py#L38-L39)

#### Methods

- `compute(self, confidences: List[float], correctness: List[bool]) -> Dict[str, Any]`: Computes overall ECE and per-bin gap metrics. ([`foq/calibration.py:41`](../foq/calibration.py#L41))

---

### `BrierScore`

Computes Brier score for probabilistic predictions.

*Definition*: [`foq/calibration.py:15`](../foq/calibration.py#L15)

#### Methods

```python
@staticmethod
def compute(probabilities: List[float], outcomes: List[int]) -> float
```

*Definition*: [`foq/calibration.py:18-28`](../foq/calibration.py#L18-L28)

Computes mean squared error between probabilities and binary outcomes.

---

### `CalibrationProfile`

Saves and loads calibrated temperature profiles to and from JSON files.

*Definition*: [`foq/calibration.py:155`](../foq/calibration.py#L155)

#### Constructor

```python
def __init__(self, filepath: str = _DEFAULT)
```

*Definition*: [`foq/calibration.py:160-166`](../foq/calibration.py#L160-L166)

#### Methods

- `load(self) -> bool`: Reads calibration parameters from disk. ([`foq/calibration.py:168`](../foq/calibration.py#L168))
- `save(self) -> None`: Writes calibration parameters to disk. ([`foq/calibration.py:183`](../foq/calibration.py#L183))

---

## 5. Browser Automation (`foq.browser`)

### `FoqBrowserAgent`

Autonomous browser controller operating via Playwright.

*Definition*: [`foq/browser/agent.py:63`](../foq/browser/agent.py#L63)

#### Constructor

```python
def __init__(
    self,
    engine: Optional[FoqEngine] = None,
    headless: bool = True,
    max_steps: int = 12,
    step_delay_ms: int = 80,
)
```

*Definition*: [`foq/browser/agent.py:66-76`](../foq/browser/agent.py#L66-L76)

#### Methods

```python
def run(
    self,
    goal: str,
    start_url: str,
    params: Optional[Dict[str, str]] = None,
    html_content: Optional[str] = None,
) -> BrowserRunResult
```

*Definition*: [`foq/browser/agent.py:111-117`](../foq/browser/agent.py#L111-L117)

Navigates Playwright Chromium instance towards `goal`, selecting actions based on pruned DOM state.

---

### `DOMPruner`

DOM extractor filtering raw web pages into structured interactive representations.

*Definition*: [`foq/browser/pruner.py:154`](../foq/browser/pruner.py#L154)

#### Methods

- `extract_interactive_elements(page) -> List[InteractiveElement]`: Evaluates page DOM script and returns interactive candidates. ([`foq/browser/pruner.py:158`](../foq/browser/pruner.py#L158))
- `extract_page_state(page) -> Tuple[List[InteractiveElement], str]`: Evaluates page DOM script and returns elements along with text snippets. ([`foq/browser/pruner.py:164`](../foq/browser/pruner.py#L164))
- `format_state(goal: str, current_url: str, page_title: str, elements: List[InteractiveElement], page_snippets: Optional[str] = None, last_action_feedback: Optional[str] = None) -> str`: Formats state into compact textual representation. ([`foq/browser/pruner.py:184`](../foq/browser/pruner.py#L184))

---

### Supporting Browser Dataclasses

- `BrowserStep`: Details individual navigation actions (`foq/browser/agent.py:17-30`).
- `BrowserRunResult`: Comprehensive result of an agent run (`foq/browser/agent.py:33-43`).
- `InteractiveElement`: Parsed DOM element with identifier, tag, label, and selector (`foq/browser/pruner.py:12-28`).

---

## 6. Command-Line Interface (`foq` CLI)

The CLI entrypoint is defined in [`foq/cli.py`](../foq/cli.py).

```
foq <command> [options]
```

### Commands

#### `foq setup`
- *Handler*: `cmd_setup` ([`foq/cli.py:74`](../foq/cli.py#L74))
- *Arguments*: None.
- *Function*: Downloads the required GGUF model file to `~/.models/foq/`, verifies its SHA-256 checksum, checks local inference runtime compatibility in `~/.local/bin/foq-llama/`, and downloads the optional decision adapter if present.

#### `foq serve`
- *Handler*: `cmd_serve` ([`foq/cli.py:26`](../foq/cli.py#L26))
- *Arguments*: None.
- *Function*: Launches the local inference server via `start_foq_server.cmd` on Windows or `start_foq_server.sh` on Unix.

#### `foq demo`
- *Handler*: `cmd_demo` ([`foq/cli.py:69`](../foq/cli.py#L69))
- *Arguments*: None.
- *Function*: Starts an interactive terminal demonstration (`python -m foq.demo`).

#### `foq inspect`
- *Handler*: `cmd_inspect` ([`foq/cli.py:47`](../foq/cli.py#L47))
- *Arguments*: `text` (positional, `nargs="+"`, string payload to audit).
- *Function*: Audits input string against security threats and prompt injection using `FoqSecurityGuard`.

#### `foq benchmark`
- *Handler*: `cmd_benchmark` ([`foq/cli.py:42`](../foq/cli.py#L42))
- *Arguments*: None.
- *Function*: Executes the benchmark suite (`python -m foq.bench`).

---

## 7. `needs_review` Threshold Mechanics

The `needs_review` flag signals when a decision's calibrated confidence is below a specified threshold, allowing upstream applications to route uncertain cases to fallback handlers or human reviewers.

Its application differs between `decide()` and `system_one()`:

### In `decide` and `decide_async`

In `decide` and `decide_async`, the threshold resolution is:

```python
seuil = min_confidence if min_confidence is not None else self.min_confidence
if seuil is not None and result.get("success"):
    result["needs_review"] = result["confidence"] < seuil
```

- *Code citations*: [`foq/engine.py:217-219`](../foq/engine.py#L217-L219) (synchronous), [`foq/engine.py:252-254`](../foq/engine.py#L252-L254) (asynchronous).
- **Default behavior**: The `FoqEngine` constructor initializes `min_confidence` to `SEUIL_REVIEW_MESURE` (`0.8`), defined at [`foq/engine.py:21`](../foq/engine.py#L21) and assigned at [`foq/engine.py:64`](../foq/engine.py#L64).
- If the caller passes no `min_confidence` parameter to `decide()`, `seuil` defaults to `self.min_confidence` (`0.8`). Therefore, `result["needs_review"]` is populated as a `bool` by default.

### In `system_one` and `system_one_async`

In `system_one` and `system_one_async`, the parameter default is `None`:

```python
min_confidence: Optional[float] = None
```

- *Code citations*: [`foq/engine.py:404`](../foq/engine.py#L404) (synchronous signature), [`foq/engine.py:461`](../foq/engine.py#L461) (asynchronous signature).
- Unlike `decide()`, `system_one()` **does not** fall back to `self.min_confidence`. It evaluates thresholds only when `min_confidence is not None`:

```python
if min_confidence is not None:
    for key, res in parsed_results.items():
        raw_conf = getattr(res, "confidence", None)
        if raw_conf is not None:
            res.needs_review = raw_conf < min_confidence

...
if min_confidence is not None:
    response.needs_review = [
        k for k, res in parsed_results.items() if getattr(res, "needs_review", False)
    ]
```

- *Code citations*: [`foq/engine.py:442-453`](../foq/engine.py#L442-L453) (synchronous), [`foq/engine.py:505-516`](../foq/engine.py#L505-L516) (asynchronous).
- If `min_confidence` is omitted when calling `system_one()`, neither the individual result items nor `response.needs_review` receive the flag.

---

## Code Examples

### 1. `FoqEngine` Context Manager and `is_server_ready`

```python
from foq import FoqEngine

with FoqEngine(base_url="http://127.0.0.1:8089") as engine:
    ready = engine.is_server_ready()
    print(f"Server ready: {ready}")
```

### 2. `decide` with `DecisionSchema` and `needs_review`

```python
from foq import FoqEngine, BinaryChoice

engine = FoqEngine()
schema = BinaryChoice(
    name="order_confirmation",
    question="Does the customer confirm their purchase?",
    true_label="Confirmed",
    false_label="Cancelled",
)

result = engine.decide(
    context="Yes, please charge my card and ship the item.",
    schema=schema,
    min_confidence=0.85,
)

print(result["decision_label"])
print(result["confidence"])
print(result["needs_review"])
engine.close()
```

### 3. Asynchronous `decide_async`

```python
import asyncio
from foq import FoqEngine, Boolean

async def main():
    engine = FoqEngine()
    schema = Boolean("Is this an urgent inquiry?")
    result = await engine.decide_async("Server down in production environment", schema)
    print(result["decision_key"])
    engine.close()

asyncio.run(main())
```

### 4. `decide_multi` (Concurrent Synchronous Evaluation)

```python
from foq import FoqEngine, Boolean, Choice

engine = FoqEngine()
schemas = [
    Boolean("Is the user asking for a refund?"),
    Choice("Classify the request department", {
        "sales": "Sales department",
        "support": "Technical support",
        "billing": "Billing and invoicing",
    }),
]

multi_result = engine.decide_multi(
    context="I was double charged on my invoice and want my money back.",
    schemas=schemas,
    max_workers=2,
)

print(multi_result["structured_output"])
engine.close()
```

### 5. `extract` with a Pydantic Model

```python
from pydantic import BaseModel
from foq import FoqEngine, Structure

class UserContact(BaseModel):
    name: str
    email: str

engine = FoqEngine()
contact = engine.extract(
    state="Hello, my name is Alex Doe and you can reach me at alex@example.com",
    schema=Structure(target=UserContact),
)

print(contact.name, contact.email)
engine.close()
```

### 6. `system_one` with Primitives and `min_confidence`

```python
from foq import FoqEngine, Boolean, Choice, Score

engine = FoqEngine()
response = engine.system_one(
    state="Payment received, shipment dispatched yesterday.",
    questions={
        "shipped": Boolean("Has the item been shipped?"),
        "status": Choice("Select fulfillment status", {
            "pending": "Pending fulfillment",
            "shipped": "Dispatched",
            "delivered": "Delivered",
        }),
        "urgency": Score("Rate request priority", {
            "1": "Low",
            "2": "Medium",
            "3": "High",
        }),
    },
    min_confidence=0.8,
)

print(response.shipped.answer)
print(response.status.choice)
print(response.urgency.score)
print(response.needs_review)
engine.close()
```

### 7. `FoqSecurityGuard` Real-Time Inspection

```python
from foq import FoqSecurityGuard

guard = FoqSecurityGuard()
verdict = guard.inspect("Please summarize the attached document.")
print(verdict.is_safe)
print(verdict.threat_type)
print(verdict.to_dict())
```

### 8. `FoqSecurityMiddleware` Integration in FastAPI

```python
from fastapi import FastAPI
from foq import FoqSecurityMiddleware, FoqSecurityGuard

app = FastAPI()
app.add_middleware(FoqSecurityMiddleware, guard=FoqSecurityGuard(), block_threats=True)

@app.post("/submit")
async def handle_submit(payload: dict):
    return {"status": "accepted"}
```

---

## 8. Sources

The definitions and behaviors documented above were extracted from:
- `foq/__init__.py`
- `foq/engine.py`
- `foq/schemas.py`
- `foq/security.py`
- `foq/calibration.py`
- `foq/browser/__init__.py`
- `foq/browser/agent.py`
- `foq/browser/pruner.py`
- `foq/cli.py`
