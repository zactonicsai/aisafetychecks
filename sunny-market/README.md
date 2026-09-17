Here is a **copy-paste training prompt** you can drop into a notebook, a coding agent, or Unsloth Studio. It is written for a **tiny SLM**, **CPU-only Unsloth LoRA**, then **GGUF + Ollama**.

Unsloth’s speed tricks are GPU-first. On CPU, use a **0.5B–1.7B** instruct model, **LoRA (not QLoRA / 4-bit)**, short context, and a small dataset. 4-bit `bitsandbytes` needs CUDA. After training, quantize to **Q4_K_M** or **Q8_0** so Ollama stays CPU-friendly.

---

## Training prompt (give this to an agent or follow it yourself)

```text
Goal
Fine-tune a small instruct SLM with Unsloth on CPU only (no CUDA),
export GGUF, and create an Ollama model that runs locally.

Constraints
- Device: CPU only. Do not call CUDA, bitsandbytes 4-bit, or load_in_4bit=True.
- Base model (pick one that Unsloth supports; prefer the smallest that fits RAM):
  1) unsloth/Llama-3.2-1B-Instruct   (~16 GB RAM training)
  2) unsloth/Qwen2.5-0.5B-Instruct or unsloth/Qwen3.5-0.8B if available
  3) unsloth/gemma-3-1b-it or gemma-3-270m-it for ultra-light
- Training method: LoRA / PEFT only. Freeze base weights.
- max_seq_length: 512 or 1024 (not 2048+ on CPU).
- Dataset: 200–2000 high-quality instruction pairs in ChatML / messages format.
- Epochs: 1–3. Stop if eval loss rises.
- After train: merge LoRA, save GGUF, write Ollama Modelfile, ollama create.

Install (CPU torch first)
python -m pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install unsloth unsloth_zoo trl peft accelerate datasets transformers
# Do NOT install bitsandbytes on a CPU-only box.

Training script requirements
1. Force CPU:
   import os
   os.environ["CUDA_VISIBLE_DEVICES"] = ""
   os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"   # safer on CPU
   import torch
   assert not torch.cuda.is_available()

2. Load with FastLanguageModel.from_pretrained:
   model_name = "unsloth/Llama-3.2-1B-Instruct"
   max_seq_length = 512
   model, tokenizer = FastLanguageModel.from_pretrained(
       model_name = model_name,
       max_seq_length = max_seq_length,
       dtype = torch.float32,     # CPU-safe; bf16 only if CPU supports it
       load_in_4bit = False,
       load_in_8bit = False,
   )

3. Attach LoRA (small ranks for CPU):
   model = FastLanguageModel.get_peft_model(
       model,
       r = 8,
       lora_alpha = 16,
       lora_dropout = 0,
       bias = "none",
       target_modules = ["q_proj","k_proj","v_proj","o_proj",
                         "gate_proj","up_proj","down_proj"],
       use_gradient_checkpointing = "unsloth",
       random_state = 3407,
   )

4. Dataset format — each row:
   {"messages": [
     {"role": "system", "content": "You are a concise domain assistant."},
     {"role": "user", "content": "..."},
     {"role": "assistant", "content": "..."}
   ]}
   Apply tokenizer.apply_chat_template(..., tokenize=False, add_generation_prompt=False).
   Map to a "text" field for SFTTrainer.

5. SFTTrainer / SFTConfig:
   per_device_train_batch_size = 1
   gradient_accumulation_steps = 8
   num_train_epochs = 2
   learning_rate = 2e-4
   warmup_ratio = 0.05
   logging_steps = 5
   optim = "adamw_torch"          # not adamw_8bit on CPU
   weight_decay = 0.01
   max_seq_length = 512
   output_dir = "outputs-lora"
   fp16 = False
   bf16 = False
   dataloader_num_workers = 0
   report_to = "none"

6. After trainer.train():
   - Save LoRA: model.save_pretrained("lora_adapter"); tokenizer.save_pretrained("lora_adapter")
   - Export GGUF (this step is RAM-heavy; close other apps):
     model.save_pretrained_gguf(
         "gguf_out",
         tokenizer,
         quantization_method = "q4_k_m",   # or "q8_0" for higher quality
     )
   - If save_pretrained_gguf fails on CPU, fallback:
     a) model.save_pretrained_merged("merged_16bit", tokenizer, save_method="merged_16bit")
     b) convert with llama.cpp convert_hf_to_gguf.py then llama-quantize to Q4_K_M

7. Ollama handoff
   Unsloth usually writes gguf_out/Modelfile. If not, write:

   FROM ./gguf_out/unsloth.Q4_K_M.gguf
   PARAMETER temperature 0.3
   PARAMETER top_p 0.9
   PARAMETER num_ctx 2048
   SYSTEM """You are a concise domain assistant trained for [TASK]. Answer briefly and accurately."""

   Then:
   ollama create my-slm-cpu -f gguf_out/Modelfile
   ollama run my-slm-cpu "Test prompt matching the training task."

Success criteria
- Training completes without CUDA errors.
- Adapter folder exists.
- A .gguf file exists and ollama list shows my-slm-cpu.
- The model follows the trained style on 5 held-out prompts better than the base model.

Do not
- Use 7B+ models on CPU.
- Use load_in_4bit or bitsandbytes.
- Use max_seq_length > 1024.
- Train more than ~3 epochs on a tiny set (overfit).
```

---

## Ready-to-run skeleton

```python
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["UNSLOTH_COMPILE_DISABLE"] = "1"

import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

assert not torch.cuda.is_available(), "This script is CPU-only"

max_seq_length = 512
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-1B-Instruct",
    max_seq_length=max_seq_length,
    dtype=torch.float32,
    load_in_4bit=False,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=8,
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# Replace with your jsonl of {"messages":[...]}
ds = load_dataset("json", data_files="train.jsonl", split="train")

def to_text(ex):
    text = tokenizer.apply_chat_template(
        ex["messages"], tokenize=False, add_generation_prompt=False
    )
    return {"text": text}

ds = ds.map(to_text)

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=ds,
    args=SFTConfig(
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        num_train_epochs=2,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        logging_steps=5,
        optim="adamw_torch",
        weight_decay=0.01,
        max_seq_length=max_seq_length,
        output_dir="outputs-lora",
        fp16=False,
        bf16=False,
        report_to="none",
        seed=3407,
    ),
)
trainer.train()

model.save_pretrained("lora_adapter")
tokenizer.save_pretrained("lora_adapter")

model.save_pretrained_gguf(
    "gguf_out",
    tokenizer,
    quantization_method="q4_k_m",
)
```

Then:

```bash
ollama create my-slm-cpu -f gguf_out/Modelfile
ollama run my-slm-cpu
```

---

## Practical notes

| Piece | CPU reality |
|---|---|
| Train | LoRA on 0.5B–1B is doable; expect minutes–hours, not Unsloth GPU speed |
| QLoRA 4-bit | Skip — `bitsandbytes` is CUDA |
| Best Ollama quant after train | `q4_k_m` for size/speed; `q8_0` if quality matters |
| RAM | ~16 GB for 1B LoRA; 32 GB is more comfortable for GGUF export |
| Faster path | Train on a Colab/T4 GPU with the same script (`load_in_4bit=True`, `dtype=None`), export GGUF, run the GGUF on CPU Ollama |
