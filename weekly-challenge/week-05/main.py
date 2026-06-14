"""Mini GPT 모델 성능 확인기 — FastAPI 서버.

실행:
    fastapi dev main.py
"""

import os
import sqlite3
import time
from datetime import datetime

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from model import MiniGPT
from tokenizer import Tokenizer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "test.db")
TOKENIZER_PATH = os.path.join(BASE_DIR, "checkpoints", "tokenizer.model")
CHECKPOINT_PATH = os.environ.get(
    "MINIGPT_CHECKPOINT", os.path.join(BASE_DIR, "checkpoints", "mini_gpt.pt")
)


# ---------------------------------------------------------------------------
# 요청/응답 모델
# ---------------------------------------------------------------------------
class GenConfig(BaseModel):
    temperature: float = 0.8
    top_k: int | None = 40
    repetition_penalty: float = 1.0
    max_new_tokens: int = 80


class TestRequest(BaseModel):
    input_text: str
    configs: list[GenConfig] = Field(min_length=1, max_length=3)


# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER NOT NULL,
            config_index INTEGER NOT NULL,
            temperature REAL NOT NULL,
            top_k INTEGER,
            repetition_penalty REAL NOT NULL,
            max_new_tokens INTEGER NOT NULL,
            generated_text TEXT NOT NULL,
            elapsed_time REAL NOT NULL,
            tokens_per_sec REAL NOT NULL,
            FOREIGN KEY (test_id) REFERENCES tests(id)
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# 모델 로드
# ---------------------------------------------------------------------------
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


def result_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "config_index": row["config_index"],
        "config": {
            "temperature": row["temperature"],
            "top_k": row["top_k"],
            "repetition_penalty": row["repetition_penalty"],
            "max_new_tokens": row["max_new_tokens"],
        },
        "generated_text": row["generated_text"],
        "elapsed_time": row["elapsed_time"],
        "tokens_per_sec": row["tokens_per_sec"],
    }


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------
app = FastAPI()
init_db()


@app.post("/tests")
def create_test(test: TestRequest):
    conn = get_conn()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO tests (input_text, created_at) VALUES (?, ?)",
        (test.input_text, created_at),
    )
    test_id = cur.lastrowid

    results = []
    for i, config in enumerate(test.configs):
        result = run_generation(test.input_text, config)
        conn.execute(
            """INSERT INTO results
               (test_id, config_index, temperature, top_k, repetition_penalty,
                max_new_tokens, generated_text, elapsed_time, tokens_per_sec)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                test_id, i, config.temperature, config.top_k, config.repetition_penalty,
                config.max_new_tokens, result["generated_text"], result["elapsed_time"],
                result["tokens_per_sec"],
            ),
        )
        results.append({
            "config_index": i,
            "config": config.model_dump(),
            **result,
        })

    conn.commit()
    conn.close()

    return {
        "id": test_id,
        "input_text": test.input_text,
        "created_at": created_at,
        "results": results,
    }


@app.get("/tests")
def list_tests():
    conn = get_conn()
    rows = conn.execute("SELECT id, input_text, created_at FROM tests").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.get("/tests/{test_id}")
def get_test(test_id: int):
    conn = get_conn()
    test = conn.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()
    if test is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")

    result_rows = conn.execute(
        "SELECT * FROM results WHERE test_id = ? ORDER BY config_index", (test_id,)
    ).fetchall()
    conn.close()

    return {
        "id": test["id"],
        "input_text": test["input_text"],
        "created_at": test["created_at"],
        "results": [result_row_to_dict(row) for row in result_rows],
    }


@app.delete("/tests/{test_id}")
def delete_test(test_id: int):
    conn = get_conn()
    test = conn.execute("SELECT id FROM tests WHERE id = ?", (test_id,)).fetchone()
    if test is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")

    conn.execute("DELETE FROM results WHERE test_id = ?", (test_id,))
    conn.execute("DELETE FROM tests WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()

    return {"message": f"Test {test_id} deleted"}
