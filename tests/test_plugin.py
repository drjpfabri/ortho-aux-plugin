
import os, tempfile
tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
os.environ["ORTHO_AUX_DB"] = tmp.name

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def new_session():
    with client:
        r = client.post("/session/start")
    assert r.status_code == 200
    return r.json()["session_id"]

def test_health():
    with client:
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_openapi_has_v1_paths_and_security_scheme():
    with client:
        r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert "/v1/consultations" in spec["paths"]
    assert "/v1/evidence/search" in spec["paths"]
    assert "APIKeyHeader" in spec["components"]["securitySchemes"]

def test_start_exact_message():
    with client:
        r = client.post("/session/start")
    assert r.json()["message"] == "Consulta iniciada. Documentação clínica ativa."
    assert r.json()["consultation_id"] == r.json()["session_id"]

def test_capture_and_state():
    sid = new_session()
    payload = {
        "mode": "PRONTUÁRIO",
        "facts": [{
            "field": "queixa",
            "value": "dor no tornozelo",
            "source": "PACIENTE",
            "validated": False
        }]
    }
    with client:
        assert client.post("/capture", headers={"X-Session-Id": sid}, json=payload).status_code == 200
        st = client.get("/session/state", headers={"X-Session-Id": sid})
    assert st.status_code == 200
    assert st.json()["facts"][0]["field"] == "queixa"

def test_v1_consultation_flow():
    with client:
        started = client.post("/v1/consultations")
    assert started.status_code == 200
    cid = started.json()["consultation_id"]
    payload = {
        "mode": "PRONTUÁRIO",
        "facts": [{
            "field": "lateralidade",
            "value": "direita",
            "source": "ACHADO MÉDICO",
            "validated": True
        }]
    }
    with client:
        captured = client.post(f"/v1/consultations/{cid}/events", json=payload)
        state = client.get(f"/v1/consultations/{cid}")
    assert captured.status_code == 200
    assert state.status_code == 200
    assert state.json()["facts"][0]["value"] == "direita"

def test_auth_required_only_when_configured(monkeypatch):
    monkeypatch.setenv("ORTHO_API_KEY", "test-secret")
    with client:
        denied = client.post("/v1/consultations")
        allowed = client.post("/v1/consultations", headers={"X-Ortho-Api-Key": "test-secret"})
    assert denied.status_code == 401
    assert allowed.status_code == 200

def test_nv_blocker():
    sid = new_session()
    payload = {
        "intervention": {
            "performed": True,
            "kind": "imobilização",
            "may_change_nv": True,
            "post_nv_documented": False
        }
    }
    with client:
        r = client.post("/finalize", headers={"X-Session-Id": sid}, json=payload)
    assert r.status_code == 409

def test_patient_mix_blocker():
    sid = new_session()
    with client:
        r = client.post("/finalize", headers={"X-Session-Id": sid},
                        json={"identity": {"possible_patient_mix": True}})
    assert r.status_code == 409

def test_finalize_ok():
    sid = new_session()
    with client:
        r = client.post("/finalize", headers={"X-Session-Id": sid}, json={})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_evidence_search_is_safe_metadata_only():
    with client:
        r = client.post("/v1/evidence/search", json={"query": "fratura exposta da tíbia", "domain": "trauma_adulto"})
    assert r.status_code == 200
    body = r.json()
    assert body["routing"]["preferred"] == "Rockwood and Green's Fractures in Adults"
    assert body["items"] == []
    assert "Nenhum trecho protegido" in body["copyright_policy"]
