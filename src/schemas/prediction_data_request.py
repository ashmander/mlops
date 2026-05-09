from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Severity(str, Enum):
    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class Symptom(BaseModel):
    present: bool = Field(
        default=False,
        description="Indicates whether the symptom is present"
    )
    severity: Optional[Severity] = Field(
        default=None,
        description="Severity level of the symptom"
    )
    duration_days: Optional[int] = Field(
        default=None,
        ge=1,           # mayor o igual a 1
        le=365,         # máximo 1 año
        description="Duration of the symptom in days"
    )


class SymptomsSchema(BaseModel):
    # General
    fever: Symptom = Field(default=Symptom(), description="High body temperature")
    fatigue: Symptom = Field(default=Symptom(), description="Persistent tiredness or exhaustion")
    weight_loss: Symptom = Field(default=Symptom(), description="Unintentional weight loss")
    night_sweats: Symptom = Field(default=Symptom(), description="Excessive sweating during sleep")

    # Respiratory
    cough: Symptom = Field(default=Symptom(), description="Persistent cough")
    shortness_of_breath: Symptom = Field(default=Symptom(), description="Difficulty breathing")
    sore_throat: Symptom = Field(default=Symptom(), description="Pain or irritation in the throat")

    # Gastrointestinal
    nausea: Symptom = Field(default=Symptom(), description="Feeling of sickness with urge to vomit")
    diarrhea: Symptom = Field(default=Symptom(), description="Loose or watery stools")
    abdominal_pain: Symptom = Field(default=Symptom(), description="Pain in the abdominal area")

    # Neurological
    headache: Symptom = Field(default=Symptom(), description="Pain in the head or neck area")
    dizziness: Symptom = Field(default=Symptom(), description="Feeling of being unsteady or lightheaded")

    # Musculoskeletal
    joint_pain: Symptom = Field(default=Symptom(), description="Pain in one or more joints")
    muscle_pain: Symptom = Field(default=Symptom(), description="Pain or aching in muscles")

    # Skin
    rash: Symptom = Field(default=Symptom(), description="Skin irritation or discoloration")

    model_config = {
        "json_schema_extra": {
            "example": {
                "fever": {"present": True, "severity": "severe", "duration_days": 3},
                "cough": {"present": True, "severity": "moderate", "duration_days": 7},
                "fatigue": {"present": False, "severity": None, "duration_days": None}
            }
        }
    }