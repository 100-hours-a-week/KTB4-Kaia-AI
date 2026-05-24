from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

app = FastAPI()

posts = []
next_post_id = 1
next_comment_id = 1

def find_post(post_id: int):
    for post in posts:
        if post["post_id"] == post_id:
            return post
    return None

# 게시글 기능
@app.post("/posts/")
async def write_post(post: Post):
    global next_post_id
    posts.append(
        {
            "post_id": next_post_id,
            "author": post.author,
            "title": post.title,
            "content": post.content,
            "comments": [],
            "created_at": datetime.now(),
        }
    )
    next_post_id += 1
    return posts[-1]

@app.get("/posts/") 
async def read_post_list():
    return posts

@app.get("/posts/{post_id}")
async def read_post(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.patch("/posts/{post_id}")
async def update_post(post_id: int, post: PostUpdate):
    post_to_update = find_post(post_id)
    if not post_to_update:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author is not None:
        post_to_update["author"] = post.author
    if post.title is not None:
        post_to_update["title"] = post.title
    if post.content is not None:
        post_to_update["content"] = post.content
    return post_to_update


@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    posts.remove(post)
    return {"message": "Post deleted successfully"}


# 댓글 기능
@app.post("/posts/{post_id}/comments/")
async def write_comment(post_id: int, comment: Comment):
    global next_comment_id
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post_comment = post["comments"]
    post_comment.append(
        {
            "comment_id": next_comment_id,
            "author": comment.author,
            "content": comment.content,
            "created_at": datetime.now()
        }
    )
    next_comment_id += 1
    return post_comment[-1]

@app.get("/posts/{post_id}/comments/")
async def read_comment(post_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post["comments"]

@app.patch("/posts/{post_id}/comments/{comment_id}")
async def update_comment(post_id: int, comment_id: int, comment: CommentUpdate):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment_to_update = next((c for c in post["comments"] if c["comment_id"] == comment_id), None)
    if not comment_to_update:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author is not None:
        comment_to_update["author"] = comment.author
    if comment.content is not None:
        comment_to_update["content"] = comment.content

    return comment_to_update

@app.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int):
    post = find_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = next((c for c in post["comments"] if c["comment_id"] == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    post["comments"].remove(comment)
    return {"message": "Comment deleted successfully"}