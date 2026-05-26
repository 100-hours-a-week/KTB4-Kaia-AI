from pydantic import BaseModel


class Post(BaseModel):
    author: str
    title: str
    content: str


class PostUpdate(BaseModel):
    author: str | None = None
    title: str | None = None
    content: str | None = None


class Comment(BaseModel):
    author: str
    content: str


class CommentUpdate(BaseModel):
    author: str | None = None
    content: str | None = None
