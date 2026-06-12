"""Corpus 빌더: 한국어 위키피디아(70%) + FineWeb Korean(30%)을 스트리밍으로 받아
data/corpus.txt 로 합친다. (Mini GPT pretraining 코퍼스, 목표 100~500MB)

Usage:
    python data_preprocess.py --target-mb 500
"""

import argparse
import os
import re
import sys

from datasets import load_dataset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "corpus.txt")

WIKI_DATASET = ("wikimedia/wikipedia", "20231101.ko")
FINEWEB_DATASET = ("HuggingFaceFW/fineweb-2", "kor_Hang")

WIKI_RATIO = 0.7
FINEWEB_RATIO = 0.3
LOG_EVERY_MB = 10


def clean_text(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def stream_to_file(f, dataset_iter, target_bytes: int, source_name: str) -> int:
    written = 0
    last_logged_mb = 0
    for example in dataset_iter:
        text = clean_text(example.get("text", ""))
        if len(text) < 200:  # 너무 짧은 문서는 노이즈로 간주하고 제외
            continue

        chunk = text + "\n\n"
        f.write(chunk)
        written += len(chunk.encode("utf-8"))

        written_mb = written // (1024 * 1024)
        if written_mb >= last_logged_mb + LOG_EVERY_MB:
            last_logged_mb = written_mb
            print(f"[{source_name}] {written_mb} MB written...", flush=True)

        if written >= target_bytes:
            break
    return written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-mb", type=float, default=500, help="corpus.txt 목표 크기(MB)")
    args = parser.parse_args()

    target_bytes = int(args.target_mb * 1024 * 1024)
    wiki_target = int(target_bytes * WIKI_RATIO)
    fineweb_target = int(target_bytes * FINEWEB_RATIO)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        print(f"== Korean Wikipedia 스트리밍 시작 (목표 {wiki_target / 1e6:.1f}MB) ==", flush=True)
        wiki = load_dataset(*WIKI_DATASET, split="train", streaming=True)
        wiki_written = stream_to_file(f, wiki, wiki_target, "wiki")
        print(f"== Wikipedia 완료: {wiki_written / 1e6:.1f}MB ==", flush=True)

        print(f"== FineWeb Korean 스트리밍 시작 (목표 {fineweb_target / 1e6:.1f}MB) ==", flush=True)
        fineweb = load_dataset(*FINEWEB_DATASET, split="train", streaming=True)
        fineweb_written = stream_to_file(f, fineweb, fineweb_target, "fineweb")
        print(f"== FineWeb 완료: {fineweb_written / 1e6:.1f}MB ==", flush=True)

    total_mb = (wiki_written + fineweb_written) / 1e6
    print(f"== corpus.txt 생성 완료: 총 {total_mb:.1f}MB -> {OUTPUT_PATH} ==", flush=True)


if __name__ == "__main__":
    sys.exit(main())
