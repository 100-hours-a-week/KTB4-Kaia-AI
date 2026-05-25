from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3

class Post(BaseModel):
    author: str
    title: str
    content: str

class PostUpdate(BaseModel):
    author: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None

class Comment(BaseModel):
    author: str
    content: str

class CommentUpdate(BaseModel):
    author: Optional[str] = None
    content: Optional[str] = None


# database connection
conn = sqlite3.connect("board.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS post(
        post_id INTEGER PRIMARY KEY,
        author TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS comment(
        comment_id INTEGER PRIMARY KEY,
        post_id INTEGER NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP
    )
""")

conn.commit()


# FastAPI app
app = FastAPI()

# 게시글 기능
@app.post("/posts/")
async def write_post(post: Post):
    cur.execute(
        "INSERT INTO post (author, title, content, created_at) VALUES (?, ?, ?, ?)",
        (post.author, post.title, post.content, datetime.now())
    )
    conn.commit()
    new_id = cur.lastrowid
    return dict(cur.execute("SELECT * FROM post WHERE post_id = ?", (new_id,)).fetchone())

@app.get("/posts/")
async def read_post_list():
    cur.execute("SELECT * FROM post")
    return [dict(row) for row in cur.fetchall()]

@app.get("/posts/{post_id}")
async def read_post(post_id: int):
    post = cur.execute(
        "SELECT * FROM post WHERE post_id = ?", (post_id,)
    ).fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return dict(post)

ALLOWED_POST_COLUMNS = {"author", "title", "content"}

@app.patch("/posts/{post_id}")
async def update_post(post_id: int, post: PostUpdate):
    post_to_update = cur.execute(
        "SELECT * FROM post WHERE post_id = ?", (post_id,)
    ).fetchone()
    if not post_to_update:
        raise HTTPException(status_code=404, detail="Post not found")
    update_data = post.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key not in ALLOWED_POST_COLUMNS:
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")
        cur.execute(f"UPDATE post SET {key} = ? WHERE post_id = ?", (value, post_id))
    conn.commit()
    return dict(cur.execute("SELECT * FROM post WHERE post_id = ?", (post_id,)).fetchone())

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    post = cur.execute("SELECT * FROM post WHERE post_id = ?", (post_id,)).fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    cur.execute("DELETE FROM comment WHERE post_id = ?", (post_id,))
    cur.execute("DELETE FROM post WHERE post_id = ?", (post_id,))
    conn.commit()
    return {"message": "Post deleted successfully"}

# 댓글 기능
@app.post("/posts/{post_id}/comments/")
async def write_comment(post_id: int, comment: Comment):
    post = cur.execute("SELECT post_id FROM post WHERE post_id = ?", (post_id,)).fetchone()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    cur.execute(
        "INSERT INTO comment (post_id, author, content, created_at) VALUES (?, ?, ?, ?)",
        (post_id, comment.author, comment.content, datetime.now())
    )
    conn.commit()
    new_id = cur.lastrowid
    return dict(cur.execute("SELECT * FROM comment WHERE comment_id = ?", (new_id,)).fetchone())

@app.get("/posts/{post_id}/comments/")
async def read_comment(post_id: int):
    cur.execute("SELECT * FROM comment WHERE post_id = ?", (post_id,))
    return [dict(row) for row in cur.fetchall()]

@app.patch("/posts/{post_id}/comments/{comment_id}")
async def update_comment(post_id: int, comment_id: int, comment: CommentUpdate):
    comment_to_update = cur.execute(
        "SELECT * FROM comment WHERE comment_id = ? AND post_id = ?", (comment_id, post_id)
    ).fetchone()
    if not comment_to_update:
        raise HTTPException(status_code=404, detail="Comment not found")
    update_data = comment.model_dump(exclude_unset=True)
    if "author" in update_data:
        cur.execute("UPDATE comment SET author = ? WHERE comment_id = ?", (update_data["author"], comment_id))
    if "content" in update_data:
        cur.execute("UPDATE comment SET content = ? WHERE comment_id = ?", (update_data["content"], comment_id))
    conn.commit()
    return dict(cur.execute("SELECT * FROM comment WHERE comment_id = ?", (comment_id,)).fetchone())


@app.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int):
    comment = cur.execute(
        "SELECT * FROM comment WHERE comment_id = ? AND post_id = ?", (comment_id, post_id)
    ).fetchone()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    cur.execute("DELETE FROM comment WHERE comment_id = ?", (comment_id,))
    conn.commit()
    return {"message": "Comment deleted successfully"}