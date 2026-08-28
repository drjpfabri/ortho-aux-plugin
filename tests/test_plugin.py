import os
import tempfile

import pytest
import yaml

tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
os.environ["ORTHO_AUX_DB"] = tmp.name
os.environ["ORTHO_ENV"] = "test"
os.environ["ORTHO_ALLOWED_DATA_CLASSIFICATIONS"] = "synthetic"
os.environ["ORTHO_DATA_RETENTION_HOURS"] = "168"
os.environ["ORTHO_GOVERNANCE_PROFILE"] = "synthetic_alpha"
os.environ["ORTHO_GOVERNANCE_REVIEW_DUE"] = "2099-12-31"
os.environ["ORTHO_GOVERNANCE_APPROVED"] = "false"

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.main import (
    GOVERNANCE_POLICY_VERSION,
    GOVERNANCE_REFERENCE_CONTROLS,
    SAFETY_KEYS,
    app,
    consultation_metadata_table,
    deidentified_governance_errors,
    engine,
    governance_status,
    normalize_database_url,
    purge_unclassified_and_expired_sessions,
    validate_runtime_configuration,
)

client = TestClient(app)
EMPTY_SAFETY = {key: False for key in SAFETY_KEYS}
START_PAYLOAD = {
    "data_classification": "synthetic",
    "purpose": "technical_test",
    "attested_no_direct_identifiers": True,
}
VALID_GATE = {
    "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
    "neurovascular": {"baseline_documented": True},
    "safety": EMPTY_SAFETY,
}


def new_session():
    with client:
        response = client.post("/v1/consultations", json=START_PAYLOAD)
    assert response.status_code == 200
    return response.json()["consultation_id"]


def test_health_and_security_headers():
    with client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["database"] == "ok"
    assert response.json()["profile"] == "synthetic_alpha"
    assert response.json()["accepting_new_consultations"] is True
    assert response.json()["clinical_use_authorized"] is False
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-request-id"]


