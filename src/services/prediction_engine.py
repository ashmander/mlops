from src.schemas.prediction_data_request import Severity, SymptomsSchema
from src.schemas.prediction_data_response import DiagnosticResponse

def predict(input_data: SymptomsSchema):
    """
    Mock prediction function. In a real implementation, this would
    load a trained model and make predictions based on the input data.
    """

    # Acute — severity symptoms that require immediate attention
    if (input_data.fever.present and input_data.fever.severity == Severity.severe
            and input_data.shortness_of_breath.present):
        return {"prediction": DiagnosticResponse.ACUTE_DISEASE}

    if (input_data.cough.present and input_data.cough.severity == Severity.severe
            and input_data.fever.present):
        return {"prediction": DiagnosticResponse.ACUTE_DISEASE}

    # Chronic — symptoms that persist for a long time or recur frequently
    if (input_data.weight_loss.present
            and input_data.weight_loss.duration_days is not None
            and input_data.weight_loss.duration_days > 30
            and input_data.fatigue.present):
        return {"prediction": DiagnosticResponse.CHRONIC_DISEASE}

    if (input_data.night_sweats.present
            and input_data.night_sweats.duration_days is not None
            and input_data.night_sweats.duration_days > 21):
        return {"prediction": DiagnosticResponse.CHRONIC_DISEASE}

    # Mild — moderate or mild symptoms that do not require immediate attention
    if (input_data.sore_throat.present and input_data.sore_throat.severity == Severity.moderate
            and input_data.fatigue.present):
        return {"prediction": DiagnosticResponse.MILD_DISEASE}

    if input_data.fatigue.present and input_data.fatigue.severity == Severity.mild:
        return {"prediction": DiagnosticResponse.MILD_DISEASE}

    # Healthy — no significant symptoms or only mild symptoms that do not indicate a disease
    return {"prediction": DiagnosticResponse.HEALTHY}