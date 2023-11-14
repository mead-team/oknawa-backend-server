from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import SessionLocal, engine
from app.core.metadata import swagger_metadata
from app.core.middleware import ProcessTimeMiddleware
from app.core.setting import settings
from app.routers import item, location

app = FastAPI(**swagger_metadata)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeMiddleware)

app.include_router(location.router)
app.include_router(item.router)


@app.on_event("startup")
def start():
    print(f"👋 Hello, Run the server in the {settings.APP_ENV} environment")


@app.on_event("shutdown")
def start():
    print(f"👋 Bye, Shut down the server in the {settings.APP_ENV} environment")


@app.get("/")
def health_check():
    return {"health_check": "oknawa-backend-server is Ok", "debug": settings.DEBUG}


app.mount("/static", StaticFiles(directory="app/core/static"), name="static")
