# train_cpu.py  -- teach Qwen2.5-0.5B-Instruct the Sunny Market store map, on a CPU


import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"            # NEW: never talk to the Hub
os.environ["TRANSFORMERS_OFFLINE"] = "1"      # NEW


import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

torch.set_num_threads(os.cpu_count() or 4)     # let PyTorch use every CPU core
assert not torch.cuda.is_available(), "GPU is visible; this script is meant for CPU-only runs"

MODEL   = "./base/Qwen2.5-0.5B-Instruct"   

#MODEL   = "unsloth/Qwen2.5-0.5B-Instruct"       # same weights as Qwen/Qwen2.5-0.5B-Instruct
MAX_LEN = 512                                   # longest example we allow (in tokens)

# 1) Load the "student" (the model) and its "dictionary" (the tokenizer)
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32)  # older transformers: torch_dtype=

# 2) Add LoRA "sticky notes" instead of rewriting the whole model
lora = LoraConfig(
    r=8, lora_alpha=16, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(model, lora)
model.print_trainable_parameters()             # only ~1% of the model will change

# 3) Load the flashcards
ds = load_dataset("json", data_files="train.jsonl", split="train")
print("Example flashcard, exactly as the model sees it:")
print(tokenizer.apply_chat_template(ds[0]["messages"], tokenize=False, add_generation_prompt=False))

# 4) Study plan
args = SFTConfig(
    output_dir="outputs-qwen05b",
    per_device_train_batch_size=1,     # one flashcard at a time (small RAM)
    gradient_accumulation_steps=4,     # ...but update the notes after every 4 cards
    num_train_epochs=3,                # read the whole deck 3 times
    learning_rate=2e-4,                # how big each correction step is
    warmup_steps=0.05,                 # start gently
    weight_decay=0.01,                 # keep the notes tidy
    optim="adamw_torch",               # the plain PyTorch optimizer (no GPU tricks)
    max_length=MAX_LEN,                # NOTE: old TRL called this max_seq_length
    packing=False,
    gradient_checkpointing=False,      # set True if you run out of RAM (slower)
    fp16=False, bf16=False,            # full-size numbers on CPU
    use_cpu=True,
    dataloader_num_workers=0,
    logging_steps=5,                   # print the loss every 5 steps
    save_strategy="no",                # we save by hand at the end
    report_to="none",
    seed=3407,
)

# 5) Train (this is the slow part)
trainer = SFTTrainer(model=model, args=args, train_dataset=ds, processing_class=tokenizer)
trainer.train()

# 6) Save only the sticky notes (a few MB), plus the tokenizer
model.save_pretrained("lora_qwen05b")
tokenizer.save_pretrained("lora_qwen05b")
print("Saved LoRA adapter to lora_qwen05b/")