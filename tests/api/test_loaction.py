from fastapi.testclient import TestClient


def test_post_location_meeting(client: TestClient):
    response = client.get("/location/meeting")
    content = response.json()
    assert response.status_code == 200


def test_post_location_meeting(client: TestClient):
    response = client.post("/location/meeting")
    content = response.json()
    assert response.status_code == 200


def test_post_location_point(client: TestClient):
    login_data = {
        "participant": [
            {
                "name": "김XX",
                "region_name": "송파구",
                "start_x": 126.882661758356,
                "start_y": 37.4803959660982,
            },
            {
                "name": "장XX",
                "region_name": "송파구",
                "start_x": 127.02800140627488,
                "start_y": 37.49808633653005,
            },
        ]
    }
    response = client.post("/location/point", json=login_data)
    content = response.json()
    assert response.status_code == 200


def test_get_point_place(client: TestClient):
    params = {"x": 126.952713197762, "y": 37.4812845080678}
    for category in ["food", "drink", "cafe"]:
        response = client.get(f"/location/point/place/{category}", params=params)
        content = response.json()
        assert response.status_code == 200
