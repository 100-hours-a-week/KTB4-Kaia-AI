"""Corpus 빌더: 한국어 위키피디아 + FineWeb Korean으로 채워서 data/ 에 코퍼스 텍스트를 생성.
위키 한국어는 ~1GB 정도라서, 목표 크기가 크면 나머지를 FineWeb-2 Korean으로 채움.

사용:
    python data_preprocess.py --target-mb 11500 --output corpus.txt
"""

import argparse
import os
import re
import sys

from datasets import load_dataset

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

WIKI_DATASET = ("wikimedia/wikipedia", "20231101.ko")
FINEWEB_DATASET = ("HuggingFaceFW/fineweb-2", "kor_Hang")

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
    parser.add_argument("--output", default="corpus.txt", help="data/ 디렉토리에 저장할 출력 파일명")
    args = parser.parse_args()

    target_bytes = int(args.target_mb * 1024 * 1024)
    output_path = os.path.join(DATA_DIR, args.output)

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        print(f"== Korean Wikipedia 스트리밍 시작 (목표 {target_bytes / 1e6:.1f}MB, 있는 만큼 전부 사용) ==", flush=True)
        wiki = load_dataset(*WIKI_DATASET, split="train", streaming=True)
        wiki_written = stream_to_file(f, wiki, target_bytes, "wiki")
        print(f"== Wikipedia 완료: {wiki_written / 1e6:.1f}MB ==", flush=True)

        remaining_bytes = target_bytes - wiki_written
        fineweb_written = 0
        if remaining_bytes > 0:
            print(f"== FineWeb Korean 스트리밍 시작 (목표 {remaining_bytes / 1e6:.1f}MB) ==", flush=True)
            fineweb = load_dataset(*FINEWEB_DATASET, split="train", streaming=True)
            fineweb_written = stream_to_file(f, fineweb, remaining_bytes, "fineweb")
            print(f"== FineWeb 완료: {fineweb_written / 1e6:.1f}MB ==", flush=True)

    total_mb = (wiki_written + fineweb_written) / 1e6
    print(
        f"== {args.output} 생성 완료: 총 {total_mb:.1f}MB "
        f"(wiki {wiki_written / 1e6:.1f}MB + fineweb {fineweb_written / 1e6:.1f}MB) -> {output_path} ==",
        flush=True,
    )


if __name__ == "__main__":
    sys.exit(main())
