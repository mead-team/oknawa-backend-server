from typing import Literal

from decouple import config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import SessionLocal, engine
from app.core.metadata import swagger_metadata
from app.core.middleware import ProcessTimeMiddleware
from app.routers import item, location

DEBUG = bool(config("DEBUG"))
ORIGINS = config("ALLOWED_ORIGINS", default="").split(",")


app = FastAPI(**swagger_metadata)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeMiddleware)

app.include_router(location.router)
app.include_router(item.router)


@app.get("/")
def health_check():
    return {"health_check": "Hello World", "debug": DEBUG}


app.mount("/static", StaticFiles(directory="app/core/static"), name="static")
