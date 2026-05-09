from pydantic import BaseModel
from enum import Enum

class DiagnosticResponse(str, Enum):
    HEALTHY = "NO ENFERMO"
    MILD_DISEASE = "ENFERMEDAD LEVE"
    ACUTE_DISEASE = "ENFERMEDAD AGUDA"
    CHRONIC_DISEASE = "ENFERMEDAD CRÓNICA"

