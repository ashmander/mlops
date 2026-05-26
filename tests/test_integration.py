"""
Tests de integración para el endpoint POST /healthy-checker/predict.
Usa TestClient de FastAPI para levantar la app en memoria sin servidor real.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

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
