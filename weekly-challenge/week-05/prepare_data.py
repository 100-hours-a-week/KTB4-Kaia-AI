"""Corpus를 토큰화해 tokens.bin (uint16 raw array)으로 저장.

대용량 코퍼스를 한 번에 메모리에 올리지 않기 위해 청크 단위로 스트리밍 토큰화한다.
train.py는 이 tokens.bin을 np.memmap으로 읽어 학습한다.
중단 후 재실행하면 마지막으로 처리한 위치부터 이어서 진행한다.

사용:
    python prepare_data.py --corpus data/corpus.txt
"""

import argparse
import os

import numpy as np

from tokenizer import Tokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.join(BASE_DIR, "data", "corpus.txt")
TOKENIZER_PATH = os.path.join(BASE_DIR, "checkpoints", "tokenizer.model")

CHUNK_CHARS = 5_000_000  # 한 번에 읽어서 인코딩할 문자 수


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", default=DEFAULT_CORPUS)
    parser.add_argument("--tokenizer", default=TOKENIZER_PATH)
    parser.add_argument("--output", default=None, help="출력 경로 (기본: <corpus>와 같은 디렉토리의 tokens.bin)")
    args = parser.parse_args()

    tok = Tokenizer(args.tokenizer)
    assert tok.vocab_size <= 65536, f"vocab_size({tok.vocab_size})가 uint16 범위를 초과합니다"
    print(f"vocab size: {tok.vocab_size}")

    output_path = args.output or os.path.join(os.path.dirname(args.corpus), "tokens.bin")
    progress_path = output_path + ".progress"
    corpus_size = os.path.getsize(args.corpus)
    print(f"corpus size: {corpus_size / 1e9:.2f} GB")

    start_pos = 0
    mode = "wb"
    if os.path.exists(progress_path) and os.path.exists(output_path):
        with open(progress_path) as pf:
            start_pos = int(pf.read().strip())
        mode = "ab"
        print(f"resuming from previous run (corpus position {start_pos:,})")

    with open(args.corpus, "r", encoding="utf-8") as fin, open(output_path, mode) as fout:
        if start_pos:
            fin.seek(start_pos)
        while True:
            chunk = fin.read(CHUNK_CHARS)
            if not chunk:
                break
            ids = tok.encode(chunk)
            np.array(ids, dtype=np.uint16).tofile(fout)
            with open(progress_path, "w") as pf:
                pf.write(str(fin.tell()))
            print(f"corpus position {fin.tell():,} / {corpus_size:,}...", flush=True)

    total_tokens = os.path.getsize(output_path) // 2
    os.remove(progress_path)
    print(f"== 완료: {total_tokens:,} tokens -> {output_path} ({os.path.getsize(output_path) / 1e9:.2f} GB) ==")


if __name__ == "__main__":
    main()
