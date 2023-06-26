from fastapi.testclient import TestClient

from app.server import APP

testclient = TestClient(APP)

def test_sync_get_appraisal():
    """Test calling /query endpoint."""
    response = testclient.post(
        "/sync_get_appraisal",
        json={"message": {}},
    )
    response.raise_for_status()
    response_json = response.json()
    assert response_json["status"] == "Rejected"