"""Mini GPT Pretraining (Stage 1: Next Token Prediction).

토큰화:
    python prepare_data.py --corpus data/corpus.txt

전체 학습:
    python train.py

중단 후 이어서 학습:
    python train.py --resume checkpoints/mini_gpt.pt
"""

import argparse
import os
import time

import numpy as np
import torch

from model import MiniGPT
from tokenizer import Tokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_PATH = os.path.join(BASE_DIR, "data", "tokens.bin")
TOKENIZER_PATH = os.path.join(BASE_DIR, "checkpoints", "tokenizer.model")
CHECKPOINT_PATH = os.path.join(BASE_DIR, "checkpoints", "mini_gpt.pt")


def get_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_batch(data: np.memmap, block_size: int, batch_size: int, device: str):
    idx = np.random.randint(0, len(data) - block_size - 1, size=batch_size)
    x = torch.stack([torch.from_numpy(data[i:i + block_size].astype(np.int64)) for i in idx])
    y = torch.stack([torch.from_numpy(data[i + 1:i + block_size + 1].astype(np.int64)) for i in idx])
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
    parser.add_argument("--tokens", default=TOKENS_PATH, help="prepare_data.py로 생성한 tokens.bin 경로")
    parser.add_argument("--tokenizer", default=TOKENIZER_PATH)
    parser.add_argument("--max-tokens", type=int, default=None, help="tokens.bin 앞부분 N개 토큰만 사용 (빠른 테스트용)")

    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--n-embd", type=int, default=512)
    parser.add_argument("--n-head", type=int, default=8)
    parser.add_argument("--n-layer", type=int, default=12)
    parser.add_argument("--dropout", type=float, default=0.1)

    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--steps", type=int, default=30000)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--eval-interval", type=int, default=500)
    parser.add_argument("--eval-iters", type=int, default=20)

    parser.add_argument("--checkpoint", default=CHECKPOINT_PATH)
    parser.add_argument("--checkpoint-interval", type=int, default=2000, help="N step마다 체크포인트 저장 (resume용)")
    parser.add_argument("--resume", default=None, help="이전 체크포인트 경로 (지정 시 이어서 학습)")
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = get_device()
    print(f"device: {device}")

    tok = Tokenizer(args.tokenizer)
    print(f"vocab size: {tok.vocab_size}")

    print(f"loading tokens from {args.tokens} (memmap)...")
    data = np.memmap(args.tokens, dtype=np.uint16, mode="r")
    if args.max_tokens:
        data = data[:args.max_tokens]
    print(f"corpus tokens: {len(data):,}")

    split_idx = int(0.9 * len(data))
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    print(f"train tokens: {len(train_data):,}, val tokens: {len(val_data):,}")

    start_step = 0
    if args.resume and os.path.exists(args.resume):
        print(f"resuming from {args.resume}")
        ckpt = torch.load(args.resume, map_location=device, weights_only=False)
        model_config = ckpt["config"]
        model = MiniGPT(**model_config).to(device)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        start_step = ckpt["step"] + 1
        print(f"resumed at step {start_step}")
    else:
        model_config = dict(
            vocab_size=tok.vocab_size,
            block_size=args.block_size,
            n_embd=args.n_embd,
            n_head=args.n_head,
            n_layer=args.n_layer,
            dropout=args.dropout,
        )
        model = MiniGPT(**model_config).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    print(f"params: {sum(p.numel() for p in model.parameters()):,}")

    def save_checkpoint(step):
        os.makedirs(os.path.dirname(args.checkpoint), exist_ok=True)
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "step": step,
                "config": model_config,
            },
            args.checkpoint,
        )

    start = time.time()
    for step in range(start_step, args.steps):
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

        if step % args.checkpoint_interval == 0 and step > start_step:
            save_checkpoint(step)
            print(f"checkpoint saved at step {step} -> {args.checkpoint}")

    save_checkpoint(args.steps - 1)
    print(f"saved checkpoint to {args.checkpoint}")


if __name__ == "__main__":
    main()
