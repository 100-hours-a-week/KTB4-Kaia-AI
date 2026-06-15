from fastapi import FastAPI

from database.db import init_db
from routers.tests import router as tests_router

app = FastAPI()
init_db()
app.include_router(tests_router)
