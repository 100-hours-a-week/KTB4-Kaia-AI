from datetime import datetime

from database.db import get_conn
from schemas import GenConfig


def insert_test(input_text: str) -> tuple[int, str]:
    conn = get_conn()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO tests (input_text, created_at) VALUES (?, ?)",
        (input_text, created_at),
    )
    conn.commit()
    test_id = cur.lastrowid
    conn.close()
    return test_id, created_at


def insert_result(test_id: int, config_index: int, config: GenConfig, result: dict):
    conn = get_conn()
    conn.execute(
        """INSERT INTO results
           (test_id, config_index, temperature, top_k, repetition_penalty,
            max_new_tokens, generated_text, elapsed_time, tokens_per_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            test_id, config_index, config.temperature, config.top_k,
            config.repetition_penalty, config.max_new_tokens,
            result["generated_text"], result["elapsed_time"], result["tokens_per_sec"],
        ),
    )
    conn.commit()
    conn.close()


def get_all_tests() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT id, input_text, created_at FROM tests").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_test(test_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tests WHERE id = ?", (test_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_results(test_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM results WHERE test_id = ? ORDER BY config_index", (test_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_test(test_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM results WHERE test_id = ?", (test_id,))
    conn.execute("DELETE FROM tests WHERE id = ?", (test_id,))
    conn.commit()
    conn.close()