def test_openapi_has_v1_paths_and_security_scheme():
    with client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"] == "3.1.0"
    assert "/v1/consultations" in spec["paths"]
    assert "/v1/evidence/search" in spec["paths"]
    assert "/v1/pilot/metrics" in spec["paths"]
    assert "/v1/governance/status" in spec["paths"]
    assert "/session/start" not in spec["paths"]
    assert "APIKeyHeader" in spec["components"]["securitySchemes"]
    operation_ids = [
        operation["operationId"]
        for path in spec["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))


def test_static_gpt_action_schema_matches_generated_contract():
    with open("gpt-action.openapi.yaml", encoding="utf-8") as schema_file:
        static_schema = yaml.safe_load(schema_file)
    with client:
        generated_schema = client.get("/openapi.json").json()
    assert static_schema["info"]["version"] == generated_schema["info"]["version"]
    assert static_schema["servers"] == generated_schema["servers"]
    assert static_schema["paths"] == generated_schema["paths"]
    assert static_schema["components"] == generated_schema["components"]


def test_render_postgres_url_uses_psycopg_driver():
    assert normalize_database_url("postgresql://user:pass@db/ortho") == (
        "postgresql+psycopg://user:pass@db/ortho"
    )


def test_start_requires_explicit_synthetic_attestation():
    with client:
        missing = client.post("/v1/consultations", json={})
        false_attestation = client.post(
            "/v1/consultations", json={**START_PAYLOAD, "attested_no_direct_identifiers": False}
        )
        allowed = client.post("/v1/consultations", json=START_PAYLOAD)
    assert missing.status_code == 422
    assert false_attestation.status_code == 422
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["data_classification"] == "synthetic"
    assert body["expires_at"] > 0
    assert "sintética" in body["message"]


def test_deidentified_data_is_blocked_before_governance_approval():
    payload = {**START_PAYLOAD, "data_classification": "deidentified"}
    with client:
        response = client.post("/v1/consultations", json=payload)
    assert response.status_code == 403


def test_governance_status_is_explicit_and_fail_closed():
    with client:
        response = client.get("/v1/governance/status")
    assert response.status_code == 200
    body = response.json()
    assert body["policy_version"] == GOVERNANCE_POLICY_VERSION
    assert body["current_profile"] == "synthetic_alpha"
    assert body["review_current"] is True
    assert body["accepting_new_consultations"] is True
    assert body["clinical_use_authorized"] is False
    assert body["identifiable_data_supported"] is False
    assert body["patient_derived_data_authorized"] is False
    assert body["allowed_data_classifications"] == ["synthetic"]
    assert body["frontend_integration_authorized"] is False
    assert body["rag_enabled"] is False
    assert "GOV-008" in body["next_stage_blockers"]


def test_expired_governance_review_blocks_new_consultations(monkeypatch):
    monkeypatch.setenv("ORTHO_GOVERNANCE_REVIEW_DUE", "2000-01-01")
    with client:
        health = client.get("/health")
        response = client.post("/v1/consultations", json=START_PAYLOAD)
    assert health.status_code == 200
    assert health.json()["accepting_new_consultations"] is False
    assert response.status_code == 503
    assert "governança vencida" in response.text


def test_deidentified_requires_full_governance_bundle(monkeypatch):
    monkeypatch.setenv("ORTHO_ALLOWED_DATA_CLASSIFICATIONS", "synthetic,deidentified")
    monkeypatch.setenv("ORTHO_GOVERNANCE_APPROVED", "true")
    assert "ORTHO_GOVERNANCE_APPROVAL_REF" in deidentified_governance_errors()
    with pytest.raises(RuntimeError, match="controles ausentes ou inválidos"):
        validate_runtime_configuration()


def test_complete_deidentified_bundle_is_still_not_clinical_authorization(monkeypatch):
    monkeypatch.setenv("ORTHO_ALLOWED_DATA_CLASSIFICATIONS", "synthetic,deidentified")
    monkeypatch.setenv("ORTHO_GOVERNANCE_PROFILE", "deidentified_validation")
    monkeypatch.setenv("ORTHO_GOVERNANCE_APPROVED", "true")
    monkeypatch.setenv("ORTHO_GOVERNANCE_EXPIRES_ON", "2099-12-31")
    monkeypatch.setenv("ORTHO_IDENTITY_MODE", "individual_rbac")
    monkeypatch.setenv("ORTHO_BACKUP_MODE", "managed_pitr")
    monkeypatch.setenv("ORTHO_CHANGE_CONTROL_MODE", "protected_checks")
    for variable_name in GOVERNANCE_REFERENCE_CONTROLS:
        monkeypatch.setenv(variable_name, f"test-reference-{variable_name.lower()}")

    validate_runtime_configuration()
    status = governance_status()
    assert status["patient_derived_data_authorized"] is True
    assert status["clinical_use_authorized"] is False
    assert status["identifiable_data_supported"] is False
    assert status["next_stage_blockers"] == []


def test_capture_and_state_with_explicit_provenance():
    consultation_id = new_session()
    payload = {
        "mode": "PRONTUÁRIO",
        "facts": [
            {
                "field": "queixa",
                "value": "dor no tornozelo do caso sintético",
                "source": "PACIENTE",
                "kind": "RELATO",
                "validated": False,
            },
            {
                "field": "lateralidade",
                "value": "direita",
                "source": "ACHADO MÉDICO",
                "kind": "ACHADO",
                "validated": True,
            },
        ],
    }
    with client:
        captured = client.post(f"/v1/consultations/{consultation_id}/events", json=payload)
        state = client.get(f"/v1/consultations/{consultation_id}")
    assert captured.status_code == 200
    assert captured.json()["facts_recorded"] == 2
    assert state.status_code == 200
    assert state.json()["facts"][0]["kind"] == "RELATO"
    assert state.json()["data_policy"]["data_classification"] == "synthetic"
    assert state.json()["human_review_required"] is True


def test_reported_information_cannot_be_stored_as_physical_exam():
    consultation_id = new_session()
    payload = {
        "facts": [
            {
                "field": "sensibilidade",
                "value": "preservada",
                "source": "PACIENTE",
                "kind": "ACHADO",
            }
        ]
    }
    with client:
        response = client.post(f"/v1/consultations/{consultation_id}/events", json=payload)
    assert response.status_code == 422


def test_ai_suggestion_cannot_arrive_prevalidated():
    consultation_id = new_session()
    payload = {
        "facts": [
            {
                "field": "hipotese_ia",
                "value": "conteúdo sintético",
                "source": "SUGESTÃO IA",
                "kind": "SUGESTÃO_IA",
                "validated": True,
            }
        ]
    }
    with client:
        response = client.post(f"/v1/consultations/{consultation_id}/events", json=payload)
    assert response.status_code == 422


def test_direct_identifiers_are_rejected_without_echoing_them():
    consultation_id = new_session()
    payload = {
        "facts": [
            {
                "field": "cpf",
                "value": "123.456.789-00",
                "source": "PACIENTE",
                "kind": "RELATO",
            }
        ]
    }
    with client:
        response = client.post(f"/v1/consultations/{consultation_id}/events", json=payload)
    assert response.status_code == 422
    assert "123.456.789-00" not in response.text


def test_nested_identifier_keys_are_rejected():
    consultation_id = new_session()
    payload = {
        "facts": [
            {
                "field": "dados_do_caso",
                "value": {"contexto": {"patient_name": "Synthetic Person"}},
                "source": "PACIENTE",
                "kind": "RELATO",
            }
        ]
    }
    with client:
        response = client.post(f"/v1/consultations/{consultation_id}/events", json=payload)
    assert response.status_code == 422
    assert "Synthetic Person" not in response.text


def test_auth_required_only_when_configured(monkeypatch):
    monkeypatch.setenv("ORTHO_API_KEY", "test-secret")
    with client:
        denied = client.post("/v1/consultations", json=START_PAYLOAD)
        allowed = client.post(
            "/v1/consultations",
            headers={"X-Ortho-Api-Key": "test-secret"},
            json=START_PAYLOAD,
        )
    assert denied.status_code == 401
    assert allowed.status_code == 200


def test_baseline_neurovascular_status_is_required():
    consultation_id = new_session()
    payload = {
        **VALID_GATE,
        "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
        "neurovascular": {},
    }
    with client:
        response = client.post(f"/v1/consultations/{consultation_id}/finalize", json=payload)
    assert response.status_code == 409
    assert "neurovascular basal" in response.text


def test_all_safety_flags_must_be_reviewed_explicitly():
    consultation_id = new_session()
    payload = {
        "context": {"case_type": "extremity_trauma", "patient_group": "adult"},
        "neurovascular": {"baseline_documented": True},
        "safety": {**EMPTY_SAFETY},
    }
    payload["safety"].pop("choque")
    with client:
        response = client.post(
            f"/v1/consultations/{consultation_id}/audit", json=payload
        )
    assert response.status_code == 422
    assert "choque" in response.text


def test_post_intervention_neurovascular_blocker():
    consultation_id = new_session()
    payload = {
        **VALID_GATE,
        "intervention": {
            "performed": True,
            "kind": "imobilização sintética",
            "may_change_nv": True,
            "post_nv_documented": False,
        },
    }
    with client:
        response = client.post(f"/v1/consultations/{consultation_id}/finalize", json=payload)
    assert response.status_code == 409
    assert "pós-imobilização" in response.text


def test_priority_alert_requires_documented_response():
    consultation_id = new_session()
    payload = {
        **VALID_GATE,
        "safety": {**EMPTY_SAFETY, "sindrome_compartimental": True},
    }
    with client:
        audit = client.post(f"/v1/consultations/{consultation_id}/audit", json=payload)
    assert audit.status_code == 200
    assert audit.json()["can_finalize"] is False
    assert any("síndrome compartimental" in item for item in audit.json()["alerts"])


def test_finalize_returns_draft_and_is_immutable():
    consultation_id = new_session()
    with client:
        finalized = client.post(f"/v1/consultations/{consultation_id}/finalize", json=VALID_GATE)
        second_finalize = client.post(
            f"/v1/consultations/{consultation_id}/finalize", json=VALID_GATE
        )
        late_event = client.post(
            f"/v1/consultations/{consultation_id}/events",
            json={
                "facts": [
                    {
                        "field": "late_fact",
                        "value": "must not be stored",
                        "source": "SUGESTÃO IA",
                        "kind": "SUGESTÃO_IA",
                    }
                ]
            },
        )
    assert finalized.status_code == 200
    assert finalized.json()["status"] == "draft_ready"
    assert finalized.json()["human_review_required"] is True
    assert second_finalize.status_code == 409
    assert late_event.status_code == 409


def test_feedback_metrics_and_deletion_contain_no_clinical_text():
    consultation_id = new_session()
    feedback_payload = {
        "disposition": "edited",
        "documentation_seconds": 180,
        "corrections_count": 2,
        "false_alerts_count": 1,
        "technical_failure": False,
        "privacy_incident": False,
    }
    with client:
        feedback = client.post(
            f"/v1/consultations/{consultation_id}/pilot-feedback",
            json=feedback_payload,
        )
        metrics = client.get("/v1/pilot/metrics")
        deleted = client.delete(f"/v1/consultations/{consultation_id}")
        missing = client.get(f"/v1/consultations/{consultation_id}")
    assert feedback.status_code == 200
    assert feedback.json()["contains_clinical_text"] is False
    assert metrics.status_code == 200
    assert metrics.json()["contains_clinical_text"] is False
    assert any(item["event_type"] == "feedback" for item in metrics.json()["metrics"])
    assert deleted.status_code == 200
    assert missing.status_code == 404


def test_expired_consultation_is_purged():
    consultation_id = new_session()
    with engine.begin() as connection:
        connection.execute(
            update(consultation_metadata_table)
            .where(consultation_metadata_table.c.session_id == consultation_id)
            .values(expires_at=0)
        )
    result = purge_unclassified_and_expired_sessions()
    with client:
        missing = client.get(f"/v1/consultations/{consultation_id}")
    assert result["expired"] == 1
    assert missing.status_code == 404


def test_evidence_search_is_safe_metadata_only():
    with client:
        response = client.post(
            "/v1/evidence/search",
            json={"query": "fratura exposta da tíbia sintética", "domain": "trauma_adulto"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["routing"]["preferred"] == "Rockwood and Green's Fractures in Adults"
    assert body["items"] == []
    assert "Nenhum trecho protegido" in body["copyright_policy"]


def test_request_body_limit():
    with client:
        response = client.post(
            "/v1/consultations",
            content=b"x" * 65_537,
            headers={"content-type": "application/json"},
        )
    assert response.status_code == 413
