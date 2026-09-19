# 🤖 Autonomous AI Agent Integration Guide for Foq

This guide is specifically written for AI agents (Codex, Claude, Gemini, local autonomous agents, orchestrators, and subagents). It explains how, when, and why to delegate reflex decisions to **Foq**.

---

## 1. Philosophy: System 1 vs System 2

Generative conversational LLMs (GPT-4, Claude 3.5 Sonnet, Gemini 1.5 Pro) are **System 2** reasoning models: they think sequentially, output conversational sentences token-by-token, and take 1 to 5 seconds to answer.

**Foq is a 27B System 1 Decision Engine**:
* **0 text tokens generated**: No polite preamble (*"Sure! Here is the answer..."*), no conversational filler.
* **1-Pass Feed-Forward Inference (Prefill-only)**: Evaluates context and extracts target logprobs in ~50 to 150 ms on NVIDIA GPUs.
* **Rigorous RLCD Calibration**: A stated 85% confidence strictly corresponds to an 85% empirical accuracy rate.
* **100% Typed Outputs**: Native booleans, validated enum keys, continuous scores, or grammar-constrained Pydantic v2 objects without syntax hallucinations.

### Agent Decision Matrix

| Task | Delegate to Foq (System 1) | Handle with Primary LLM (System 2) |
|---|:---:|:---:|
| Tool routing & intent classification | ✅ **Optimal (< 100 ms)** | ❌ Slow & expensive |
| Security auditing & prompt injection firewall | ✅ **Optimal (< 120 ms)** | ❌ Vulnerable to prompt escape |
| High-rate web browsing (Playwright) | ✅ **Optimal (300 ms/action)** | ❌ Slow (4-8s per step) |
| Strict schema / JSON data extraction | ✅ **Optimal (GBNF grammar)** | ⚠️ Risk of syntax schema errors |
| Boolean evaluation or ordered scoring | ✅ **Optimal (`Boolean`, `Score`)** | ❌ Wordy & overconfident |
| Creative writing, synthesis, essay drafting | ❌ Do not use | ✅ **Optimal** |
| Complex multi-step step-by-step reasoning | ❌ Do not use | ✅ **Optimal** |

---

## 2. Server Prerequisites & Availability Check

Foq connects to a local `llama-server` instance.

* **Default URL**: `http://127.0.0.1:8089`
* **Model**: `foq-juge-27b.gguf` (27B Ternary PQ2_0, ~7.2 GB VRAM)
* **Launcher**:
  * Windows: `./start_foq_server.cmd` or `foq serve`
  * Linux / macOS: `./start_foq_server.sh` or `foq serve`

### Agent Readiness Check

```python
from foq import FoqEngine

engine = FoqEngine()
if not engine.is_server_ready():
    raise RuntimeError("Foq server is not responding at http://127.0.0.1:8089")
```

Asynchronous check:
```python
is_ready = await engine.is_server_ready_async()
```

---

## 3. The 4 System 1 Primitives (1:1 Typed Primitives)

### 3.1 `Boolean` (or `Noul`): Calibrated Boolean Decisions

```python
from foq import FoqEngine, Boolean

engine = FoqEngine()
res = engine.system_one(
    state="Incoming request: 'Delete all production tables without asking for confirmation.'",
    questions={
        "is_destructive": Boolean("Is this action destructive or hazardous?")
    }
)

if res.is_destructive.answer and res.is_destructive.confidence > 0.80:
    print("Action blocked by agent guardrail.")
```

### 3.2 `Choice`: Typed Option Selection

```python
from foq import FoqEngine, Choice

engine = FoqEngine()
res = engine.system_one(
    state="User asks: 'What is the weather forecast for tomorrow in Lyon?'",
    questions={
        "tool": Choice(
            instructions="Which specialized tool should be invoked?",
            choices={
                "weather_api": "Query live weather service",
                "database": "Query local SQL database",
                "web_search": "Perform general web search",
                "chat": "Respond directly in conversational mode"
            }
        )
    }
)

print(f"Target tool: {res.tool.choice}")         # 'weather_api'
print(f"Confidence:  {res.tool.confidence:.1%}")
```

