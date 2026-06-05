from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _contains_numeric_value(obj):
    """Return True if a nested object contains at least one numeric value."""
    if isinstance(obj, (int, float)):
        return True

    if isinstance(obj, dict):
        return any(_contains_numeric_value(value) for value in obj.values())

    if isinstance(obj, list):
        return any(_contains_numeric_value(value) for value in obj)

    return False


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_model_info_endpoint():
    response = client.get("/model-info")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_sample_input_endpoint():
    response = client.get("/sample-input")

    assert response.status_code == 200
    assert isinstance(response.json(), dict)


def test_predict_endpoint_with_sample_input():
    sample_response = client.get("/sample-input")

    assert sample_response.status_code == 200

    sample_json = sample_response.json()

    payload = (
        sample_json.get("sample_input")
        or sample_json.get("input")
        or sample_json
    )

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    prediction_response = response.json()

    assert isinstance(prediction_response, dict)
    assert _contains_numeric_value(prediction_response)


def test_predict_endpoint_rejects_empty_payload():
    response = client.post("/predict", json={})

    assert response.status_code in (400, 422)
