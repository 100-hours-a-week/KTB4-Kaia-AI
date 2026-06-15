import os
import time

import torch

from model import MiniGPT
from schemas import GenConfig
from tokenizer import Tokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENIZER_PATH = os.path.join(BASE_DIR, "checkpoints", "tokenizer.model")
CHECKPOINT_PATH = os.environ.get(
    "MINIGPT_CHECKPOINT", os.path.join(BASE_DIR, "checkpoints", "mini_gpt.pt")
)


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


device = get_device()
print(f"device: {device}")

ckpt = torch.load(CHECKPOINT_PATH, map_location=device, weights_only=False)
model = MiniGPT(**ckpt["config"]).to(device)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

tok = Tokenizer(TOKENIZER_PATH)


def run_generation(prompt: str, config: GenConfig) -> dict:
    ids = tok.encode(prompt)
    x = torch.tensor([ids], dtype=torch.long, device=device)

    start = time.perf_counter()
    out = model.generate(
        x,
        max_new_tokens=config.max_new_tokens,
        temperature=config.temperature,
        top_k=config.top_k,
        repetition_penalty=config.repetition_penalty,
    )
    elapsed = time.perf_counter() - start

    generated_text = tok.decode(out[0].tolist())
    new_tokens = out.shape[1] - x.shape[1]
    tokens_per_sec = new_tokens / elapsed if elapsed > 0 else 0.0

    return {
        "generated_text": generated_text,
        "elapsed_time": elapsed,
        "tokens_per_sec": tokens_per_sec,
    }
