"""
Entraînement QLoRA de l'adaptateur décision pour Ternary-Foq-Réflexe 8B.

- Charge les poids d'entraînement (safetensors) en 4-bit NF4 (bitsandbytes).
- Applique un LoRA (rang 16) sur les projections d'attention.
- Perte appliquée UNIQUEMENT sur le token de la lettre de réponse (comme l'inférence Foq,
  qui lit le logprob du premier token après « Réponse : [ »).
- Évalue la justesse argmax sur le jeu d'évaluation à la fin.
- Sauvegarde l'adaptateur PEFT dans --output (à convertir ensuite en GGUF avec
  convert_lora_to_gguf.py, puis à charger avec llama-server --lora).

Prérequis GPU : ~9-10 Go de VRAM libres (arrêter les serveurs llama pendant l'entraînement).
"""

import sys
import os
import json
import argparse

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ORDRE D'IMPORT CRITIQUE (Windows) :
# 1. datasets/pandas/pyarrow AVANT tout le reste (sinon access violation pyarrow)
# 2. transformers AVANT bitsandbytes (sinon segfault)
# Ne pas réordonner ces blocs.
import datasets  # noqa: F401 — préchargement obligatoire avant torch
import torch
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import bitsandbytes  # noqa: F401 — chargement explicite après transformers/peft

DEFAULT_BASE = os.path.join(os.path.expanduser("~"), ".models", "foq", "foq-reflex-8b-unpacked")
DEFAULT_DATA = os.path.join(os.path.dirname(__file__), "..", "data", "lora_dataset.jsonl")
DEFAULT_EVAL = os.path.join(os.path.dirname(__file__), "..", "data", "lora_dataset_eval.jsonl")


class DecisionDataset(Dataset):
    """Chaque exemple : prompt complet + 1 token cible (la lettre)."""

    def __init__(self, path, tokenizer, max_len=1024):
        self.items = []
        skipped = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                e = json.loads(line)
                prompt_ids = tokenizer(e["prompt"], add_special_tokens=False)["input_ids"]
                letter_ids = tokenizer(e["target_letter"], add_special_tokens=False)["input_ids"]
                if len(letter_ids) != 1:
                    skipped += 1
                    continue
                if len(prompt_ids) + 1 > max_len:
                    skipped += 1
                    continue
                self.items.append((prompt_ids, letter_ids[0], e.get("domain", "?")))
        if skipped:
            print(f"[!] {skipped} exemples ignorés (lettre multi-token ou prompt trop long)")
        print(f"[*] {len(self.items)} exemples chargés depuis {os.path.basename(path)}")

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        ids, letter_id, domain = self.items[idx]
        return {
            "input_ids": ids + [letter_id],
            "label_id": letter_id,
            "domain": domain,
        }


class Collator:
    """Pad à la longueur du batch ; labels = -100 partout sauf le token lettre final."""

    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, batch):
        maxlen = max(len(b["input_ids"]) for b in batch)
        input_ids, labels, attn = [], [], []
        for b in batch:
            ids = b["input_ids"]
            pad = maxlen - len(ids)
            input_ids.append(ids + [self.pad_id] * pad)
            attn.append([1] * len(ids) + [0] * pad)
            lab = [-100] * (len(ids) - 1) + [b["label_id"]] + [-100] * pad
            labels.append(lab)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attn, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


@torch.no_grad()
def eval_accuracy(model, tokenizer, dataset, batch_size=8):
    """Justesse argmax du token suivant sur le jeu d'évaluation."""
    model.eval()
    pad_id = tokenizer.eos_token_id or 0
    collate_only = Collator(pad_id)
    correct, total = 0, 0
    by_domain = {}
    # tri par longueur pour regrouper les batches
    order = sorted(range(len(dataset)), key=lambda i: len(dataset.items[i][0]))
    for i in range(0, len(order), batch_size):
        idxs = order[i : i + batch_size]
        batch = [dataset[j] for j in idxs]
        prompts = [b["input_ids"] for b in batch]
        maxlen = max(len(p) for p in prompts)
        input_ids = torch.tensor(
            [p + [pad_id] * (maxlen - len(p)) for p in prompts], device=model.device
        )
        attn = torch.tensor(
            [[1] * len(p) + [0] * (maxlen - len(p)) for p in prompts], device=model.device
        )
        logits = model(input_ids=input_ids, attention_mask=attn).logits
        for k, b in enumerate(batch):
            last = len(b["input_ids"]) - 1  # position du token lettre
            pred = int(torch.argmax(logits[k, last - 1]).item())
            ok = pred == b["label_id"]
            correct += ok
            total += 1
            d = b["domain"]
            by_domain.setdefault(d, [0, 0])
            by_domain[d][0] += ok
            by_domain[d][1] += 1
    model.train()
    print(f"\n[*] Justesse argmax sur l'évaluation : {correct}/{total} ({correct/max(1,total)*100:.1f}%)")
    for d, (c, t) in sorted(by_domain.items()):
        print(f"    {d:<22} {c}/{t} ({c/max(1,t)*100:.0f}%)")
    return correct / max(1, total)


def main():
    parser = argparse.ArgumentParser(description="Entraînement QLoRA de l'adaptateur décision Foq-Réflexe 8B.")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Dossier des poids safetensors unpacked")
    parser.add_argument("--data", default=DEFAULT_DATA)
    parser.add_argument("--eval", default=DEFAULT_EVAL)
    parser.add_argument("--output", default=os.path.join("adapters", "foq_decision_8b"))
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--max-steps", type=int, default=-1, help="Smoke test : nombre de pas (-1 = complet)")
    args = parser.parse_args()

    print("=" * 66)
    print("  ENTRAÎNEMENT QLORA — ADAPTATEUR DÉCISION POUR REFERENCE-8B")
    print(f"  Base : {args.base}")
    print(f"  Données : {args.data}")
    print("=" * 66)

    if not torch.cuda.is_available():
        print("[!] CUDA indisponible : l'entraînement exige un GPU NVIDIA.")
        return

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    print("[*] Chargement du modèle de base en 4-bit NF4 (premier chargement : quelques minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base,
        quantization_config=bnb,
        device_map={"": 0},
        dtype=torch.bfloat16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
                                            gradient_checkpointing_kwargs={"use_reentrant": False})

    lora = LoraConfig(
        r=args.rank,
        lora_alpha=args.rank * 2,
        lora_dropout=0.1,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    train_ds = DecisionDataset(args.data, tokenizer)
    eval_ds = DecisionDataset(args.eval, tokenizer) if os.path.exists(args.eval) else None

    targs = TrainingArguments(
        output_dir=os.path.join(args.output, "trainer_tmp"),
        num_train_epochs=args.epochs if args.max_steps < 0 else 1.0,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        logging_steps=10,
        save_strategy="no",
        report_to="none",
        optim="paged_adamw_8bit",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model,
        args=targs,
        train_dataset=train_ds,
        data_collator=Collator(tokenizer.pad_token_id),
    )

    print("[*] Entraînement en cours...")
    trainer.train()

    if eval_ds is not None and args.max_steps < 0:
        eval_accuracy(model, tokenizer, eval_ds)

    out = os.path.abspath(args.output)
    model.save_pretrained(out)
    tokenizer.save_pretrained(os.path.join(out, "tokenizer"))
    print(f"\n[+] Adaptateur sauvegardé : {out}")
    print("[>] Prochaine étape : conversion GGUF (voir docs/FINETUNING.md) puis llama-server --lora")


if __name__ == "__main__":
    main()
