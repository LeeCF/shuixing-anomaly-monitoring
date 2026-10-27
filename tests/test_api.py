from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

SIX_ELEMENTS = [
    "anomaly_description", "trigger_reasons", "similar_cases",
    "recommended_actions", "parties", "data_lineage",
]


def test_list_returns_three_summaries():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    for item in data:
        assert {"id", "alert_no", "risk_score", "level", "scenario", "summary"} <= item.keys()


def test_each_card_carries_all_six_elements():
    for item in client.get("/api/alerts").json():
        full = client.get(f"/api/alerts/{item['id']}").json()
        for key in SIX_ELEMENTS:
            assert key in full, f"{item['id']} 缺少 {key}"
        assert len(full["trigger_reasons"]) == 3          # 规则/统计/画像 三层
        assert len(full["similar_cases"]) >= 1
        assert len(full["recommended_actions"]) >= 1


def test_unknown_alert_returns_404():
    assert client.get("/api/alerts/nope").status_code == 404


def test_detect_run_returns_count_and_list():
    r = client.post("/api/detect/run")
    assert r.status_code == 200
    body = r.json()
    assert body["detected"] == 3
    assert len(body["alerts"]) == 3
