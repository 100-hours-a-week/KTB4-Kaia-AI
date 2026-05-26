from fastapi import APIRouter
from schemas import Post, PostUpdate, Comment, CommentUpdate
from controllers import post as post_controller

router = APIRouter()


@router.post("/posts/")
async def write_post(post: Post):
    return post_controller.create_post(post)


@router.get("/posts/")
async def read_post_list():
    return post_controller.list_posts()


@router.get("/posts/{post_id}")
async def read_post(post_id: int):
    return post_controller.read_post(post_id)


@router.get("/posts/{post_id}/summary")
async def summarize_post(post_id: int):
    return await post_controller.summarize_post(post_id)


@router.patch("/posts/{post_id}")
async def update_post(post_id: int, post: PostUpdate):
    return post_controller.update_post(post_id, post)


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    return post_controller.delete_post(post_id)


@router.post("/posts/{post_id}/comments/")
async def write_comment(post_id: int, comment: Comment):
    return post_controller.create_comment(post_id, comment)


@router.get("/posts/{post_id}/comments/")
async def read_comments(post_id: int):
    return post_controller.list_comments(post_id)


@router.patch("/posts/{post_id}/comments/{comment_id}")
async def update_comment(post_id: int, comment_id: int, comment: CommentUpdate):
    return post_controller.update_comment(post_id, comment_id, comment)


@router.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int):
    return post_controller.delete_comment(post_id, comment_id)
