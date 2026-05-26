import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.schemas.prediction_data_response import DiagnosticResponse


DEFAULT_HISTORY_FILE = Path("data/prediction_history.jsonl")


def _history_file() -> Path:
    return Path(os.getenv("PREDICTION_HISTORY_FILE", DEFAULT_HISTORY_FILE))


def save_prediction(prediction: DiagnosticResponse) -> dict:
    record = {
        "prediction": prediction.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    history_file = _history_file()
    history_file.parent.mkdir(parents=True, exist_ok=True)

    with history_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def get_prediction_statistics() -> dict:
    records = _read_prediction_history()
    counts = Counter(record["prediction"] for record in records)

    return {
        "total_predictions_by_category": {
            category.value: counts.get(category.value, 0)
            for category in DiagnosticResponse
        },
        "last_5_predictions": records[-5:],
        "last_prediction_at": records[-1]["created_at"] if records else None,
    }


def _read_prediction_history() -> list[dict]:
    history_file = _history_file()
    if not history_file.exists():
        return []

    records = []
    with history_file.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    return records