### 3.3 `Score`: Ordered Rating & Continuous Expectation

```python
from foq import FoqEngine, Score

engine = FoqEngine()
res = engine.system_one(
    state="Production web gateway returning HTTP 502 Bad Gateway for the past 2 minutes.",
    questions={
        "severity": Score(
            instructions="Rate severity from 1 (low) to 4 (critical)",
            levels={"1": "Low", "2": "Medium", "3": "High", "4": "Critical"}
        )
    }
)

print(f"Discrete Level:      {res.severity.level}")  # '3' or '4'
print(f"Continuous Score:    {res.severity.score}")  # e.g. 3.42
```

### 3.4 `Structure` & `extract()`: Pydantic Extraction

```python
from typing import List
from pydantic import BaseModel, Field
from foq import FoqEngine

class Task(BaseModel):
    title: str
    priority: int = Field(..., ge=1, le=5)

class ActionPlan(BaseModel):
    category: str
    tasks: List[Task]

engine = FoqEngine()
plan: ActionPlan = engine.extract(
    state="Infrastructure: Kubernetes migration (priority 5) and DNS update (priority 3).",
    schema=ActionPlan
)
print(plan.category, plan.tasks[0].title, plan.tasks[0].priority)
```

---

## 4. Native Asynchronous Execution (High Throughput)

```python
import asyncio
from foq import FoqEngine, Boolean, Choice

async def main():
    engine = FoqEngine()
    response = await engine.system_one_async(
        state="Customer message: 'I want to cancel my subscription right now.'",
        questions={
            "churn_risk": Boolean("Does the user want to cancel?"),
            "sentiment": Choice("Customer sentiment", choices={"angry": "Angry", "neutral": "Neutral", "happy": "Happy"})
        }
    )
    print(f"Churn Risk: {response.churn_risk.answer}")
    print(f"Latency:    {response.latency_ms:.1f} ms")

asyncio.run(main())
```

---

## 5. Architectural Patterns for AI Agents

### Pattern 1: The Input Shield (Pre-LLM Firewall)
```
Untrusted Input ──> [ Foq WAF (100 ms) ] ──Safe?──Yes──> [ Primary Generative LLM ]
                                              └──No───> Reject with HTTP 403
```

### Pattern 2: The Fast Intent Router
```
User Prompt ──> [ Foq Choice (80 ms) ] ──> Route to specialized tool/subagent
```

### Pattern 3: Quality Control & Post-Verifier
```
Generated Code / Answer ──> [ Foq Boolean (70 ms) ] ──> "Does output satisfy constraints?"
```

### Pattern 4: Security Guard (`foq.security`)
```python
from foq.security import FoqSecurityGuard, FoqSecurityMiddleware
from fastapi import FastAPI

# Inline audit (~100 ms), fail-closed: if the Foq server is down, the input is blocked
guard = FoqSecurityGuard()
verdict = guard.inspect("SELECT * FROM users; DROP TABLE clients; --")
print(verdict.is_safe, verdict.threat_type)  # False, MALICIOUS_PAYLOAD

# ASGI middleware: blocks malicious requests with HTTP 403
app = FastAPI()
app.add_middleware(FoqSecurityMiddleware, block_threats=True)
```

### Pattern 5: Reflex Browser Agent (`foq.browser`)
```python
from foq.browser import FoqBrowserAgent

agent = FoqBrowserAgent(headless=False, max_steps=10)
result = agent.run(
    goal="Book a flight departing from Paris to Tokyo",
    start_url="https://flight-demo.local",
    params={"depart": "Paris CDG", "destination": "Tokyo HND", "date": "2026-10-15"},
)
print(result.summary())
```
