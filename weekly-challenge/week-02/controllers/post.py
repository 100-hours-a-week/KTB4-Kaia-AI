from fastapi import HTTPException
import httpx

from models import post as post_model


def create_post(post):
    return post_model.insert_post(post.author, post.title, post.content)


def list_posts():
    return post_model.get_all_posts()


def read_post(post_id):
    post = post_model.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


async def summarize_post(post_id):
    post = post_model.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    payload = {
        "model": "gemma4:e4b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise summarization assistant. "
                    "Always respond in the same language as the input text. "
                    "Keep the summary natural, concise, and easy to read."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Summarize the following post in 3-5 sentences. "
                    f"Return only the summary.\n\n{post['content']}"
                ),
            },
        ],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/v1/chat/completions",
            json=payload,
            timeout=120.0,
        )
    result = response.json()
    if "choices" not in result or not result["choices"]:
        raise HTTPException(status_code=502, detail="AI response error")
    return {"summary": result["choices"][0]["message"]["content"]}


def update_post(post_id, post_update):
    if not post_model.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    fields = post_update.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다")
    for key in fields:
        if key not in post_model.ALLOWED_POST_COLUMNS:
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")
    return post_model.update_post(post_id, fields)


def delete_post(post_id):
    if not post_model.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    post_model.delete_post(post_id)
    return {"message": "Post deleted successfully"}


def create_comment(post_id, comment):
    if not post_model.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    return post_model.insert_comment(post_id, comment.author, comment.content)


def list_comments(post_id):
    if not post_model.get_post(post_id):
        raise HTTPException(status_code=404, detail="Post not found")
    return post_model.get_comments(post_id)


def update_comment(post_id, comment_id, comment_update):
    if not post_model.get_comment(post_id, comment_id):
        raise HTTPException(status_code=404, detail="Comment not found")
    fields = comment_update.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다")
    for key in fields:
        if key not in post_model.ALLOWED_COMMENT_COLUMNS:
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")
    return post_model.update_comment(comment_id, fields)


def delete_comment(post_id, comment_id):
    if not post_model.get_comment(post_id, comment_id):
        raise HTTPException(status_code=404, detail="Comment not found")
    post_model.delete_comment(comment_id)
    return {"message": "Comment deleted successfully"}
