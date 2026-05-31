# MLOps Pipeline v2 — Diagnóstico de Enfermedades Huérfanas

> **Versión:** 2.0  
> **Fecha:** Mayo 2026  
> **Equipo:** Proyecto de diagnóstico asistido por IA para enfermedades huérfanas

---

## Índice

1. [Puntos de entrada al sistema](#1-puntos-de-entrada-al-sistema)
2. [Arquitectura general y decisión local/cloud](#2-arquitectura-general-y-decisión-localcloud)
3. [Etapa 1 — Centralización de la fuente de datos](#etapa-1--centralización-de-la-fuente-de-datos)
4. [Etapa 2 — Limpieza, transformación y aumentación ↻](#etapa-2--limpieza-transformación-y-aumentación-)
5. [Etapa 3 — Experimentos DS ↻](#etapa-3--experimentos-ds-)
6. [Etapa 4 — Tests unitarios](#etapa-4--tests-unitarios)
7. [Etapa 5 — Automatización de ingeniería de datos](#etapa-5--automatización-de-ingeniería-de-datos)
8. [Etapa 6 — Generación de artefactos](#etapa-6--generación-de-artefactos)
9. [Etapa 7 — Tests del modelo](#etapa-7--tests-del-modelo)
10. [Etapa 8 — Tests de integración](#etapa-8--tests-de-integración)
11. [Etapa 9 — Despliegue canary](#etapa-9--despliegue-canary)
12. [Etapa 10 — Monitoreo de métricas](#etapa-10--monitoreo-de-métricas)
13. [Trigger de reentrenamiento](#trigger-de-reentrenamiento-)
14. [Resumen de ciclos](#resumen-de-ciclos)
15. [Stack tecnológico completo](#stack-tecnológico-completo)
16. [CHANGELOG v1 → v2](#changelog-v1--v2)

---

## 1. Puntos de entrada al sistema

El sistema tiene dos puntos de entrada bien diferenciados que coexisten:

### 1.1 API REST — Predicción en tiempo real

- **Quién lo usa:** el médico, desde el frontend (navegador o app local).
- **Cómo funciona:** el médico ingresa los síntomas del paciente mediante un formulario; el frontend hace una petición HTTP POST al endpoint `/predict` del modelo. El modelo retorna en milisegundos la predicción de enfermedad con su probabilidad por clase.
- **Rol de la predicción:** sirve como punto de contraste frente al diagnóstico previo del médico, **no como reemplazo**. El médico mantiene la autoridad clínica.
- **Tecnología frontend:** React (SPA ligera) + Axios para llamadas HTTP.
- **Tecnología backend de inferencia:** FastAPI (Python), empaquetado en Docker.

> **Suposición:** los síntomas se capturan con tres tipos de campo: severidad (categórico ordinal: leve/moderada/severa), duración en días (numérico entero) y presencia del síntoma (booleano). El esquema es fijo y validado en el frontend antes de enviar.

### 1.2 Batch diario — Reentrenamiento

- **Quién lo genera:** al final del día, el sistema recopila automáticamente las consultas donde el médico ya realizó el seguimiento del paciente y confirmó o corrigió el diagnóstico.
- **Filtro crítico:** **solo ingresan registros con diagnóstico médico confirmado**. Los registros sin cierre clínico quedan en espera hasta que el médico los valide.
- **Tecnología:** Apache Airflow DAG programado a las 23:00 horas locales. El DAG consulta la base de datos de consultas del día y extrae únicamente los registros con campo `diagnosis_confirmed = True`.

---

## 2. Arquitectura general y decisión local/cloud

Una restricción explícita del problema es que **el médico puede correr la solución en su computador local** si los recursos son bajos, o puede hacer peticiones a un servidor cloud. Se define la siguiente arquitectura bifurcada:

### Opción A — Despliegue local (recursos bajos)

| Componente | Tecnología |
|---|---|
| Orquestación de servicios | Docker Compose |
| API de inferencia | FastAPI en contenedor Docker |
| Base de datos | PostgreSQL en contenedor Docker |
| Feature Store | Feast con backend Redis (local) |
| Tracking de experimentos | MLflow local (sqlite backend) |
| Monitoreo | Grafana + Prometheus (contenedores) |

**Ventajas:** sin costos cloud, datos no salen de la máquina del médico, privacidad máxima.  
**Desventajas:** el reentrenamiento con muchos registros puede ser lento; el canary deployment se simula cambiando el contenedor activo.

> **Suposición:** en despliegue local, el "canary" se implementa con dos contenedores Docker en puertos distintos y un script de validación que redirige tráfico manualmente. No se usa Kubernetes ni Istio.

### Opción B — Despliegue cloud (producción escalable)

| Componente | Tecnología |
|---|---|
| Orquestación de contenedores | AWS EKS (Kubernetes) |
| API de inferencia | FastAPI en pods EKS |
| Base de datos raw | AWS RDS (PostgreSQL) |
| Almacenamiento de artefactos | AWS S3 |
| Feature Store | Feast con backend Redis (ElastiCache) |
| Tracking de experimentos | MLflow con S3 artifact store |
| Orquestación de pipelines | Apache Airflow (MWAA o self-hosted) |
| Monitoreo | Prometheus + Grafana Cloud |
| CI/CD | GitHub Actions |
| Canary | NGINX Ingress Controller o Istio |

**Ventajas:** escalabilidad horizontal, alta disponibilidad, canary real con control de tráfico por porcentaje.  
**Desventajas:** costo mensual, configuración inicial más compleja.

> **Suposición:** dado que las enfermedades huérfanas implican pocos pacientes por definición, **la opción A (local) es viable en etapas tempranas**. La opción B se recomienda una vez el modelo está validado clínicamente y se necesita escalar a múltiples hospitales o centros médicos.

---

## Etapa 1 — Centralización de la fuente de datos

### Descripción

Mediante un **proceso batch diario** (Airflow DAG) se recopilan las consultas del día que ya cuentan con diagnóstico médico confirmado y se almacenan en la base de datos centralizada de datos crudos. El proceso incluye anonimización de datos antes del almacenamiento.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **Apache Airflow** | Orquestador del batch diario | Estándar de la industria para pipelines de datos con scheduling, reintentos y monitoreo de DAGs. Permite definir el flujo como código (DAG en Python). |
| **PostgreSQL** (local Docker / AWS RDS cloud) | Almacén de datos crudos | Relacional, soporta los tipos de datos del problema (categóricos, numéricos, booleanos). Bien integrado con Python y Airflow. Opción local con Docker y cloud con RDS sin cambios de código. |
| **Python + hashlib (SHA-256)** | Anonimización | Los identificadores del paciente (nombre, ID) se reemplazan por hashes SHA-256 antes de almacenar. No es reversible, cumple con requisitos de privacidad clínica. |
| **AWS S3** (solo cloud) | Backup de datos crudos en formato Parquet | Almacenamiento barato y duradero. Parquet permite lectura eficiente por columnas. |

### Suposiciones

- **Solo datos validados ingresan:** un registro solo entra al pipeline si tiene `diagnosis_confirmed = True` en la tabla de consultas. Registros sin cierre clínico se omiten. Esta restricción garantiza que el modelo aprenda de diagnósticos correctos, no de hipótesis.
- **Anonimización obligatoria:** antes de almacenar en la fuente centralizada, se eliminan o hashean todos los campos que puedan identificar al paciente (nombre, fecha de nacimiento exacta, número de historia clínica). El campo `patient_id` se reemplaza por un UUID generado por hash.
- **Schema fijo:** los datos tienen tres tipos de campo — `severity` (string: "mild"/"moderate"/"severe"), `duration_days` (int), `symptom_present` (bool) — más el label `disease_class` (string). Cualquier registro que no cumpla este schema es rechazado y registrado en un log de errores.
- **Frecuencia del batch:** una vez al día, al final de la jornada médica. Si en un día no hay registros validados nuevos, el DAG termina exitosamente sin escribir nada (idempotente).

---

## Etapa 2 — Limpieza, transformación y aumentación ↻

### Descripción

A partir de los datos crudos de la fuente centralizada se realiza análisis exploratorio, limpieza, estandarización, encoding y generación de features. Se evalúa la viabilidad de técnicas de aumentación para las enfermedades huérfanas. Esta etapa es **iterativa**: si los datos no son suficientes en cantidad o calidad, se re-evalúa la estrategia antes de continuar.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **Pandas** | EDA, limpieza, transformación | Librería estándar para manipulación tabular en Python. Suficiente para los volúmenes esperados (enfermedades huérfanas implican pocos registros). |
| **Great Expectations** | Validación de calidad de datos | Permite definir "expectativas" sobre los datos (e.g., `severity` solo puede ser uno de tres valores, `duration_days` ≥ 0) y generar reportes automáticos de calidad. Se integra con Airflow. |
| **scikit-learn (OrdinalEncoder, StandardScaler)** | Encoding y normalización | `OrdinalEncoder` para `severity` (leve < moderada < severa), `StandardScaler` para `duration_days`. Los booleans se mantienen como 0/1. |
| **imbalanced-learn (SMOTE)** | Aumentación para clases desbalanceadas | SMOTE genera muestras sintéticas interpolando entre registros existentes del mismo label. Es la primera opción para enfermedades huérfanas con pocos registros validados. |
| **Conditional GAN (PyTorch, opcional)** | Aumentación avanzada | Si SMOTE no es suficiente o produce datos no realistas (síntomas clínicamente incoherentes), se evalúa entrenar una cGAN condicionada al label de enfermedad. Opción de mayor costo computacional. |
| **DVC (Data Version Control)** | Versionado de datasets | Permite rastrear qué versión del dataset (crudos + aumentados) produjo cada experimento. Se integra con Git. |
| **Feast** | Feature Store | Almacena las features ya procesadas y las sirve tanto para entrenamiento (offline store) como para inferencia en tiempo real (online store). Evita duplicar la lógica de transformación entre entrenamiento y producción. |

### Suposiciones

- **Umbral de suficiencia:** se define como mínimo **30 registros por clase de enfermedad huérfana** para considerar los datos suficientes. Por debajo de este umbral se activa la estrategia de aumentación.
- **Encoding de severidad:** se asume orden semántico válido (leve < moderada < severa), por lo que se usa `OrdinalEncoder` en lugar de One-Hot Encoding. Si el modelo no captura bien esta relación, se puede cambiar a One-Hot en la siguiente iteración.
- **SMOTE primero, GAN después:** se intenta SMOTE primero por su simplicidad y bajo costo computacional. Si un experto clínico indica que las muestras sintéticas son clínicamente incoherentes, se escala a GAN con restricciones de dominio.
- **Feature Store como contrato:** la interfaz entre esta etapa y las etapas de entrenamiento e inferencia es el Feature Store (Feast). Ninguna etapa downstream relee los datos crudos; siempre consumen desde Feast. Esto garantiza consistencia entre entrenamiento y producción (evita el "training-serving skew").

---

## Etapa 3 — Experimentos DS ↻

### Descripción

Con los datos del Feature Store se ejecutan múltiples experimentos de entrenamiento y evaluación. Se exploran modelos clásicos como baseline y redes neuronales para capturar relaciones no lineales. El ciclo se repite hasta identificar la mejor configuración.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **MLflow** (Tracking Server) | Registro de experimentos | Registra automáticamente hiperparámetros, métricas (recall por clase, F1, AUC), artefactos y la versión del dataset usada. Permite comparar experimentos visualmente. |
| **Git + ramas por experimento** | Control de versiones del código | Cada experimento vive en su propia rama (e.g., `exp/xgboost-smote-v2`). Facilita reproducibilidad y revisión entre pares. |
| **scikit-learn** | Random Forest, SVM, Logistic Regression | Baselines rápidos de implementar. Random Forest es robusto ante features de tipos mixtos (categórico + numérico + booleano). SVM funciona bien con datos de alta dimensionalidad y pocos registros. |
| **XGBoost** | Gradient Boosting | Excelente rendimiento en datos tabulares desbalanceados con el parámetro `scale_pos_weight`. |
| **PyTorch** | Redes neuronales (MLP) | Para capturar interacciones no lineales complejas entre síntomas. Se usa en experimentos avanzados si los modelos clásicos no alcanzan el recall objetivo. |
| **Optuna** | Optimización de hiperparámetros | Búsqueda eficiente de hiperparámetros mediante pruning de trials no prometedores. Se integra con MLflow para registrar cada trial. |
| **Jupyter / VS Code** | Entorno de experimentación | Jupyter para exploración inicial; scripts `.py` en VS Code para experimentos formalizados y reproducibles. |

### Criterio de selección de modelo

El criterio principal es el **recall por clase**, con énfasis especial en las enfermedades huérfanas. Se prefiere un modelo con alto recall en huérfanas aunque tenga menor precisión global, porque **un falso negativo en una enfermedad huérfana (dejar de diagnosticarla) tiene consecuencias clínicas graves**.

Se define un umbral mínimo de recall por clase de **0.75** para enfermedades comunes y **0.85** para huérfanas. Si ningún modelo alcanza estos umbrales, se regresa a la Etapa 2 para re-evaluar la estrategia de aumentación o recopilar más datos.

### Suposiciones

- **El médico no tiene acceso a esta etapa:** los experimentos son trabajo interno del equipo de ML. El médico solo interactúa con el modelo ya desplegado.
- **Reproducibilidad total:** cada experimento fija las semillas aleatorias (`random_state=42` en scikit-learn, `torch.manual_seed(42)` en PyTorch). El dataset usado se referencia por su hash DVC.
- **No se usa AutoML:** se prefiere control explícito sobre el proceso para poder justificar clínicamente las decisiones del modelo.

---

## Etapa 4 — Tests unitarios

### Descripción

Pruebas sobre los componentes aislados del pipeline: funciones de preprocesamiento, lógica de aumentación, lectura del Feature Store y formato de salida del modelo. Se ejecutan automáticamente en cada Pull Request mediante CI.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **pytest** | Framework de tests | Estándar en Python. Permite fixtures, parametrización y cobertura. |
| **pytest-cov** | Cobertura de código | Se exige mínimo 80% de cobertura en los módulos críticos (preprocesamiento, aumentación). |
| **GitHub Actions** | CI automático | En cada PR o push a `main`, GitHub Actions corre la suite de tests. Si falla algún test, el merge es bloqueado. |
| **unittest.mock / pytest-mock** | Mocking | Para aislar funciones que dependen de la base de datos o del Feature Store en los tests unitarios. |

### Tests clave

- `test_encoding_severity`: verifica que `OrdinalEncoder` asigna los valores correctos (leve=0, moderada=1, severa=2).
- `test_smote_output_shape`: verifica que SMOTE genera el número correcto de muestras sintéticas por clase.
- `test_feast_read_schema`: verifica que las features leídas del Feature Store tienen el schema esperado.
- `test_model_output_format`: verifica que la salida del modelo es un array de probabilidades con forma `(n_samples, n_classes)`.
- `test_anonymization`: verifica que ningún campo con PII sobrevive al proceso de anonimización.

### Suposiciones

- Los tests unitarios corren en menos de 2 minutos para no bloquear el flujo de desarrollo.
- Los tests unitarios no requieren conexión a la base de datos real ni al Feature Store de producción; usan datos sintéticos en memoria.

---

## Etapa 5 — Automatización de ingeniería de datos

### Descripción

El proceso de limpieza y transformación validado en la fase experimental se estandariza como pipeline automático activado por el Trigger de reentrenamiento. Implementa una arquitectura Medallion: **Bronze → Silver → Gold**.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **Apache Airflow** | Orquestador del pipeline de datos | El mismo DAG del batch diario (Etapa 1) lanza este pipeline como paso siguiente. Permite reintentos, alertas y monitoreo del progreso. |
| **dbt (data build tool)** | Transformaciones SQL estructuradas | dbt estandariza las transformaciones de Bronze → Silver → Gold como modelos SQL versionados en Git. Genera documentación automática y permite tests de calidad en cada capa. |
| **Feast** | Materialización al Feature Store de producción | Una vez que los datos están en la capa Gold, Feast los materializa en el Feature Store de producción (online + offline stores). |
| **Great Expectations** | Validación en cada capa | Se validan los datos en cada transición (Bronze → Silver → Gold) para detectar anomalías antes de que lleguen al entrenamiento. |

### Capas Medallion

| Capa | Contenido | Acción |
|---|---|---|
| **Bronze** | Datos validados tal como llegan de la fuente centralizada (crudos, anonimizados) | Ingesta sin transformación. Preserva los datos originales. |
| **Silver** | Datos limpios, sin valores faltantes, con encoding aplicado | Limpieza, imputación, `OrdinalEncoder`, `StandardScaler`, cast de tipos. |
| **Gold** | Features finales listas para entrenamiento, con aumentación si aplica | SMOTE/GAN aplicados, features adicionales derivadas (e.g., `symptom_count`). |

### Suposiciones

- **Esta etapa no se ejecuta en cada batch diario:** el pipeline de ingeniería de datos de producción se activa únicamente cuando el Trigger de reentrenamiento lo indica. El batch diario solo alimenta la fuente centralizada (Etapa 1); la Etapa 5 se activa cuando hay suficientes registros nuevos para reentrenar.
- **Los registros procesados se acumulan:** la Etapa 5 procesa **todos los registros validados acumulados desde el último reentrenamiento**, no solo los del día. Esto maximiza el volumen disponible para el nuevo modelo.

---

## Etapa 6 — Generación de artefactos

### Descripción

Con los datos del Feature Store de producción (capa Gold) se entrena el modelo seleccionado en la Etapa 3. El artefacto resultante (modelo serializado + metadatos) queda versionado en el Model Registry.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **scikit-learn / XGBoost / PyTorch** | Entrenamiento del modelo | El modelo específico depende de qué configuración ganó en la Etapa 3. El código de entrenamiento es el mismo que el del experimento ganador, pero ejecutado con los datos de producción. |
| **MLflow** (Model Registry) | Versionado y registro del modelo | Almacena el modelo serializado (pickle para scikit-learn, ONNX o `mlflow.pytorch` para PyTorch), sus métricas de entrenamiento, el hash del dataset usado y la versión del código. Permite transiciones de estado: Staging → Production → Archived. |
| **joblib / ONNX** | Serialización del modelo | `joblib` para modelos de scikit-learn (más eficiente que pickle para arrays NumPy). ONNX para modelos PyTorch, permitiendo inferencia en entornos sin PyTorch instalado. |
| **GitHub Actions** | Automatización del entrenamiento | El workflow de reentrenamiento se dispara automáticamente cuando el Trigger activa el pipeline (via webhook o Airflow). |

### Suposiciones

- **El modelo en producción siempre está en el registry:** nunca se despliega un modelo que no haya sido registrado en MLflow. Esto garantiza trazabilidad completa.
- **El artefacto incluye el preprocesador:** el objeto serializado es un `Pipeline` de scikit-learn que encapsula el preprocesador (encoder + scaler) y el modelo. Esto elimina el riesgo de training-serving skew en el preprocesamiento.
- **Metadatos del modelo:** cada versión en el registry incluye: fecha de entrenamiento, hash del dataset, recall por clase en validación, hiperparámetros usados y referencia al experimento MLflow de origen.

---

## Etapa 7 — Tests del modelo

### Descripción

Casos preparados para validar el comportamiento del modelo recién entrenado antes de llevarlo a producción. Énfasis en enfermedades huérfanas.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **pytest** | Framework de tests | Consistente con la Etapa 4. |
| **Great Expectations** | Validación de predicciones | Verifica que las probabilidades de salida estén en [0,1], sumen 1, y que el recall en el conjunto de test fijo supere los umbrales definidos. |
| **GitHub Actions** | Ejecución automática en CI | Se ejecuta después de la Etapa 6; si falla, el artefacto no pasa a la Etapa 8. |

### Tests clave

- **Recall mínimo por clase:** para cada clase de enfermedad, recall ≥ 0.75 (comunes) y ≥ 0.85 (huérfanas). Si no se cumple, el pipeline se detiene y se alerta al equipo.
- **Robustez ante síntomas faltantes:** se prueba el modelo con registros donde algunos campos de síntomas son `NaN`. El modelo debe retornar una predicción válida (no error) gracias a la imputation en el preprocesador.
- **Robustez ante valores ruidosos:** se prueba con `duration_days` con valores extremos (0, 365) y severidades en el límite.
- **Coherencia de probabilidades:** la suma de probabilidades por registro debe ser 1.0 ± 1e-6.
- **Test de regresión:** se compara el recall en el conjunto de test fijo contra el modelo actualmente en producción. El nuevo modelo debe tener recall ≥ al anterior en la mayoría de clases.

### Suposiciones

- Existe un **conjunto de test fijo y etiquetado** que no se usa en entrenamiento ni aumentación. Este conjunto se construye manualmente con casos clínicamente validados y permanece constante a lo largo de todas las versiones del modelo, permitiendo comparación directa entre versiones.
- El conjunto de test fijo incluye al menos 10 registros por cada clase de enfermedad huérfana.

---

## Etapa 8 — Tests de integración

### Descripción

Validación del flujo completo por los dos puntos de entrada: ingesta del batch con formatos inválidos o registros sin validar, y casos borde en el API REST de predicción.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **pytest + httpx** | Tests de la API REST | `httpx` permite hacer peticiones HTTP síncronas y asíncronas al endpoint `/predict` en un entorno de test (usando el cliente de test de FastAPI). |
| **Postman / Newman** | Tests de API end-to-end (opcional) | Colección de Postman exportable que puede correrse en CI con Newman. Útil para documentar los contratos de la API. |
| **pytest** + Docker Compose | Tests del flujo batch | Se levanta un entorno Docker Compose con base de datos de test y se simula el DAG de Airflow con datos de prueba. |
| **locust** | Pruebas de carga | Simula múltiples médicos haciendo predicciones simultáneas para verificar que el tiempo de respuesta ≤ 500ms bajo carga de 50 usuarios concurrentes. |
| **GitHub Actions** | Ejecución automática en CI | Corre después de la Etapa 7. Si falla, el pipeline se detiene. |

### Tests clave

- **Batch con formato inválido:** enviar registros con `severity = "extreme"` (valor no válido). El sistema debe rechazarlos con error descriptivo y no almacenarlos.
- **Batch con registros sin validar:** enviar registros con `diagnosis_confirmed = False`. Deben ser filtrados y no procesados.
- **API REST — caso normal:** POST con síntomas válidos → respuesta 200 con probabilidades por clase.
- **API REST — campos faltantes:** POST sin `duration_days` → el sistema imputa y responde sin error 500.
- **API REST — tiempo de respuesta:** bajo 50 usuarios concurrentes (locust), el percentil 95 de latencia debe ser ≤ 500ms.
- **Coherencia del pipeline completo:** un registro ingresado por batch aparece correctamente en el Feature Store después del pipeline de Etapa 5.

### Suposiciones

- El entorno de integración usa una base de datos PostgreSQL separada de producción (instancia de test).
- Los tests de integración toman hasta 10 minutos en CI; se aceptan tiempos más largos que los unitarios por la naturaleza del entorno.

---

## Etapa 9 — Despliegue canary

### Descripción

El modelo aprobado en las etapas de test se despliega mediante una estrategia canary: se expone a un porcentaje reducido del tráfico primero, y si las métricas son satisfactorias, se escala al 100%.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **Docker** | Empaquetado del modelo | La API FastAPI + modelo serializado se empaqueta en una imagen Docker reproducible y portable. Funciona igual en local y en cloud. |
| **FastAPI** | API de inferencia | Framework Python de alto rendimiento para APIs asíncronas. Genera documentación OpenAPI automática. Soporta validación de request/response con Pydantic. |
| **Kubernetes + NGINX Ingress / Istio** (cloud) | Canary deployment | Istio permite dividir el tráfico por porcentaje (e.g., 10% al nuevo modelo, 90% al modelo actual) a nivel de service mesh, sin cambiar código. NGINX Ingress es alternativa más simple. |
| **Docker Compose con scripts** (local) | Canary simplificado | En local, se levantan dos contenedores (modelo actual y nuevo) en puertos diferentes; un script redirige manualmente el tráfico de prueba al nuevo y valida las métricas antes de hacer el switch. |
| **GitHub Actions** | Automatización del despliegue | El workflow de CD construye la imagen Docker, la sube al registry y aplica el manifiesto de Kubernetes (cloud) o actualiza el `docker-compose.yml` (local). |

### Flujo canary

1. Se despliega el nuevo modelo con el 10% del tráfico (cloud) o en modo prueba (local).
2. Durante 24 horas se monitorea el recall en producción del nuevo modelo vs. el actual.
3. **Si mejora o iguala:** se escala gradualmente al 100% y se archiva el modelo anterior en el registry.
4. **Si degrada:** se ejecuta rollback automático. El 100% del tráfico regresa al modelo anterior. Se genera una alerta al equipo con las métricas que fallaron.

### Suposiciones

- **El rollback es automático:** no requiere intervención humana. El sistema detecta la degradación comparando el recall del canary contra el modelo actual en producción.
- **El médico no nota el canary:** desde el frontend, ambos modelos exponen el mismo endpoint `/predict`. El enrutamiento es transparente.
- **Período de observación:** 24 horas es suficiente para acumular suficientes predicciones validadas en el contexto de una clínica (estimado: 20-50 consultas/día).

---

## Etapa 10 — Monitoreo de métricas

### Descripción

Se monitorea el recall por clase en producción de forma continua. El ciclo de validación clínica es la fuente de la métrica real: la predicción del modelo se contrasta con el diagnóstico final del médico tras el seguimiento del paciente.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **Prometheus** | Recolección de métricas | Se expone un endpoint `/metrics` en la API FastAPI (con `prometheus-fastapi-instrumentator`). Prometheus scrape cada 30 segundos métricas de latencia, throughput y predicciones por clase. |
| **Grafana** | Visualización de métricas | Dashboards en tiempo real con alertas configurables. Dashboard principal: recall por clase de enfermedad, con línea de umbral mínimo visible. |
| **MLflow** | Registro de métricas del modelo en producción | Cuando un registro validado llega (batch diario), se calcula el recall acumulado y se registra en MLflow como métrica de producción asociada a la versión del modelo activa. |
| **Airflow** | Cálculo periódico del recall real | Un DAG diario compara las predicciones del día anterior con los diagnósticos confirmados disponibles y actualiza las métricas de producción. |
| **PagerDuty / Slack Webhook** (opcional) | Alertas | Si Grafana detecta que el recall de alguna clase cae por debajo del umbral, dispara una alerta al equipo vía Slack o PagerDuty. |

### Ciclo de validación

```
Modelo emite predicción
    ↓
Médico contrasta con su diagnóstico previo
    ↓
Médico realiza seguimiento del paciente (horas/días)
    ↓
Médico confirma o corrige el diagnóstico → diagnosis_confirmed = True
    ↓
Registro ingresa al batch diario (Etapa 1)
    ↓
DAG de monitoreo calcula recall real acumulado
    ↓
Si recall < umbral → alerta → Trigger de reentrenamiento
```

### Suposiciones

- **El recall real tarda en calcularse:** dado que depende de la confirmación del médico tras el seguimiento clínico, puede haber un rezago de días entre la predicción y la validación. Se usa una ventana deslizante de 30 días para calcular el recall en producción.
- **Umbral dinámico:** en las primeras semanas de producción, el recall puede ser más volátil por el bajo volumen. Se aplica un período de "burn-in" de 2 semanas sin disparar el Trigger.

---

## Trigger de reentrenamiento ↻

### Descripción

Al detectar degradación del recall en producción, el Trigger reinicia el pipeline desde la **Etapa 5**, procesando los registros validados acumulados en la fuente centralizada desde el último entrenamiento.

### Tecnologías

| Tecnología | Rol | Justificación |
|---|---|---|
| **Airflow** | Activación del pipeline de reentrenamiento | El DAG de monitoreo evalúa el recall; si cae bajo el umbral, activa el DAG de reentrenamiento (Etapas 5 → 6 → 7 → 8 → 9) mediante `TriggerDagRunOperator`. |
| **GitHub Actions** (alternativa) | Webhook de reentrenamiento | Se puede disparar el pipeline de reentrenamiento vía un workflow de GitHub Actions activado por un webhook desde Grafana/Prometheus. |

### Condición de activación

- Recall de **cualquier clase de enfermedad** cae por debajo del umbral definido (0.75 comunes / 0.85 huérfanas) durante más de **3 días consecutivos** (para evitar disparos por ruido estadístico).
- O bien, han transcurrido **90 días** desde el último reentrenamiento (reentrenamiento periódico preventivo).

---

## Resumen de ciclos

| Ciclo | Etapas involucradas | Condición de activación | Tecnología que lo controla |
|---|---|---|---|
| Re-evaluar aumentación | Etapa 2 → Etapa 2 | Menos de 30 registros por clase huérfana | Lógica condicional en DAG Airflow |
| Iterar modelos | Etapa 3 → Feature Store → Etapa 3 | Recall < umbrales definidos en experimentos | MLflow + revisión manual del equipo |
| Reentrenamiento | Monitoreo → Trigger → Etapa 5 | Degradación del recall en producción | Airflow `TriggerDagRunOperator` |
| Rollback canary | Etapa 9 (ciclo interno) | Recall canary peor que modelo actual en 24h | Script automatizado en GitHub Actions / Kubernetes |

---

## Stack tecnológico completo

| Categoría | Tecnología | Capa |
|---|---|---|
| Orquestación | Apache Airflow | Datos + CI/CD |
| Transformaciones SQL | dbt | Datos |
| Feature Store | Feast | Datos + Inferencia |
| Versionado de datos | DVC | Datos |
| Validación de datos | Great Expectations | Datos |
| Manipulación tabular | Pandas | Datos + DS |
| ML clásico | scikit-learn, XGBoost | DS + Modelo |
| Deep Learning | PyTorch | DS + Modelo |
| Aumentación | imbalanced-learn (SMOTE) | Datos |
| Optimización hiperparámetros | Optuna | DS |
| Tracking de experimentos | MLflow | DS + Modelo |
| Model Registry | MLflow Model Registry | Modelo |
| Serialización | joblib, ONNX | Modelo |
| API de inferencia | FastAPI | Producción |
| Empaquetado | Docker | Producción |
| Orquestación cloud | Kubernetes (EKS) | Producción |
| Canary (cloud) | Istio / NGINX Ingress | Producción |
| Base de datos | PostgreSQL | Datos + Producción |
| Almacenamiento cloud | AWS S3 | Cloud |
| Tests | pytest, httpx, locust | QA |
| CI/CD | GitHub Actions | QA + Producción |
| Monitoreo | Prometheus + Grafana | Producción |
| Alertas | Slack Webhook / PagerDuty | Producción |
| Frontend médico | React + Axios | UX |
| Control de versiones | Git + GitHub | Todo |

---

## CHANGELOG v1 → v2

### Resumen ejecutivo de cambios

La v1 era una propuesta conceptual con etapas bien definidas pero sin tecnologías específicas ni decisiones de implementación justificadas. La v2 especifica tecnologías concretas en cada etapa, agrega la restricción local/cloud, formaliza los ciclos iterativos y documenta todas las suposiciones.

---

### Cambios por etapa

| # | Etapa | Cambio en v2 | Justificación del cambio |
|---|---|---|---|
| — | Arquitectura global | **Nuevo:** arquitectura bifurcada local/cloud con Docker Compose (local) y AWS EKS (cloud) | La restricción explícita del enunciado de que el médico puede correr en local requería definir dos modos de despliegue |
| 1 | Centralización | Tecnología especificada: **Airflow + PostgreSQL + SHA-256** para anonimización | v1 no especificaba el orquestador ni el mecanismo de anonimización |
| 2 | Limpieza y aumentación | **Nuevo:** `Great Expectations` para validación de calidad. **Especificado:** `OrdinalEncoder` para severidad, justificación del orden semántico. **Nuevo:** umbral de 30 registros por clase para activar aumentación | v1 mencionaba SMOTE y GANs pero sin criterios de cuándo usarlos ni tecnología de validación |
| 2 | Feature Store | **Especificado:** Feast con Redis (online) + PostgreSQL (offline). **Nuevo:** justificación del contrato Feature Store para evitar training-serving skew | v1 mencionaba "Feature Store" sin tecnología ni rol específico |
| 3 | Experimentos DS | **Especificado:** MLflow para tracking, Optuna para hiperparámetros. **Nuevo:** umbrales de recall cuantificados (0.75 / 0.85). **Nuevo:** justificación de no usar AutoML | v1 mencionaba Git y modelos pero sin tracking ni umbrales numéricos |
| 4 | Tests unitarios | **Especificado:** pytest + pytest-cov + GitHub Actions CI. **Nuevo:** lista de tests concretos y umbral de cobertura del 80% | v1 listaba qué se testea pero no la tecnología ni los criterios de aprobación |
| 5 | Automatización | **Especificado:** dbt para transformaciones. **Nuevo:** arquitectura Medallion detallada (Bronze/Silver/Gold con contenido de cada capa). **Nuevo:** clarificación de cuándo se activa (solo con Trigger, no en cada batch) | v1 mencionaba "análogo a Medallion" sin detallar las capas ni cuándo se activa |
| 6 | Generación de artefactos | **Especificado:** MLflow Model Registry con estados (Staging/Production/Archived). **Nuevo:** el artefacto incluye el preprocesador en un Pipeline de scikit-learn. **Especificado:** joblib/ONNX para serialización | v1 mencionaba "Model Registry" y "artefacto versionado" sin tecnología ni detalles |
| 7 | Tests del modelo | **Nuevo:** test de regresión contra modelo en producción. **Nuevo:** conjunto de test fijo con al menos 10 registros por clase huérfana. **Especificado:** Great Expectations para validación de predicciones | v1 mencionaba pruebas exhaustivas pero sin tecnología ni criterios numéricos |
| 8 | Tests de integración | **Especificado:** httpx para tests de API, locust para pruebas de carga. **Nuevo:** criterio de latencia (p95 ≤ 500ms bajo 50 usuarios concurrentes) | v1 mencionaba "casos borde y tiempo de respuesta" sin umbrales ni tecnología |
| 9 | Despliegue canary | **Especificado:** Docker + FastAPI + Kubernetes/Istio (cloud) y Docker Compose + scripts (local). **Nuevo:** período de observación de 24h. **Nuevo:** escalado gradual (10% → 100%) | v1 mencionaba "API REST dockerizado" y "rollback automático" sin detallar la mecánica ni las tecnologías de canary |
| 10 | Monitoreo | **Especificado:** Prometheus + Grafana + `prometheus-fastapi-instrumentator`. **Nuevo:** ventana deslizante de 30 días para el recall. **Nuevo:** período de burn-in de 2 semanas | v1 describía el ciclo de monitoreo correctamente pero sin tecnologías ni parámetros temporales |
| — | Trigger | **Nuevo:** condición de 3 días consecutivos bajo umbral para evitar falsos positivos. **Nuevo:** reentrenamiento periódico preventivo cada 90 días. **Especificado:** `TriggerDagRunOperator` de Airflow | v1 mencionaba el Trigger pero sin condición de activación precisa ni tecnología |

### Lo que se mantuvo de v1

- La lógica general del flujo (10 etapas en el mismo orden)
- La distinción entre batch diario y API REST como puntos de entrada
- El criterio de recall por clase como métrica principal, con énfasis en huérfanas
- La naturaleza iterativa de las Etapas 2 y 3
- El concepto de canary deployment con rollback automático
- El Feature Store como contrato entre etapas
- La estrategia de aumentación con SMOTE como primera opción y GANs como avanzada
- La validación médica como única fuente de verdad para el recall real en producción
