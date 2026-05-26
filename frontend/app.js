const symptoms = [
  ["fever", "Fiebre"],
  ["fatigue", "Fatiga"],
  ["weight_loss", "Perdida de peso"],
  ["night_sweats", "Sudoracion nocturna"],
  ["cough", "Tos"],
  ["shortness_of_breath", "Dificultad respiratoria"],
  ["sore_throat", "Dolor de garganta"],
  ["nausea", "Nausea"],
  ["diarrhea", "Diarrea"],
  ["abdominal_pain", "Dolor abdominal"],
  ["headache", "Dolor de cabeza"],
  ["dizziness", "Mareo"],
  ["joint_pain", "Dolor articular"],
  ["muscle_pain", "Dolor muscular"],
  ["rash", "Erupcion"],
];

const form = document.querySelector("#prediction-form");
const grid = document.querySelector("#symptom-grid");
const resultBox = document.querySelector("#prediction-result");
const countsContainer = document.querySelector("#category-counts");
const lastPredictionAt = document.querySelector("#last-prediction-at");
const lastPredictions = document.querySelector("#last-predictions");

function renderSymptomControls() {
  grid.innerHTML = symptoms.map(([name, label]) => `
    <div class="symptom-card">
      <label><input type="checkbox" name="${name}_present"> ${label}</label>
      <select name="${name}_severity">
        <option value="">Sin severidad</option>
        <option value="mild">Leve</option>
        <option value="moderate">Moderada</option>
        <option value="severe">Severa</option>
      </select>
      <input type="number" name="${name}_duration_days" min="1" max="365" placeholder="Dias">
    </div>
  `).join("");
}

function buildPayload() {
  const data = new FormData(form);
  const payload = {};

  symptoms.forEach(([symptom]) => {
    const duration = data.get(`${symptom}_duration_days`);
    payload[symptom] = {
      present: data.get(`${symptom}_present`) === "on",
      severity: data.get(`${symptom}_severity`) || null,
      duration_days: duration ? Number(duration) : null,
    };
  });

  return payload;
}

function setSymptom(symptom, present, severity, durationDays) {
  form.elements[`${symptom}_present`].checked = present;
  form.elements[`${symptom}_severity`].value = severity || "";
  form.elements[`${symptom}_duration_days`].value = durationDays || "";
}

function resetForm() {
  symptoms.forEach(([symptom]) => setSymptom(symptom, false, null, null));
  resultBox.className = "result-box";
  resultBox.textContent = "Sin prediccion todavia";
}

function loadTerminalExample() {
  resetForm();
  setSymptom("fatigue", true, "severe", 75);
  setSymptom("weight_loss", true, "severe", 75);
  setSymptom("night_sweats", true, "severe", 45);
}

function formatDate(value) {
  if (!value) {
    return "Sin datos";
  }

  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function submitPrediction(event) {
  event.preventDefault();
  resultBox.className = "result-box";
  resultBox.textContent = "Procesando prediccion...";

  try {
    const response = await fetch("/healthy-checker/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });

    if (!response.ok) {
      throw new Error("No fue posible realizar la prediccion");
    }

    const body = await response.json();
    resultBox.className = "result-box has-result";
    resultBox.textContent = `Resultado: ${body.prediction}`;
    await loadStatistics();
  } catch (error) {
    resultBox.className = "result-box has-error";
    resultBox.textContent = error.message;
  }
}

async function loadStatistics() {
  const response = await fetch("/healthy-checker/statistics");

  if (!response.ok) {
    throw new Error("No fue posible cargar estadisticas");
  }

  const stats = await response.json();
  renderCounts(stats.total_predictions_by_category);
  renderHistory(stats.last_5_predictions);
  lastPredictionAt.textContent = formatDate(stats.last_prediction_at);
}

function renderCounts(counts) {
  countsContainer.innerHTML = "";

  Object.entries(counts).forEach(([category, total]) => {
    const row = document.createElement("div");
    const label = document.createElement("dt");
    const value = document.createElement("dd");

    label.textContent = category;
    value.textContent = total;
    row.append(label, value);
    countsContainer.append(row);
  });
}

function renderHistory(predictions) {
  lastPredictions.innerHTML = "";

  if (!predictions.length) {
    const empty = document.createElement("li");
    empty.textContent = "No hay predicciones registradas";
    lastPredictions.append(empty);
    return;
  }

  [...predictions].reverse().forEach((record) => {
    const item = document.createElement("li");
    const prediction = document.createElement("strong");
    const date = document.createElement("span");

    prediction.textContent = record.prediction;
    date.textContent = formatDate(record.created_at);
    item.append(prediction, date);
    lastPredictions.append(item);
  });
}

renderSymptomControls();
form.addEventListener("submit", submitPrediction);
document.querySelector("#reset-button").addEventListener("click", resetForm);
document.querySelector("#healthy-example").addEventListener("click", resetForm);
document.querySelector("#terminal-example").addEventListener("click", loadTerminalExample);
document.querySelector("#refresh-stats").addEventListener("click", () => loadStatistics());

resetForm();
loadStatistics().catch(() => {
  countsContainer.innerHTML = "";
  lastPredictionAt.textContent = "Sin datos";
});
