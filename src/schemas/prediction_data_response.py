from pydantic import BaseModel
from enum import Enum

class DiagnosticResponse(str, Enum):
    HEALTHY = "NO ENFERMO"
    MILD_DISEASE = "ENFERMEDAD LEVE"
    ACUTE_DISEASE = "ENFERMEDAD AGUDA"
    TERMINAL_DISEASE = "ENFERMEDAD TERMINAL"
    CHRONIC_DISEASE = "ENFERMEDAD CRÓNICA"

