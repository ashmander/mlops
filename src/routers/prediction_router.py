from fastapi import APIRouter, Body
from src.schemas.prediction_data_request import SymptomsSchema
from src.services.prediction_engine import predict

router = APIRouter(
    prefix="/healthy-checker",
    tags=["prediction"]
)

@router.post("/predict")
def predict_disease(
    input_data: SymptomsSchema = Body(
        openapi_examples={
            "healthy": {
                "summary": "🟢 Healthy patient",
                "description": "Patient with no significant symptoms",
                "value": {
                    "fever":               {"present": False, "severity": None, "duration_days": None},
                    "fatigue":             {"present": False, "severity": None, "duration_days": None},
                    "weight_loss":         {"present": False, "severity": None, "duration_days": None},
                    "night_sweats":        {"present": False, "severity": None, "duration_days": None},
                    "cough":               {"present": False, "severity": None, "duration_days": None},
                    "shortness_of_breath": {"present": False, "severity": None, "duration_days": None},
                    "sore_throat":         {"present": False, "severity": None, "duration_days": None},
                    "nausea":              {"present": False, "severity": None, "duration_days": None},
                    "diarrhea":            {"present": False, "severity": None, "duration_days": None},
                    "abdominal_pain":      {"present": False, "severity": None, "duration_days": None},
                    "headache":            {"present": False, "severity": None, "duration_days": None},
                    "dizziness":           {"present": False, "severity": None, "duration_days": None},
                    "joint_pain":          {"present": False, "severity": None, "duration_days": None},
                    "muscle_pain":         {"present": False, "severity": None, "duration_days": None},
                    "rash":                {"present": False, "severity": None, "duration_days": None},
                }
            },
            "mild_disease": {
                "summary": "🟡 Mild disease",
                "description": "Patient with mild symptoms — sore throat and fatigue",
                "value": {
                    "fever":               {"present": False, "severity": None,     "duration_days": None},
                    "fatigue":             {"present": True,  "severity": "mild",   "duration_days": 3},
                    "weight_loss":         {"present": False, "severity": None,     "duration_days": None},
                    "night_sweats":        {"present": False, "severity": None,     "duration_days": None},
                    "cough":               {"present": False, "severity": None,     "duration_days": None},
                    "shortness_of_breath": {"present": False, "severity": None,     "duration_days": None},
                    "sore_throat":         {"present": True,  "severity": "moderate","duration_days": 4},
                    "nausea":              {"present": False, "severity": None,     "duration_days": None},
                    "diarrhea":            {"present": False, "severity": None,     "duration_days": None},
                    "abdominal_pain":      {"present": False, "severity": None,     "duration_days": None},
                    "headache":            {"present": False, "severity": None,     "duration_days": None},
                    "dizziness":           {"present": False, "severity": None,     "duration_days": None},
                    "joint_pain":          {"present": False, "severity": None,     "duration_days": None},
                    "muscle_pain":         {"present": False, "severity": None,     "duration_days": None},
                    "rash":                {"present": False, "severity": None,     "duration_days": None},
                }
            },
            "acute_disease": {
                "summary": "🔵 Acute disease",
                "description": "Patient with severe fever and shortness of breath",
                "value": {
                    "fever":               {"present": True,  "severity": "severe", "duration_days": 2},
                    "fatigue":             {"present": True,  "severity": "moderate","duration_days": 2},
                    "weight_loss":         {"present": False, "severity": None,     "duration_days": None},
                    "night_sweats":        {"present": False, "severity": None,     "duration_days": None},
                    "cough":               {"present": True,  "severity": "severe", "duration_days": 2},
                    "shortness_of_breath": {"present": True,  "severity": "severe", "duration_days": 1},
                    "sore_throat":         {"present": False, "severity": None,     "duration_days": None},
                    "nausea":              {"present": False, "severity": None,     "duration_days": None},
                    "diarrhea":            {"present": False, "severity": None,     "duration_days": None},
                    "abdominal_pain":      {"present": False, "severity": None,     "duration_days": None},
                    "headache":            {"present": False, "severity": None,     "duration_days": None},
                    "dizziness":           {"present": False, "severity": None,     "duration_days": None},
                    "joint_pain":          {"present": False, "severity": None,     "duration_days": None},
                    "muscle_pain":         {"present": False, "severity": None,     "duration_days": None},
                    "rash":                {"present": False, "severity": None,     "duration_days": None},
                }
            },
            "chronic_disease": {
                "summary": "🟠 Chronic disease",
                "description": "Patient with long-term weight loss and night sweats",
                "value": {
                    "fever":               {"present": False, "severity": None,     "duration_days": None},
                    "fatigue":             {"present": True,  "severity": "moderate","duration_days": 60},
                    "weight_loss":         {"present": True,  "severity": "severe", "duration_days": 45},
                    "night_sweats":        {"present": True,  "severity": "moderate","duration_days": 30},
                    "cough":               {"present": False, "severity": None,     "duration_days": None},
                    "shortness_of_breath": {"present": False, "severity": None,     "duration_days": None},
                    "sore_throat":         {"present": False, "severity": None,     "duration_days": None},
                    "nausea":              {"present": False, "severity": None,     "duration_days": None},
                    "diarrhea":            {"present": False, "severity": None,     "duration_days": None},
                    "abdominal_pain":      {"present": False, "severity": None,     "duration_days": None},
                    "headache":            {"present": False, "severity": None,     "duration_days": None},
                    "dizziness":           {"present": False, "severity": None,     "duration_days": None},
                    "joint_pain":          {"present": False, "severity": None,     "duration_days": None},
                    "muscle_pain":         {"present": False, "severity": None,     "duration_days": None},
                    "rash":                {"present": False, "severity": None,     "duration_days": None},
                }
            },
            "terminal_disease": {
                "summary": "🔴 Terminal disease",
                "description": "Patient with severe long-lasting systemic symptoms",
                "value": {
                    "fever":               {"present": False, "severity": None,     "duration_days": None},
                    "fatigue":             {"present": True,  "severity": "severe", "duration_days": 75},
                    "weight_loss":         {"present": True,  "severity": "severe", "duration_days": 75},
                    "night_sweats":        {"present": True,  "severity": "severe", "duration_days": 45},
                    "cough":               {"present": False, "severity": None,     "duration_days": None},
                    "shortness_of_breath": {"present": False, "severity": None,     "duration_days": None},
                    "sore_throat":         {"present": False, "severity": None,     "duration_days": None},
                    "nausea":              {"present": False, "severity": None,     "duration_days": None},
                    "diarrhea":            {"present": False, "severity": None,     "duration_days": None},
                    "abdominal_pain":      {"present": False, "severity": None,     "duration_days": None},
                    "headache":            {"present": False, "severity": None,     "duration_days": None},
                    "dizziness":           {"present": False, "severity": None,     "duration_days": None},
                    "joint_pain":          {"present": False, "severity": None,     "duration_days": None},
                    "muscle_pain":         {"present": False, "severity": None,     "duration_days": None},
                    "rash":                {"present": False, "severity": None,     "duration_days": None},
                }
            },
        }
    )
):
    return predict(input_data)
