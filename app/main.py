from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.middleware import ProcessTimeMiddleware
from app.core.database import SessionLocal, engine

DEBUG = bool(config("DEBUG"))
ORIGINS = config("ALLOWED_ORIGINS", default="").split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeMiddleware)


@app.get("/")
def health_check():
    return {"health_check": "Hello World", "debug": DEBUG}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
