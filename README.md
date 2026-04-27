# minsa-clinical-offline

**Sistema de Soporte Clínico Offline: Diagnósticos CIE-10 para Clínicas Rurales MINSA Perú**
RAG offline-first con Llama-2 7B + FAISS — funciona sin internet

[![CI Tests](https://github.com/yechevarriav/minsa-clinical-offline/actions/workflows/tests.yml/badge.svg)](https://github.com/yechevarriav/minsa-clinical-offline/actions)
[![Deploy](https://img.shields.io/badge/deploy-render.com-46E3B7)](https://minsa-clinical-offline.onrender.com)
[![Python](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> 🌐 **Demo en producción:** [minsa-clinical-offline.onrender.com](https://minsa-clinical-offline.onrender.com)

---

## Stack Tecnológico

| Componente    | Tecnología                 | Versión                     |
| ------------- | -------------------------- | --------------------------- |
| Backend       | Python + FastAPI           | 3.10 / 0.104.1              |
| LLM Local     | Llama-2 7B (4-bit, Ollama) | llama2:7b-q4                |
| Embeddings    | multilingual-MiniLM-L6-v2  | sentence-transformers 2.2.2 |
| Vector Store  | FAISS IVF+PQ               | 1.7.4                       |
| Orquestación  | LangChain                  | 0.0.352                     |
| Base de Datos | SQLite (FeedbackDB)        | —                           |
| Contenedores  | Docker + Docker Compose    | python:3.10-slim            |
| CI/CD         | GitHub Actions             | —                           |
| Deploy Cloud  | Render.com Standard        | $25/mes                     |

---

## Resultados Reales

### Métricas LLM (RAGAS) — 8 casos clínicos

| Métrica                | Score          | Umbral        |
| ---------------------- | -------------- | ------------- |
| Faithfulness           | 0.847          | ≥ 0.80 ✅     |
| Context Relevancy      | 0.835          | ≥ 0.80 ✅     |
| Answer Relevancy       | 0.823          | ≥ 0.80 ✅     |
| Context Recall         | 0.812          | ≥ 0.80 ✅     |
| Answer Correctness     | 0.798          | ≥ 0.70 ✅     |
| Context Precision      | 0.791          | ≥ 0.70 ✅     |
| **RAGAS Score Global** | **0.818 (B+)** | **≥ 0.80 ✅** |

### Latencia

| Endpoint                       | Latencia avg | p95    | KPI        |
| ------------------------------ | ------------ | ------ | ---------- |
| `GET /health`                  | < 10ms       | < 10ms | < 100ms ✅ |
| `POST /api/v1/query`           | 870ms        | 1.24s  | < 3s ✅    |
| `POST /api/v1/query` (con LLM) | 3-5s         | 5s     | < 10s ✅   |

### Prueba de Carga

| Métrica               | Resultado | KPI         |
| --------------------- | --------- | ----------- |
| Usuarios concurrentes | 10–20     | ≥ 10 ✅     |
| Queries en 60s        | 697       | —           |
| Throughput            | 11.5 q/s  | ≥ 10 q/s ✅ |
| Success rate          | 100%      | ≥ 95% ✅    |

### Costos

| Concepto                                | Costo       |
| --------------------------------------- | ----------- |
| LLM (Llama-2 7B local, Ollama)          | $0/mes      |
| Embeddings (sentence-transformers, CPU) | $0/mes      |
| Render.com Standard (2GB RAM)           | $25/mes     |
| **Total mensual**                       | **$25/mes** |
| Alternativa satelital (sin IA)          | $500+/mes   |
| **Ahorro**                              | **95%**     |

---

## Instalación

### Prerrequisitos

```
- Python 3.10+
- Git
- Docker + Docker Compose (modo Docker/cloud)
- Ollama (solo modo local con LLM)
- 8 GB RAM mínimo (modo local con Llama-2)
- 2 GB RAM mínimo (modo cloud sin LLM)
```

### Paso 0 — Clonar el repositorio (todos los modos)

```bash
git clone https://github.com/yechevarriav/minsa-clinical-offline.git
cd minsa-clinical-offline
cp .env.example .env
```

---

## 🖥️ Modo A — Local sin Docker (desarrollo + LLM completo)

**Requiere:** Python 3.10, Ollama, 8GB RAM

#### 1. Crear entorno virtual e instalar dependencias

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### 2. Instalar y configurar Ollama

```bash
# Descargar Ollama desde: https://ollama.com/download
# Luego descargar el modelo Llama-2 7B (4-bit, ~3.6GB):
ollama pull llama2:7b-q4_K_M
ollama serve   # Inicia en http://localhost:11434
```

#### 3. Iniciar FastAPI

```bash
cd src
uvicorn offline_clinic.main:app --host 0.0.0.0 --port 8000
```

#### 4. Primera ejecución — construcción de embeddings

> ⚠️ La primera vez, el sistema indexa los 14,702 códigos CIE-10 en FAISS.
> **Puede tardar 3-5 minutos en CPU.**
> El índice se guarda en `src/offline_clinic/data/faiss_index.bin`.
> Las siguientes ejecuciones cargan el índice ya construido (~5 segundos).

Verás en los logs:

```
🔄 Cargando modelos en background...
✅ CatalogManager: 14702 códigos CIE-10
✅ SemanticEngine cargado
✅ HybridSearchV4 cargado
🏥 Sistema MINSA Clinical listo!
```

#### 5. Verificar

```bash
curl http://localhost:8000/health
# {"models_ready": true, "version": "2.0.0"}
```

#### 6. Primera consulta (con LLM)

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "fiebre alta", "edad": 45, "sexo": "M", "top_k": 5, "use_llm": true}'
```

---

## 🐳 Modo B — Docker Compose (local con contenedores)

**Requiere:** Docker Desktop, 8GB RAM

#### 1. Construir e iniciar

```bash
docker-compose up --build
# FastAPI disponible en: http://localhost:8000
# Ollama disponible en:  http://localhost:11434
```

#### 2. Descargar modelo Llama-2 (primera vez)

```bash
docker-compose exec ollama ollama pull llama2:7b-q4_K_M
```

#### 3. Verificar

```bash
curl http://localhost:8000/health
# {"models_ready": true}
```

> ⚠️ Primera ejecución: FAISS se construye en background (3-5 min).
> El frontend en http://localhost:8000 muestra "⏳ Cargando modelos..." hasta que termina.

---

## ☁️ Modo C — Render.com (cloud, sin LLM)

**Requiere:** Cuenta en Render.com (gratuita o Standard $25/mes)

#### 1. Conectar repositorio

```
1. Ir a https://render.com → New → Web Service
2. Conectar GitHub → seleccionar yechevarriav/minsa-clinical-offline
3. Configurar:
   - Name:          minsa-clinical-offline
   - Runtime:       Docker
   - Branch:        main
   - Plan:          Standard ($25/mes) — necesita 2GB RAM
```

#### 2. Variables de entorno en Render

```
PYTHONPATH    = /app/src
ENVIRONMENT   = cloud
LOG_LEVEL     = INFO
```

#### 3. Health Check en Render

```
Path:               /health
Interval:           30s
Timeout:            10s
```

#### 4. Deploy automático

Render hace deploy automático en cada `git push origin main`.

#### 5. Verificar URL pública

```bash
curl https://minsa-clinical-offline.onrender.com/health
# {"models_ready": true, "version": "2.0.0"}
```

> ⚠️ **Limitación cloud:** Llama-2 7B requiere 8GB RAM.
> Render Standard tiene 2GB — el LLM no está disponible en cloud.
> La búsqueda CIE-10 (FAISS + NER) funciona completamente.

---

## 🏗️ Modo D — AWS ECS (producción enterprise)

**Requiere:** Cuenta AWS activa, AWS CLI configurado

#### 1. Configurar AWS CLI

```bash
aws configure
# AWS Access Key ID: [tu key]
# AWS Secret Access Key: [tu secret]
# Default region: us-east-1
```

#### 2. Crear repositorio ECR y subir imagen

```bash
# Crear repositorio ECR
aws ecr create-repository --repository-name minsa-clinical-offline

# Login a ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS \
  --password-stdin [cuenta].dkr.ecr.us-east-1.amazonaws.com

# Build y push
docker build -t minsa-clinical-offline .
docker tag minsa-clinical-offline:latest \
  [cuenta].dkr.ecr.us-east-1.amazonaws.com/minsa-clinical-offline:latest
docker push \
  [cuenta].dkr.ecr.us-east-1.amazonaws.com/minsa-clinical-offline:latest
```

#### 3. Crear cluster ECS y servicio

```bash
# Crear cluster
aws ecs create-cluster --cluster-name minsa-clinical-prod

# Registrar task definition (2GB RAM, 1 vCPU)
aws ecs register-task-definition \
  --family minsa-clinical \
  --requires-compatibilities FARGATE \
  --network-mode awsvpc \
  --cpu 1024 --memory 2048 \
  --container-definitions '[{
    "name": "minsa-clinical",
    "image": "[cuenta].dkr.ecr.us-east-1.amazonaws.com/minsa-clinical-offline:latest",
    "portMappings": [{"containerPort": 8000}],
    "environment": [
      {"name": "PYTHONPATH", "value": "/app/src"},
      {"name": "ENVIRONMENT", "value": "aws"}
    ]
  }]'

# Crear servicio
aws ecs create-service \
  --cluster minsa-clinical-prod \
  --service-name minsa-clinical-svc \
  --task-definition minsa-clinical \
  --desired-count 2 \
  --launch-type FARGATE
```

#### 4. Configurar Application Load Balancer

```bash
# Crear ALB
aws elbv2 create-load-balancer \
  --name minsa-clinical-alb \
  --type application

# Health check path: /health
# Puerto: 8000
```

> ⚠️ **Misma limitación:** Llama-2 requiere instancia con mínimo 8GB RAM.
> Usar AWS ECS con task de 8GB RAM o instancia EC2 con GPU para LLM completo.

---

## ✅ Verificación final (todos los modos)

```bash
# 1. Health check
curl [URL]/health
# {"models_ready": true}

# 2. Consulta de prueba
curl -X POST [URL]/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"question": "dolor de cabeza", "edad": 40, "sexo": "M", "top_k": 5}'

# 3. Swagger UI
# Abrir en navegador: [URL]/docs

# 4. Evaluación RAGAS en vivo (apunta a Render)
python evaluate_ragas_live.py
```

---

## Endpoints Principales

| Endpoint           | Método | Descripción                                         |
| ------------------ | ------ | --------------------------------------------------- |
| `/health`          | GET    | Health check — `models_ready: true/false`           |
| `/api/v1/query`    | POST   | Búsqueda CIE-10 por síntomas + contexto demográfico |
| `/api/v1/feedback` | POST   | Registra código seleccionado por el médico          |
| `/docs`            | GET    | Swagger UI (OpenAPI 3.0)                            |

---

## Documentación API

Con el servidor corriendo: [http://localhost:8000/docs](http://localhost:8000/docs)

Especificación completa: [`docs/api/openapi.yaml`](docs/api/openapi.yaml)

---

## Tests

```bash
make test              # Suite completa (48 tests)
make test-unit         # 27 tests unitarios
make test-integration  # 18 tests de integración
make test-load         # 3 tests de carga (10–20 usuarios)
make coverage          # Reporte de cobertura (82%)
```

---

## Evaluación LLM

```bash
# Calcular métricas RAGAS en vivo contra la URL de producción
python evaluate_ragas_live.py

# O abrir el notebook interactivo
make evaluate
```

Resultados guardados en `reports/ragas_report.json`.

---

## Comandos (Makefile)

```bash
make help            # Lista todos los comandos
make install         # Instala dependencias
make dev             # Inicia servidor en localhost:8000
make dev-docker      # Inicia con docker-compose
make test            # Suite completa de tests
make coverage        # Cobertura (objetivo: ≥ 80%)
make lint            # flake8 PEP 8
make format          # black
make security        # bandit (0 high/critical)
make evaluate        # Evaluación RAGAS (notebook)
make deploy-check    # lint + test + security antes de push
make info            # Información del proyecto
```

---

## Arquitectura

El sistema implementa un pipeline RAG offline-first en 8 pasos:

```
Médico ingresa síntomas + edad + sexo
        ↓
FastAPI — construye query enriquecida
        ↓
NER Extractor — identifica entidades médicas (13 categorías)
        ↓
SemanticEngine — genera embedding 768d (roberta-base-biomedical-clinical-es)
        ↓
FAISS Index — búsqueda similitud en 14,702 vectores CIE-10
        ↓
FastAPI — retorna JSON (código + descripción + score)
        ↓
Frontend HTML — muestra resultados, médico selecciona
        ↓
FeedbackDB (SQLite) — registra selección para aprendizaje
```

**Modo offline** (clínica rural): FastAPI + FAISS + Llama-2 local via Ollama.
**Modo cloud** (demo): FastAPI + FAISS en Render.com, sin LLM (RAM limitada).

Diagrama C4: [`docs/architecture/`](docs/architecture/)
Flujo de datos: [`docs/flujo-datos.md`](docs/flujo-datos.md)

---

## Estructura del Repositorio

```
minsa-clinical-offline/
├── .github/workflows/       # CI/CD GitHub Actions (🟢 verde)
├── src/offline_clinic/
│   ├── main.py              # FastAPI entry point
│   ├── static/index.html    # Frontend HTML clínico
│   └── core/
│       ├── hybrid_search_v4.py        # NER + FAISS + feedback
│       ├── semantic_search_medical.py # Embeddings 768d
│       ├── ner_extractor.py           # 13 categorías médicas
│       ├── feedback_db.py             # SQLite aprendizaje
│       └── rag_engine.py              # Llama-2 via Ollama
├── data/
│   ├── CIE10_MINSA_OFICIAL.xlsx       # 14,702 códigos CIE-10
│   └── Procedimientos.xlsx            # 12,141 procedimientos
├── tests/
│   ├── unit/                # 27 tests
│   ├── integration/         # 18 tests
│   └── load/                # 3 tests (k6-compatible)
├── docs/
│   ├── adr/                 # 3 Architecture Decision Records
│   ├── api/openapi.yaml     # Especificación OpenAPI 3.0
│   └── flujo-datos.md       # Diagrama Mermaid del pipeline
├── notebooks/
│   └── evaluation.ipynb     # Evaluación RAGAS
├── reports/
│   ├── ragas_report.json    # Score 0.818 (B+)
│   ├── test_coverage.xml    # Cobertura 82%
│   └── load_test_results.html
├── evaluate_ragas_live.py   # Script evaluación en vivo
├── Makefile                 # 20+ comandos documentados
├── Dockerfile               # python:3.10-slim
└── docker-compose.yml       # FastAPI + Ollama
```

---

## Requisitos

- Python 3.10+
- Docker y Docker Compose
- Ollama (para modo local con LLM)
- 8 GB RAM mínimo (modo local con Llama-2)
- 2 GB RAM mínimo (modo cloud sin LLM)

---

## 🎥 Demo

> 📹 [Ver demo en Google Drive](https://drive.google.com/file/d/1K_CCxeEarEtzx8_h2OFlFe9UiJ34tV59/view?usp=sharing)

---

## Documentación Completa

Ver [`docs/PROJECT_DOCUMENTATION.md`](docs/PROJECT_DOCUMENTATION.md) — plantilla oficial BSG completada (13 secciones).

---

## Licencia

Proyecto académico — AI-LLM Solution Architect · Cohorte 2026-A
Yvonne Patricia Echevarria Vargas
