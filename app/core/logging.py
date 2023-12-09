import logging

from fastapi import Request
from starlette.types import Message

from fastapi import FastAPI, Request, Response
from starlette.background import BackgroundTask

# logging
logger = logging.getLogger("main")
logging.basicConfig(
    format="%(asctime)s %(levelname)s : %(message)s",
    level=logging.INFO,
    datefmt="%Y/%m/%d %H:%M:%S",
)
steam_handler = logging.StreamHandler()
logger.addHandler(steam_handler)


def log_error(req_body, res_body):
    logging.error("-----------------------------------------------------------------")
    logging.error(f"request body: {req_body}")
    logging.error(f"response body: {res_body}")
    logging.error("-----------------------------------------------------------------")


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive
    

async def logging_temp(request, call_next):
    req_body = await request.body()
    await set_body(request, req_body)
    response = await call_next(request)

    res_body = b""
    async for chunk in response.body_iterator:
        res_body += chunk
        
    if response.headers["content-type"] != "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        res_body = res_body.decode("utf-8")
        req_body = req_body.decode("utf-8")
        
    if response.status_code == 200:
        return Response(
            content=res_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
    else:
        task = BackgroundTask(log_error, req_body, res_body)
        return Response(
            content=res_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
            background=task,
        )
