from contextlib import asynccontextmanager
from fastapi import FastAPI

from database.db import create_db_and_tables as create_db
from routers.post import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
