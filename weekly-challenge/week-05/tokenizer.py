"""SentencePiece BPE 토크나이저 학습/적용.

학습:
    python tokenizer.py train --corpus data/corpus.txt --vocab-size 16000
"""

import argparse
import os

import sentencepiece as spm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.join(BASE_DIR, "data", "corpus.txt")
DEFAULT_MODEL_PREFIX = os.path.join(BASE_DIR, "checkpoints", "tokenizer")
DEFAULT_VOCAB_SIZE = 16000

# 특수 토큰 id (model.py / train.py에서도 동일하게 참조)
PAD_ID = 0
UNK_ID = 1
BOS_ID = 2
EOS_ID = 3


def train(
    corpus_path: str = DEFAULT_CORPUS,
    model_prefix: str = DEFAULT_MODEL_PREFIX,
    vocab_size: int = DEFAULT_VOCAB_SIZE,
):
    os.makedirs(os.path.dirname(model_prefix), exist_ok=True)
    spm.SentencePieceTrainer.train(
        input=corpus_path,
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        model_type="bpe",
        character_coverage=0.9995,  # 한국어 등 문자 수가 많은 언어 권장값
        pad_id=PAD_ID,
        unk_id=UNK_ID,
        bos_id=BOS_ID,
        eos_id=EOS_ID,
        input_sentence_size=3_000_000,
        shuffle_input_sentence=True,
        num_threads=os.cpu_count() or 4,
    )
    print(f"tokenizer model saved to {model_prefix}.model / {model_prefix}.vocab")


class Tokenizer:
    def __init__(self, model_path: str = f"{DEFAULT_MODEL_PREFIX}.model"):
        self.sp = spm.SentencePieceProcessor(model_file=model_path)

    @property
    def vocab_size(self) -> int:
        return self.sp.vocab_size()

    def encode(self, text: str, add_bos: bool = False, add_eos: bool = False) -> list[int]:
        ids = self.sp.encode(text, out_type=int)
        if add_bos:
            ids = [BOS_ID] + ids
        if add_eos:
            ids = ids + [EOS_ID]
        return ids

    def decode(self, ids: list[int]) -> str:
        return self.sp.decode(ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    train_p = sub.add_parser("train")
    train_p.add_argument("--corpus", default=DEFAULT_CORPUS)
    train_p.add_argument("--model-prefix", default=DEFAULT_MODEL_PREFIX)
    train_p.add_argument("--vocab-size", type=int, default=DEFAULT_VOCAB_SIZE)

    args = parser.parse_args()

    if args.command == "train":
        train(args.corpus, args.model_prefix, args.vocab_size)

        tok = Tokenizer(f"{args.model_prefix}.model")
        sample = "안녕하세요, Mini GPT 토크나이저 테스트입니다. 오늘은 날씨가 좋네요."
        ids = tok.encode(sample)
        print("vocab size:", tok.vocab_size)
        print("sample text:", sample)
        print("token ids:", ids)
        print("token count:", len(ids))
        print("decoded:", tok.decode(ids))
