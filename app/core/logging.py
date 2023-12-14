import logging

from fastapi import Request
from starlette.concurrency import iterate_in_threadpool
from starlette.types import Message

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


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


async def logging_print(request: Request, call_next):
    await set_body(request, await request.body())
    response = await call_next(request)
    response_body = [chunk async for chunk in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(response_body))
    if response.status_code != 200:
        req_body = await get_body(request)
        res_body = (b"".join(response_body)).decode()
        log_error(response.status_code, req_body.decode(), res_body)
    return response
