"""Mini GPT Pretraining (Stage 1: Next Token Prediction)

가벼운 로컬 테스트 (CPU/MPS, corpus 일부만 사용):
    python train.py --max-chars 5000000 --steps 200 --eval-interval 50 \
        --checkpoint checkpoints/mini_gpt_light.pt

전체 학습 (Colab GPU, project_final.md 기본 하이퍼파라미터):
    python train.py --steps 20000
"""

import argparse
import os
import time

import torch

from model import MiniGPT
from tokenizer import Tokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(BASE_DIR, "data", "corpus.txt")
TOKENIZER_PATH = os.path.join(BASE_DIR, "checkpoints", "tokenizer.model")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "checkpoints", "mini_gpt.pt")


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_batch(data: torch.Tensor, block_size: int, batch_size: int, device: str):
    idx = torch.randint(0, len(data) - block_size - 1, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in idx])
    y = torch.stack([data[i + 1:i + block_size + 1] for i in idx])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, train_data, val_data, block_size, batch_size, device, eval_iters):
    model.eval()
    out = {}
    for split, data in (("train", train_data), ("val", val_data)):
        losses = torch.zeros(eval_iters)
        for k in range(eval_iters):
            x, y = get_batch(data, block_size, batch_size, device)
            _, loss = model(x, y)
            losses[k] = loss.item()
        out[split] = losses.mean().item()
    model.train()
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=CORPUS_PATH)
    parser.add_argument("--tokenizer", default=TOKENIZER_PATH)
    parser.add_argument("--max-chars", type=int, default=None, help="corpus 앞부분 N자만 사용 (빠른 테스트용)")

    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--n-embd", type=int, default=256)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-layer", type=int, default=6)
    parser.add_argument("--dropout", type=float, default=0.1)

    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--eval-interval", type=int, default=500)
    parser.add_argument("--eval-iters", type=int, default=20)

    parser.add_argument("--checkpoint", default=CHECKPOINT_PATH)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = get_device()
    print(f"device: {device}")

    tok = Tokenizer(args.tokenizer)
    print(f"vocab size: {tok.vocab_size}")

    print("loading corpus...")
    with open(args.corpus, "r", encoding="utf-8") as f:
        text = f.read(args.max_chars) if args.max_chars else f.read()
    print(f"corpus chars: {len(text):,}")

    print("tokenizing...")
    ids = tok.encode(text)
    data = torch.tensor(ids, dtype=torch.long)
    print(f"corpus tokens: {len(data):,}")

    split_idx = int(0.9 * len(data))
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    print(f"train tokens: {len(train_data):,}, val tokens: {len(val_data):,}")

    model = MiniGPT(
        vocab_size=tok.vocab_size,
        block_size=args.block_size,
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        dropout=args.dropout,
    ).to(device)
    print(f"params: {sum(p.numel() for p in model.parameters()):,}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    start = time.time()
    for step in range(args.steps):
        x, y = get_batch(train_data, args.block_size, args.batch_size, device)
        _, loss = model(x, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % args.eval_interval == 0 or step == args.steps - 1:
            losses = estimate_loss(
                model, train_data, val_data, args.block_size, args.batch_size, device, args.eval_iters
            )
            elapsed = time.time() - start
            print(
                f"step {step}: train loss {losses['train']:.4f}, "
                f"val loss {losses['val']:.4f} ({elapsed:.1f}s)"
            )

    os.makedirs(os.path.dirname(args.checkpoint), exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": {
                "vocab_size": tok.vocab_size,
                "block_size": args.block_size,
                "n_embd": args.n_embd,
                "n_head": args.n_head,
                "n_layer": args.n_layer,
                "dropout": args.dropout,
            },
        },
        args.checkpoint,
    )
    print(f"saved checkpoint to {args.checkpoint}")


if __name__ == "__main__":
    main()
