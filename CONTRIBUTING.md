# 🤝 Contributing to Foq

Thank you for your interest in contributing to **Foq**! We welcome contributions to improve System 1 decision latency, calibration algorithms, schemas, security features, and integrations.

---

## 🛠️ Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yohanargentina-oss/foq.git
   cd foq
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   # Linux / macOS
   source .venv/bin/activate
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies in editable mode**:
   ```bash
   pip install -e ".[all]"
   ```

---

## 🧪 Running Tests

Before submitting any Pull Request, ensure all tests pass:

```bash
# Run unit tests
python -m unittest discover -s tests
```

Tests cover:
* 1:1 Jev compatibility (`Boolean`, `Choice`, `Score`).
* Complex hierarchical extraction with Pydantic v2 (up to 5 levels).
* Native asynchronous execution (`system_one_async`, `extract_async`).
* Security WAF (`FoqSecurityGuard` and ASGI middleware).
* DOM pruning and browser agent logic.

---

## 📐 Coding Guidelines

1. **Follow YAGNI & Simplicity**: Implement the minimum clean code that solves the issue without speculative complexity.
2. **Deterministic Outputs**: System 1 decisions must remain reproducible and strictly typed.
3. **Prompt Integrity**: Any new schema must sanitize control tokens (`<|im_start|>`, `<|im_end|>`, `<think>`) and enclose raw user context within passive `<donnees>` XML tags.
4. **Calibration Alignment**: Any change modifying probability extraction or logit processing must preserve rank ordering and be evaluated against the Expected Calibration Error (ECE) and Brier score.

---

## 📦 Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(schemas): add dynamic range support for Score"
   ```
3. Push to your fork and open a Pull Request against `main`.
4. Ensure your PR description explains the motivation, implementation details, and verification steps.

---

## 📜 License

By contributing to Foq, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
