"""
Tests unitarios para el motor de predicción.
Validan la lógica de predict() de forma aislada, sin levantar el servidor.
"""

import pytest
from src.schemas.prediction_data_request import Symptom, SymptomsSchema, Severity
from src.schemas.prediction_data_response import DiagnosticResponse
from src.services.prediction_engine import predict


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_symptoms(**overrides) -> SymptomsSchema:
    """
    Construye un SymptomsSchema base (paciente sano) y aplica los overrides
    indicados, para no repetir todos los campos en cada test.
    """
    base = {
        "fever":               Symptom(),
        "fatigue":             Symptom(),
        "weight_loss":         Symptom(),
        "night_sweats":        Symptom(),
        "cough":               Symptom(),
        "shortness_of_breath": Symptom(),
        "sore_throat":         Symptom(),
        "nausea":              Symptom(),
        "diarrhea":            Symptom(),
        "abdominal_pain":      Symptom(),
        "headache":            Symptom(),
        "dizziness":           Symptom(),
        "joint_pain":          Symptom(),
        "muscle_pain":         Symptom(),
        "rash":                Symptom(),
    }
    base.update(overrides)
    return SymptomsSchema(**base)


# ── Test 1: Paciente sano ─────────────────────────────────────────────────────

def test_healthy_patient():
    """
    Un paciente sin ningún síntoma debe ser clasificado como NO ENFERMO.
    """
    data = make_symptoms()
    result = predict(data)

    assert result["prediction"] == DiagnosticResponse.HEALTHY


# ── Test 2: Enfermedad leve ───────────────────────────────────────────────────

def test_mild_disease_sore_throat_and_fatigue():
    """
    Garganta irritada moderada + fatiga → ENFERMEDAD LEVE.
    Corresponde a la primera regla de mild en prediction_engine.
    """
    data = make_symptoms(
        sore_throat=Symptom(present=True, severity=Severity.moderate, duration_days=4),
        fatigue=Symptom(present=True, severity=Severity.mild, duration_days=3),
    )
    result = predict(data)

    assert result["prediction"] == DiagnosticResponse.MILD_DISEASE


# ── Test 3: Enfermedad aguda ──────────────────────────────────────────────────

def test_acute_disease_severe_fever_with_shortness_of_breath():
    """
    Fiebre severa + dificultad respiratoria → ENFERMEDAD AGUDA.
    Es el caso más crítico que el modelo debe detectar correctamente.
    """
    data = make_symptoms(
        fever=Symptom(present=True, severity=Severity.severe, duration_days=2),
        shortness_of_breath=Symptom(present=True, severity=Severity.severe, duration_days=1),
    )
    result = predict(data)

    assert result["prediction"] == DiagnosticResponse.ACUTE_DISEASE


# ── Test 4: Enfermedad crónica ────────────────────────────────────────────────

def test_chronic_disease_weight_loss_and_fatigue():
    """
    Pérdida de peso prolongada (>30 días) + fatiga → ENFERMEDAD CRÓNICA.
    Valida la detección de patrones crónicos de larga duración.
    """
    data = make_symptoms(
        weight_loss=Symptom(present=True, severity=Severity.severe, duration_days=45),
        fatigue=Symptom(present=True, severity=Severity.moderate, duration_days=60),
    )
    result = predict(data)

    assert result["prediction"] == DiagnosticResponse.CHRONIC_DISEASE
