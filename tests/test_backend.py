import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "app"))

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
OLD_POLICY = SAMPLES_DIR / "policy_v1.txt"
NEW_POLICY = SAMPLES_DIR / "policy_v2.txt"

@pytest.fixture(scope="module")
def client():
    from main import app
    with TestClient(app) as c:
        yield c

def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "DocuDiff AI"

def test_api_comparison_flow(client):
    with open(OLD_POLICY, "rb") as f_old, open(NEW_POLICY, "rb") as f_new:
        response = client.post(
            "/api/v1/comparisons",
            files={
                "old_file": ("policy_old.txt", f_old, "text/plain"),
                "new_file": ("policy_new.txt", f_new, "text/plain")
            },
            data={"provider": "deterministic", "threshold": 0.65}
        )

    assert response.status_code == 200, response.text
    data = response.json()
    summary = data["summary"]
    cid = summary["comparison_id"]
    assert summary["total_changes"] == 5
    assert summary["added"] == 1
    assert summary["modified"] == 4

    # 1. Test get comparison
    get_res = client.get(f"/api/v1/comparisons/{cid}")
    assert get_res.status_code == 200
    assert get_res.json()["summary"]["comparison_id"] == cid

    # 2. Test get changes with filter
    filter_res = client.get(f"/api/v1/comparisons/{cid}/changes?change_type=added")
    assert filter_res.status_code == 200
    added_list = filter_res.json()
    assert len(added_list) == 1
    assert "Emergency access" in added_list[0]["new_text"]

    # 3. Test export CSV
    csv_res = client.get(f"/api/v1/comparisons/{cid}/export?format=csv")
    assert csv_res.status_code == 200
    assert "Change ID,Change Type,Priority" in csv_res.text
    assert "Emergency access requests" in csv_res.text

    # 4. Test export HTML
    html_res = client.get(f"/api/v1/comparisons/{cid}/export?format=html")
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.text
    assert "DocuDiff AI" in html_res.text
