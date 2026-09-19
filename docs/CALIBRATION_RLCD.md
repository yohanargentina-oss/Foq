# 📐 Calibration Theory & RLCD in Foq

This document presents the mathematical principles and statistical calibration protocol built into **Foq**.

---

## 1. The Overconfidence Problem (*Miscalibration*)

Deep learning models trained with the classic Cross-Entropy Loss suffer from a well-documented systematic bias (Guo et al., 2017):
> **A model that predicts a raw probability of 99% is in practice right only 70% or 80% of the time.**

For a conversational agent or a recreational chatbot, this overconfidence is tolerable. For an **autonomous decision engine (System 1)** whose verdicts trigger real production actions (security blocking, financial transactions, autonomous navigation), a miscalibrated probability is unacceptable.

---

## 2. What is RLCD?

**RLCD** (*Reinforcement Learning for Calibrated Decisions*) is the training and evaluation paradigm promoted for Foq-style decision models.

Unlike traditional RLHF (which maximizes a subjective reward derived from human preferences in dialogue), RLCD relies on **Strictly Proper Scoring Rules**:

### The Brier Score
For a sample of $N$ predictions with stated probabilities $p_i$ and actual binary outcomes $y_i \in \{0, 1\}$:
$$BS = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$

The Brier Score mathematically guarantees that stating the exact probability of an event minimizes the penalty. Any drift towards over- or under-confidence is penalized quadratically.

---

## 3. Expected Calibration Error (ECE)

The **ECE** measures the mean absolute gap between the confidence stated by the model and its actual empirical accuracy.

The probability space $[0, 1]$ is partitioned into $M$ sub-intervals (*bins*) $B_m$:
$$ECE = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

* $\text{acc}(B_m)$: proportion of correct predictions in group $B_m$.
* $\text{conf}(B_m)$: average confidence stated by the model in group $B_m$.

A perfectly calibrated model reaches **$ECE = 0.0$**: when it assigns 80% confidence to a batch of hypotheses, exactly 80% of them turn out true.

---

## 4. Implementation in Foq: Temperature Scaling

In Foq, post-hoc calibration is performed by **Temperature Scaling**:

For a vector of raw logits $z_1, z_2, \dots, z_K$, we introduce a scalar parameter $T^* > 0$ learned on a dedicated validation set:

$$\hat{p}_i(T^*) = \frac{\exp(z_i / T^*)}{\sum_{j=1}^K \exp(z_j / T^*)}$$

### Mathematical Properties
1. **Strict rank preservation**: for any $T^* > 0$, $\arg\max_i \hat{p}_i(T^*) = \arg\max_i z_i$. The final decision is never changed by calibration.
2. **Certainty regularization**: when the neural network is overconfident, $T^* > 1$ softens the probability distribution to make it match statistical reality.
3. **Convex optimization**: the optimal $T^*$ is found by minimizing the Negative Log-Likelihood (NLL) on a calibration dataset via Brent's bounded scalar optimization algorithm (`scipy.optimize.minimize_scalar`).

---

## 5. Operational Calibration Lifecycle

### 5.1 Persistence File (`calibration_profile.json`)
When `FoqEngine` loads, the `calibration_profile.json` file at the project root is read automatically. It contains:
```json
{
  "model_alias": "foq",
  "temperature": 0.1000046,
  "ece": 2.91e-08,
  "brier_score": 4.28e-15,
  "timestamp": "2026-09-18T19:19:30.054463"
}
```

### 5.2 Model Re-calibration
To recompute and optimize calibration on new data:
```bash
python scripts/run_calibration.py
```
The script computes the new $T^*$, updates `calibration_profile.json` and prints the ECE improvement before and after calibration.
