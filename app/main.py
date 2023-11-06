from decouple import config
from fastapi import FastAPI
from app.core.middleware import ProcessTimeMiddleware


DEBUG = bool(config("DEBUG"))

app = FastAPI()
app.add_middleware(ProcessTimeMiddleware)


@app.get("/")
def health_check():
    return {"health_check": "Hello World", "debug": DEBUG}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}



