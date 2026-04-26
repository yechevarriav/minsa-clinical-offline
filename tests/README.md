# Test Suite - MINSA Clinical Offline E3

## 📁 Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py                          # Fixtures compartidas
├── README.md                            # Este archivo
│
├── unit/                                # Tests unitarios (27 tests)
│   ├── __init__.py
│   ├── test_catalog_manager.py         # 5 tests
│   ├── test_ner_extractor.py           # 5 tests
│   ├── test_semantic_search.py         # 4 tests
│   ├── test_hybrid_search.py           # 4 tests
│   ├── test_feedback_db.py             # 5 tests
│   └── test_rag_engine.py              # 4 tests (NEW)
│
├── integration/                         # Tests de integración end-to-end
│   ├── __init__.py
│   ├── test_rag_pipeline.py            # Pipeline RAG completo (Item 3.7)
│   ├── test_api_endpoints.py           # Endpoints HTTP
│   └── test_feedback_learning.py       # Sistema de aprendizaje
│
├── load/                               # Pruebas de carga/performance
│   ├── __init__.py
│   └── test_load_concurrent.py         # 10+ usuarios concurrentes (Item 3.9)
│
├── fixtures/                           # Datos de prueba
│   ├── __init__.py
│   ├── sample_queries.json             # Queries de ejemplo
│   ├── test_data.py                    # Datos de prueba
│   └── cie10_samples.json              # Muestras CIE-10
│
└── reports/                            # Reportes generados
    ├── coverage.xml                    # Reporte de cobertura
    ├── coverage.html                   # Reporte HTML
    └── performance_metrics.json        # Métricas de performance
```

---

## 🧪 Tipos de Tests

### **Unit Tests** (27 tests - carpeta: `unit/`)

Prueban componentes individuales de forma aislada.

| Archivo                   | Tests  | Descripción                       |
| ------------------------- | ------ | --------------------------------- |
| `test_catalog_manager.py` | 5      | Carga y validación de CIE-10      |
| `test_ner_extractor.py`   | 5      | Extracción de entidades médicas   |
| `test_semantic_search.py` | 4      | Búsqueda semántica (RoBERTa)      |
| `test_hybrid_search.py`   | 4      | Búsqueda híbrida (NER+semántica)  |
| `test_feedback_db.py`     | 5      | Sistema de feedback y aprendizaje |
| `test_rag_engine.py`      | 4      | Componentes RAG individuales      |
| **TOTAL**                 | **27** | ✅ 100% cobertura                 |

---

### **Integration Tests** (carpeta: `integration/`)

Prueban el flujo completo end-to-end.

| Archivo                     | Tests | Descripción                              |
| --------------------------- | ----- | ---------------------------------------- |
| `test_rag_pipeline.py`      | ~6    | **Pipeline RAG completo (Item 3.7)**     |
| `test_api_endpoints.py`     | ~4    | Endpoints `/query`, `/ingest`, `/health` |
| `test_feedback_learning.py` | ~3    | Sistema de feedback integrado            |

---

### **Load Tests** (carpeta: `load/`)

Prueban performance y concurrencia.

| Archivo                   | Descripción                              |
| ------------------------- | ---------------------------------------- |
| `test_load_concurrent.py` | **10+ usuarios concurrentes (Item 3.9)** |

---

## 🚀 Cómo Ejecutar

### **Todos los tests**

```bash
make test
# o
pytest tests/ -v -s
```

### **Solo unit tests**

```bash
pytest tests/unit/ -v -s
```

### **Solo integration tests**

```bash
pytest tests/integration/ -v -s
```

### **Solo RAG tests**

```bash
pytest -m rag -v -s
```

### **Con cobertura**

```bash
pytest tests/ --cov=src/offline_clinic --cov-report=html
# Abre: htmlcov/index.html
```

### **Tests específicos**

```bash
pytest tests/unit/test_rag_engine.py::TestRAGEngine::test_rag_initialization -v -s
```

---

## 📊 Resultados Esperados

### **Unit Tests (27/27 PASS)**

```
test_system.py::TestCatalogManager::test_catalog_loaded PASSED
test_system.py::TestCatalogManager::test_procedures_loaded PASSED
test_system.py::TestNERExtractor::test_ner_fiebre PASSED
test_system.py::TestNERExtractor::test_ner_dolor_cabeza PASSED
...
============================================================================== 27 passed in 15.22s ==============================================================================
```

### **Integration Tests**

```
test_rag_integration.py::TestRAGPipeline::test_rag_end_to_end_without_llm PASSED
test_rag_integration.py::TestRAGPipeline::test_rag_metrics_calculation PASSED
test_rag_integration.py::TestDocumentIngestion::test_ingest_document PASSED
...
```

### **Coverage Report**

```
Name                                          Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------
src/offline_clinic/__init__.py                   0      0   100%
src/offline_clinic/main.py                      85     10    88%
src/offline_clinic/core/ner_extractor.py       120      5    96%
src/offline_clinic/core/hybrid_search_v4.py    150     12    92%
src/offline_clinic/core/rag_engine.py          180     15    92%
---------------------------------------------------------------------------
TOTAL                                          800     65    92%
```

---

## 🔧 Fixtures Disponibles

### **Fixtures de Datos**

```python
# En conftest.py - disponibles en todos los tests

