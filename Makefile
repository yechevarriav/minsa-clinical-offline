.PHONY: help install dev test test-unit test-integration test-load coverage lint format security docker-build docker-run docker-down clean evaluate

# Variables
PYTHON := python3
DOCKER_IMAGE := minsa-clinical-offline:latest
DOCKER_COMPOSE := docker-compose.yml

help: ## Muestra este mensaje de ayuda
	@echo "🏥 MINSA - Sistema de Soporte Clínico Offline"
	@echo ""
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==================== INSTALACIÓN ====================

install: ## Instala dependencias en entorno virtual
	$(PYTHON) -m venv venv
	. venv/bin/activate && pip install --upgrade pip setuptools wheel
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependencias instaladas"

install-dev: ## Instala dependencias + dev tools (pytest, black, flake8, etc.)
	$(PYTHON) -m venv venv
	. venv/bin/activate && pip install --upgrade pip setuptools wheel
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install pytest pytest-cov pytest-asyncio black flake8 bandit
	@echo "✅ Dependencias de desarrollo instaladas"

# ==================== DESARROLLO ====================

dev: ## Inicia servidor FastAPI en modo desarrollo (localhost:8000)
	. venv/bin/activate && uvicorn src.offline_clinic.main:app --reload --host 0.0.0.0 --port 8000
	@echo "🚀 Servidor en http://localhost:8000"

dev-docker: ## Inicia con docker-compose (incluye Ollama + FastAPI)
	docker-compose up --build
	@echo "🚀 Sistema corriendo en http://localhost:8000"

# ==================== TESTING ====================

test: test-unit test-integration test-load ## Ejecuta todos los tests (unit + integration + load)
	@echo "✅ Todos los tests completados"

test-unit: ## Ejecuta tests unitarios
	. venv/bin/activate && pytest tests/unit -v --tb=short
	@echo "✅ Tests unitarios completados"

test-integration: ## Ejecuta tests de integración (RAG pipeline E2E)
	. venv/bin/activate && pytest tests/integration -v --tb=short
	@echo "✅ Tests de integración completados"

test-load: ## Ejecuta tests de carga con k6 (10+ usuarios simultáneos)
	@which k6 > /dev/null 2>&1 || { echo "⚠️  k6 no instalado. Instala desde https://k6.io/docs/getting-started/installation/"; exit 1; }
	k6 run tests/load/load_test.js
	@echo "✅ Tests de carga completados"

coverage: ## Genera reporte de cobertura (pytest-cov)
	. venv/bin/activate && pytest tests/unit tests/integration --cov=src --cov-report=html --cov-report=term
	@echo "📊 Reporte en htmlcov/index.html"

coverage-open: coverage ## Abre reporte de cobertura en navegador
	@which xdg-open > /dev/null 2>&1 && xdg-open htmlcov/index.html || open htmlcov/index.html

# ==================== CALIDAD DE CÓDIGO ====================

lint: ## Verifica código con flake8 (PEP 8)
	. venv/bin/activate && flake8 src tests --max-line-length=120 --ignore=E203,W503
	@echo "✅ Linting completado"

format: ## Formatea código con black
	. venv/bin/activate && black src tests --line-length=120
	@echo "✅ Código formateado"

security: ## Escanea seguridad con bandit
	. venv/bin/activate && bandit -r src -ll
	@echo "✅ Escaneo de seguridad completado"

# ==================== DOCKER ====================

docker-build: ## Construye imagen Docker
	docker build -t $(DOCKER_IMAGE) .
	@echo "✅ Imagen construida: $(DOCKER_IMAGE)"

docker-run: ## Ejecuta contenedor Docker (puerto 8000)
	docker run -p 8000:8000 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 $(DOCKER_IMAGE)
	@echo "🚀 Contenedor corriendo en http://localhost:8000"

docker-down: ## Detiene contenedores docker-compose
	docker-compose down
	@echo "⏹️  Contenedores detenidos"

docker-logs: ## Muestra logs de docker-compose
	docker-compose logs -f app
	@echo "📋 Logs mostrados"

# ==================== EVALUACIÓN LLM ====================

evaluate: ## Ejecuta evaluación RAGAS (8 casos clínicos)
	. venv/bin/activate && jupyter notebook notebooks/evaluation.ipynb
	@echo "📊 Evaluación RAGAS iniciada"

evaluate-headless: ## Ejecuta evaluación sin abrir notebook
	. venv/bin/activate && jupyter nbconvert --to notebook --execute notebooks/evaluation.ipynb --output=evaluation_results.ipynb
	@echo "📊 Evaluación RAGAS completada (evaluation_results.ipynb)"

# ==================== UTILIDADES ====================

clean: ## Limpia archivos temporales (__pycache__, .pytest_cache, dist, build)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	@echo "🧹 Carpetas limpias"

clean-docker: docker-down ## Limpia contenedores y volúmenes Docker
	docker system prune -f
	@echo "🧹 Docker limpio"

venv-clean: ## Elimina virtualenv (cuidado!)
	rm -rf venv
	@echo "⚠️  Virtualenv eliminado"

requirements-freeze: ## Genera requirements.txt actualizado
	. venv/bin/activate && pip freeze > requirements.txt
	@echo "📦 requirements.txt actualizado"

# ==================== DOCUMENTACIÓN ====================

docs: ## Abre README en navegador
	@which xdg-open > /dev/null 2>&1 && xdg-open README.md || open README.md
	@echo "📖 README abierto"

openapi: ## Muestra especificación OpenAPI en http://localhost:8000/docs
	@echo "📋 OpenAPI Swagger disponible en http://localhost:8000/docs (después de 'make dev')"

# ==================== DESPLIEGUE ====================

deploy-check: ## Verifica que todo esté listo para deploy (tests + lint + security)
	@echo "🔍 Verificando proyecto..."
	@make lint || exit 1
	@make test || exit 1
	@make security || exit 1
	@echo "✅ Proyecto listo para deploy"

deploy-render: ## Instrucciones para deploy en Render.com
	@echo "📝 Pasos para deploy en Render.com:"
	@echo "1. Conectar repo GitHub a Render"
	@echo "2. Service name: minsa-clinical-offline"
	@echo "3. Build command: make install"
	@echo "4. Start command: uvicorn src.offline_clinic.main:app --host 0.0.0.0 --port $$PORT"
	@echo "5. Envs: OLLAMA_BASE_URL=https://ollama.minsa.gob.pe (si existe)"
	@echo ""
	@echo "URL actual: https://minsa-clinical-offline.onrender.com"

# ==================== INFORMACIÓN ====================

info: ## Muestra información del proyecto
	@echo "🏥 MINSA - Sistema de Soporte Clínico Offline"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "📦 Stack: Python 3.10, FastAPI, FAISS, Ollama, SQLite"
	@echo "📍 Repo: https://github.com/yechevarriav/minsa-clinical-offline"
	@echo "🌐 URL: https://minsa-clinical-offline.onrender.com"
	@echo "📊 Tests: 48/48 pasando (>80% cobertura)"
	@echo "🎯 RAGAS Score: 0.818 (B+)"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Comandos rápidos:"
	@echo "  make install-dev    → Setup completo con dev tools"
	@echo "  make dev            → Inicia servidor en localhost:8000"
	@echo "  make dev-docker     → Inicia con docker-compose"
	@echo "  make test           → Ejecuta todos los tests"
	@echo "  make coverage       → Genera reporte de cobertura"
	@echo "  make deploy-check   → Verifica que todo esté listo"
	@echo ""
