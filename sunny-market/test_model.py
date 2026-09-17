# test_model.py  -- give the model the pop quiz.  Run `python test_model.py --base` to quiz the UNtrained model.
import json, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import json, sys, os, torch
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

#MODEL = "./base/Qwen2.5-0.5B-Instruct"        # local folder

MODEL   = "./base/Qwen2.5-0.5B-Instruct"   

#MODEL = "unsloth/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32)
if "--base" not in sys.argv:
    model = PeftModel.from_pretrained(model, "lora_qwen05b")   # your trained adapter

#    model = PeftModel.from_pretrained(model, "lora_qwen05b")   # attach the sticky notes
model.eval()

def ask(messages):
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**ids, do_sample=False)
    return tokenizer.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True).strip()

right = total = 0
for line in open("test.jsonl"):
    msgs = json.loads(line)["messages"]
    expected = msgs[-1]["content"]
    answer = ask(msgs[:-1])            # everything except the answer
    ok = (answer == expected)
    right += ok
    total += 1
    print(("PASS" if ok else "FAIL"), "|", msgs[1]["content"], "->", answer)

print(f"\nScore: {right}/{total} exactly right")