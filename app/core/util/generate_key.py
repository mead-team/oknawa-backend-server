import uuid

from fastapi import HTTPException


def create_uuid():
    return str(uuid.uuid4())


def validate_uuid(uuid_str: str):
    try:
        uuid.UUID(uuid_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID Format")
