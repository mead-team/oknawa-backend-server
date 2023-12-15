from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.logging import logging_print
from app.core.metadata import swagger_metadata
from app.core.middleware import ProcessTimeMiddleware
from app.core.redis import redis_config
from app.core.scheduler import scheduler
from app.core.setting import settings
from app.routers import location


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"👋 Hello, Run the server in the {settings.APP_ENV} environment")
    scheduler.start()
    yield
    print(f"👋 Bye, Shut down the server in the {settings.APP_ENV} environment")
    scheduler.shutdown()


app = FastAPI(**swagger_metadata, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProcessTimeMiddleware)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    return await logging_print(request, call_next)


app.include_router(location.router)


@app.get("/api-health-check")
def api_health_check():
    return {
        "api_health_check": "oknawa-backend-api-server is Ok",
        "debug-mode": settings.DEBUG,
    }


@app.get("/redis-health-check")
async def redis_health_check():
    redis_config.set("redis_server_status", "Ok")
    value = redis_config.get("redis_server_status").decode("utf-8")
    return {"redis_health_check": f"oknawa-backend-api-server is {value}"}


app.mount("/static", StaticFiles(directory="app/core/static"), name="static")
