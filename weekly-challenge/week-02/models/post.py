from datetime import datetime
from database.db import get_db

ALLOWED_POST_COLUMNS = {"author", "title", "content"}
ALLOWED_COMMENT_COLUMNS = {"author", "content"}


def insert_post(author, title, content):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO post (author, title, content, created_at) VALUES (?, ?, ?, ?)",
            (author, title, content, datetime.now()),
        )
        conn.commit()
        return dict(cur.execute("SELECT * FROM post WHERE post_id = ?", (cur.lastrowid,)).fetchone())


def get_all_posts():
    with get_db() as conn:
        cur = conn.cursor()
        return [dict(r) for r in cur.execute("SELECT * FROM post").fetchall()]


def get_post(post_id):
    with get_db() as conn:
        cur = conn.cursor()
        row = cur.execute("SELECT * FROM post WHERE post_id = ?", (post_id,)).fetchone()
        return dict(row) if row else None


def update_post(post_id, fields):
    with get_db() as conn:
        cur = conn.cursor()
        for key, value in fields.items():
            cur.execute(f"UPDATE post SET {key} = ? WHERE post_id = ?", (value, post_id))
        conn.commit()
        return dict(cur.execute("SELECT * FROM post WHERE post_id = ?", (post_id,)).fetchone())


def delete_post(post_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM comment WHERE post_id = ?", (post_id,))
        cur.execute("DELETE FROM post WHERE post_id = ?", (post_id,))
        conn.commit()


def insert_comment(post_id, author, content):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO comment (post_id, author, content, created_at) VALUES (?, ?, ?, ?)",
            (post_id, author, content, datetime.now()),
        )
        conn.commit()
        return dict(cur.execute("SELECT * FROM comment WHERE comment_id = ?", (cur.lastrowid,)).fetchone())


def get_comments(post_id):
    with get_db() as conn:
        cur = conn.cursor()
        return [dict(r) for r in cur.execute("SELECT * FROM comment WHERE post_id = ?", (post_id,)).fetchall()]


def get_comment(post_id, comment_id):
    with get_db() as conn:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT * FROM comment WHERE comment_id = ? AND post_id = ?", (comment_id, post_id)
        ).fetchone()
        return dict(row) if row else None


def update_comment(comment_id, fields):
    with get_db() as conn:
        cur = conn.cursor()
        for key, value in fields.items():
            cur.execute(f"UPDATE comment SET {key} = ? WHERE comment_id = ?", (value, comment_id))
        conn.commit()
        return dict(cur.execute("SELECT * FROM comment WHERE comment_id = ?", (comment_id,)).fetchone())


def delete_comment(comment_id):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM comment WHERE comment_id = ?", (comment_id,))
        conn.commit()
