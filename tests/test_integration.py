"""
Tests de integración para el endpoint POST /healthy-checker/predict.
Usa TestClient de FastAPI para levantar la app en memoria sin servidor real.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def prediction_history_file(tmp_path, monkeypatch):
    monkeypatch.setenv("PREDICTION_HISTORY_FILE", str(tmp_path / "prediction_history.jsonl"))

# ── Payload helpers ───────────────────────────────────────────────────────────

def symptom(present=False, severity=None, duration_days=None):
    return {"present": present, "severity": severity, "duration_days": duration_days}


BASE_PAYLOAD = {
    "fever":               symptom(),
    "fatigue":             symptom(),
    "weight_loss":         symptom(),
    "night_sweats":        symptom(),
    "cough":               symptom(),
    "shortness_of_breath": symptom(),
    "sore_throat":         symptom(),
    "nausea":              symptom(),
    "diarrhea":            symptom(),
    "abdominal_pain":      symptom(),
    "headache":            symptom(),
    "dizziness":           symptom(),
    "joint_pain":          symptom(),
    "muscle_pain":         symptom(),
    "rash":                symptom(),
}


def make_payload(**overrides):
    payload = {**BASE_PAYLOAD}
    payload.update(overrides)
    return payload


# ── Test 1: Respuesta HTTP correcta con paciente sano ─────────────────────────

def test_endpoint_returns_200_healthy():
    """
    El endpoint debe responder 200 OK y retornar 'NO ENFERMO'
    cuando todos los síntomas están ausentes.
    """
    response = client.post("/healthy-checker/predict", json=make_payload())

    assert response.status_code == 200
    body = response.json()
    assert "prediction" in body
    assert body["prediction"] == "NO ENFERMO"


# ── Test 2: Predicción AGUDA via endpoint ─────────────────────────────────────

def test_endpoint_acute_disease():
    """
    Fiebre severa + dificultad respiratoria enviados al endpoint
    deben retornar 'ENFERMEDAD AGUDA' con status 200.
    """
    payload = make_payload(
        fever=symptom(present=True, severity="severe", duration_days=2),
        shortness_of_breath=symptom(present=True, severity="severe", duration_days=1),
    )
    response = client.post("/healthy-checker/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] == "ENFERMEDAD AGUDA"


# ── Test 3: Predicción CRÓNICA via endpoint ───────────────────────────────────

def test_endpoint_chronic_disease():
    """
    Pérdida de peso severa prolongada + fatiga enviados al endpoint
    deben retornar 'ENFERMEDAD CRÓNICA' con status 200.
    """
    payload = make_payload(
        weight_loss=symptom(present=True, severity="severe", duration_days=45),
        fatigue=symptom(present=True, severity="moderate", duration_days=60),
    )
    response = client.post("/healthy-checker/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] == "ENFERMEDAD CRÓNICA"


# ── Test 4: Payload inválido retorna 422 ──────────────────────────────────────

def test_endpoint_terminal_disease():
    """
    Sintomas sistemicos severos y prolongados enviados al endpoint
    deben retornar 'ENFERMEDAD TERMINAL' con status 200.
    """
    payload = make_payload(
        weight_loss=symptom(present=True, severity="severe", duration_days=75),
        fatigue=symptom(present=True, severity="severe", duration_days=75),
        night_sweats=symptom(present=True, severity="severe", duration_days=45),
    )
    response = client.post("/healthy-checker/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] == "ENFERMEDAD TERMINAL"


def test_endpoint_invalid_severity_returns_422():
    """
    Un valor de severity inválido debe ser rechazado por Pydantic
    y el endpoint debe retornar 422 Unprocessable Entity.
    Valida que la validación de esquema funciona correctamente.
    """
    payload = make_payload(
        fever=symptom(present=True, severity="INVALID_SEVERITY", duration_days=2),
    )
    response = client.post("/healthy-checker/predict", json=payload)

    assert response.status_code == 422


def test_endpoint_prediction_statistics():
    payloads = [
        make_payload(),
        make_payload(
            fever=symptom(present=True, severity="severe", duration_days=2),
            shortness_of_breath=symptom(present=True, severity="severe", duration_days=1),
        ),
        make_payload(
            weight_loss=symptom(present=True, severity="severe", duration_days=45),
            fatigue=symptom(present=True, severity="moderate", duration_days=60),
        ),
        make_payload(
            weight_loss=symptom(present=True, severity="severe", duration_days=75),
            fatigue=symptom(present=True, severity="severe", duration_days=75),
            night_sweats=symptom(present=True, severity="severe", duration_days=45),
        ),
        make_payload(
            sore_throat=symptom(present=True, severity="moderate", duration_days=4),
            fatigue=symptom(present=True, severity="mild", duration_days=3),
        ),
        make_payload(),
    ]

    for payload in payloads:
        response = client.post("/healthy-checker/predict", json=payload)
        assert response.status_code == 200

    response = client.get("/healthy-checker/statistics")

    assert response.status_code == 200
    body = response.json()
    assert body["total_predictions_by_category"] == {
        "NO ENFERMO": 2,
        "ENFERMEDAD LEVE": 1,
        "ENFERMEDAD AGUDA": 1,
        "ENFERMEDAD TERMINAL": 1,
        "ENFERMEDAD CRÓNICA": 1,
    }
    assert len(body["last_5_predictions"]) == 5
    assert body["last_5_predictions"][-1]["prediction"] == "NO ENFERMO"
    assert body["last_prediction_at"] == body["last_5_predictions"][-1]["created_at"]