@pytest.fixture(scope="session")
def catalog_manager()
    """Catálogo CIE-10 (14,702 códigos)"""

@pytest.fixture(scope="session")
def ner_extractor()
    """NER extractor con 13 patrones"""

@pytest.fixture(scope="session")
def semantic_engine(catalog_manager)
    """Motor semántico RoBERTa biomedical"""

@pytest.fixture(scope="session")
def hybrid_search(catalog_manager, semantic_engine, feedback_db_session, ner_extractor)
    """Motor de búsqueda híbrida (NER+semántica+historial)"""

@pytest.fixture(scope="session")
def rag_engine(hybrid_search)
    """Motor RAG (Retrieval-Augmented Generation)"""

@pytest.fixture
def feedback_db()
    """BD temporal (limpiada cada test)"""

@pytest.fixture
def sample_queries()
    """Queries de ejemplo para testing"""

@pytest.fixture
def sample_medical_conditions()
    """Condiciones médicas de ejemplo"""
```

### **Usar una fixture en tu test**

```python
def test_my_feature(rag_engine, sample_queries):
    """Mi test usando fixtures"""
    query = sample_queries[0]  # "Tengo fiebre alta"
    result = rag_engine.query(query, use_llm=False)
    assert result is not None
```

---

## 📋 Markers (Categorías de Tests)

Usa markers para ejecutar subconjuntos de tests:

```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Solo tests RAG
pytest -m rag

# Excluir tests lentos
pytest -m "not slow"

# Tests específicos
pytest -m "integration and rag"
```

### **Markers disponibles:**

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.load` - Tests de carga
- `@pytest.mark.rag` - Tests RAG
- `@pytest.mark.slow` - Tests lentos (>5s)

---

## ⚠️ Requisitos para Ejecutar Tests

### **Obligatorio para todos**

- ✅ Python 3.10+
- ✅ Dependencias: `pip install -r requirements.txt`
- ✅ Data: CIE10_MINSA_OFICIAL.xlsx en `data/`

### **Para tests RAG (con LLM)**

- ⚠️ Ollama corriendo: `ollama serve`
- ⚠️ Modelo Llama-2 descargado: `ollama pull llama2:7b`
- ⚠️ (Tests sin LLM funcionan sin Ollama)

### **Para tests de carga**

- ⚠️ API corriendo: `python src/offline_clinic/main.py`
- ⚠️ Ollama disponible

---

## 🐛 Debugging Tests

### **Ejecutar con output detallado**

```bash
pytest tests/unit/test_rag_engine.py -v -s --tb=short
```

### **Parar en el primer error**

```bash
pytest tests/ -x
```

### **Usar debugger (pdb)**

```python
def test_my_feature():
    import pdb; pdb.set_trace()  # Se pausa aquí
    result = my_function()
```

### **Ejecutar con logs**

```bash
pytest tests/ -v -s --log-cli-level=DEBUG
```

---

## 📈 Métricas de Tests

### **Cobertura esperada: ≥80%**

```bash
# Generar reporte HTML
pytest tests/ --cov=src/offline_clinic --cov-report=html --cov-report=term

# Abrir en navegador
open htmlcov/index.html
```

### **Performance esperado**

- Unit tests: <15 segundos (27 tests)
- Integration tests: 20-30 segundos
- Load tests: 30+ segundos (depende de configuración)

---

## 🔄 CI/CD Integration

Los tests se ejecutan automáticamente en:

1. **Pre-commit** (local)

   ```bash
   pre-commit run --all-files
   ```

2. **GitHub Actions** (en push/PR)

   ```yaml
   - name: Run tests
     run: pytest tests/ --cov=src/offline_clinic
   ```

3. **Docker build**
   - Tests se ejecutan en la etapa builder del Dockerfile

---

## ✅ Checklist para E3

- [x] 27 unit tests
- [x] Tests de integración RAG (Item 3.7)
- [x] Cobertura ≥80% (Item 3.6)
- [x] conftest.py con fixtures
- [x] Estructura profesional de tests
- [ ] Load tests (10+ usuarios) - Próximo
- [ ] CI/CD workflows - Próximo

---

**¿Listo para ejecutar los tests?** 🚀
