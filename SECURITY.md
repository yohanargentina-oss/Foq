# 🛡️ Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Reporting Vulnerabilities

Security is a core feature of Foq through its AI Web Application Firewall (`foq.security`) and prompt isolation mechanisms.

If you discover a security vulnerability, prompt injection evasion, or potential exploit in Foq:

1. **Do NOT file a public issue.**
2. Report the vulnerability privately via GitHub Security Advisories or by emailing the project maintainers.
3. Include detailed steps to reproduce the issue, including:
   - The adversarial payload or test case.
   - The observed behavior vs the expected behavior.
   - Model version and runtime environment (CUDA version, OS, Python version).

We commit to acknowledging your report within 48 hours and working collaboratively on a fix prior to public disclosure.

---

## Security Architecture in Foq

* **ChatML Sanitization**: Control tokens (`<|im_start|>`, `<|im_end|>`, `<think>`, `</think>`) are stripped from incoming contexts to prevent role escape attacks.
* **Passive Context Framing**: Context is wrapped inside `<donnees>` XML tags with strict system instructions that text inside tags is non-executable data.
* **Bounded Output Constraints**: System 1 decisions cut token generation at `n_predict = 1`, making traditional generative prompt leakage or text injection impossible.
