import json
import time

from fastapi import HTTPException

from app.core.util import generate_key


def get_together_location_polling(room_id, redis):
    generate_key.validate_uuid(room_id)
    redis_room_id_key = f"room-{room_id}"

    room_data = redis.get(redis_room_id_key)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    participant_data = json.loads(room_data).get("participant")
    response = {"room_id": room_id, "participant": participant_data}
    return response


def get_together_location_long_polling(room_id, redis):
    timeout = 30
    generate_key.validate_uuid(room_id)
    redis_room_id_key = f"room-{room_id}"

    start_time = time.time()

    previous_room_data = redis.get(redis_room_id_key)
    if not previous_room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    while True:
        current_room_data = redis.get(redis_room_id_key)
        if not current_room_data:
            raise HTTPException(status_code=404, detail="Room not found")

        if previous_room_data != current_room_data:
            participant_data = json.loads(current_room_data).get("participant")
            response = {"room_id": room_id, "participant": participant_data}
            return response

        if time.time() - start_time > timeout:
            participant_data = json.loads(current_room_data).get("participant")
            response = {"room_id": room_id, "participant": participant_data}
            return response
        time.sleep(1)


def post_together(body, redis):
    TTL = 60 * 60 * 24 * 14
    room_id = generate_key.create_uuid()
    redis_room_id_key = f"room-{room_id}"
    room_host_id = room_id.replace("-", "")[:8][::-1]
    host_start_point = body.model_dump()

    room_data = {
        "room_id": room_id,
        "room_host_id": room_host_id,
        "participant": [host_start_point],
    }
    redis.set(redis_room_id_key, json.dumps(room_data), ex=TTL)
    response = room_data
    return response


def post_together_location(body, room_id, redis):
    generate_key.validate_uuid(room_id)
    redis_room_id_key = f"room-{room_id}"

    room_data = redis.get(redis_room_id_key)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    client_start_point = body.dict()
    room_data = json.loads(room_data)
    room_data["participant"].append(client_start_point)

    ttl = redis.ttl(redis_room_id_key)
    if ttl < 0:
        raise HTTPException(status_code=404, detail="Expire TTL")

    redis.set(redis_room_id_key, json.dumps(room_data), ex=ttl)

    return {"msg": "주소 입력 완료"}


def put_together_location(body, room_id, room_host_id, redis):
    generate_key.validate_uuid(room_id)
    redis_room_id_key = f"room-{room_id}"

    room_data = redis.get(redis_room_id_key)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")

    room_data = json.loads(room_data)
    room_host_id_data = room_data["room_host_id"]

    if room_host_id != room_host_id_data:
        raise HTTPException(status_code=404, detail="Not Permission")

    body_dict = body.dict().get("participant")
    room_data["participant"] = body_dict

    ttl = redis.ttl(redis_room_id_key)
    if ttl < 0:
        raise HTTPException(status_code=404, detail="Expire TTL")

    redis.set(redis_room_id_key, json.dumps(room_data), ex=ttl)

    return {"msg": "주소 수정 완료"}
