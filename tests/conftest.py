"""
conftest.py - Configuración global de pytest y fixtures compartidas
Usado por: tests/unit/, tests/integration/, tests/load/
"""

import sys
import pytest
import logging
from pathlib import Path
import tempfile

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES: CATALOGO & DATOS
# ============================================================================

@pytest.fixture(scope="session")
def catalog_manager():
    """
    Cargar catálogo CIE-10 una sola vez para toda la sesión de tests
    Reutilizado por todos los tests
    """
    from offline_clinic.core.excel_loader_minsa import CatalogManager

    cm = CatalogManager(
        cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
        procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
    )
    logger.info(f"✓ Catalog loaded: {len(cm.get_all_cie10_codes())} CIE-10 codes")
    return cm


# ============================================================================
# FIXTURES: NER
# ============================================================================

@pytest.fixture(scope="session")
def ner_extractor():
    """
    Inicializar NER extractor una sola vez
    """
    from offline_clinic.core.ner_extractor import MedicalNERExtractor

    ner = MedicalNERExtractor()
    logger.info("✓ NER Extractor initialized")
    return ner


# ============================================================================
# FIXTURES: SEMANTIC SEARCH
# ============================================================================

@pytest.fixture(scope="session")
def semantic_engine(catalog_manager):
    """
    Inicializar motor de búsqueda semántica una sola vez
    """
    from offline_clinic.core.semantic_search_medical import MedicalSemanticSearchEngine

    engine = MedicalSemanticSearchEngine(catalog_manager)
    logger.info("✓ Semantic Search Engine initialized")
    return engine


# ============================================================================
# FIXTURES: DATABASE
# ============================================================================

@pytest.fixture(scope="function")
def feedback_db():
    """
    Crear BD temporal para cada test (función scope)
    Se limpia después de cada test
    """
    from offline_clinic.core.feedback_db import FeedbackDB

    # Usar base de datos en memoria para tests
    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = temp_db.name
    temp_db.close()

    db = FeedbackDB(db_path=db_path)
    logger.info(f"✓ Feedback DB created (temp): {db_path}")

    yield db

    # Cleanup
    import os
    try:
        os.unlink(db_path)
        logger.info(f"✓ Feedback DB cleaned up: {db_path}")
    except Exception as e:
        logger.warning(f"Could not delete temp DB: {e}")


@pytest.fixture(scope="session")
def feedback_db_session():
    """
    BD para toda la sesión (si la necesitan tests de integración)
    """
    from offline_clinic.core.feedback_db import FeedbackDB

    temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = temp_db.name
    temp_db.close()

    db = FeedbackDB(db_path=db_path)
    logger.info(f"✓ Session Feedback DB created: {db_path}")

    yield db

    # Cleanup
    import os
    try:
        os.unlink(db_path)
        logger.info(f"✓ Session Feedback DB cleaned up")
    except Exception as e:
        logger.warning(f"Could not delete session DB: {e}")


# ============================================================================
# FIXTURES: HYBRID SEARCH
# ============================================================================

@pytest.fixture(scope="session")
def hybrid_search(catalog_manager, semantic_engine, feedback_db_session, ner_extractor):
    """
    Motor híbrido reutilizado en todos los tests
    """
    from offline_clinic.core.hybrid_search_v4 import HybridSearchV4

    search = HybridSearchV4(catalog_manager, semantic_engine, feedback_db_session, ner_extractor)
    logger.info("✓ Hybrid Search V4 initialized")
    return search


# ============================================================================
# FIXTURES: RAG ENGINE
# ============================================================================

@pytest.fixture(scope="session")
def rag_engine(hybrid_search):
    """
    RAG Engine para tests de integración
    """
    from offline_clinic.core.rag_engine import RAGEngine

    rag = RAGEngine(hybrid_search, ollama_base_url="http://localhost:11434")
    logger.info("✓ RAG Engine initialized")
    return rag


# ============================================================================
# FIXTURES: TEST DATA
# ============================================================================

@pytest.fixture
def sample_queries():
    """
    Queries de ejemplo para testing
    """
    return [
        "Tengo fiebre alta",
        "Me duele la cabeza",
        "Tos persistente",
        "Dificultad para respirar",
        "Dolor abdominal",
        "Erupción en la piel",
        "Mareo y nausea",
        "Dolor de garganta",
    ]


@pytest.fixture
def sample_medical_conditions():
    """
    Condiciones médicas para testing
    """
    return {
        'R50': 'FIEBRE',
        'G43': 'MIGRAÑA',
        'R05': 'TOS',
        'R06': 'ANOMALÍAS RESPIRATORIAS',
        'R10': 'DOLOR ABDOMINAL',
        'R51': 'CEFALEA',
        'M54': 'DORSALGIA',
    }


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Hook que se ejecuta antes de los tests
    """
    # Registrar markers custom
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "load: mark test as a load test")
    config.addinivalue_line("markers", "slow: mark test as slow (>5s)")
    config.addinivalue_line("markers", "rag: mark test as RAG-related")

    logger.info("="*80)
    logger.info("MINSA Clinical Offline - Test Suite")
    logger.info("="*80)


def pytest_collection_modifyitems(config, items):
    """
    Modificar items recolectados para agregar markers automáticamente
    """
    for item in items:
        # Agregar markers basado en la carpeta
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "load" in str(item.fspath):
            item.add_marker(pytest.mark.load)

        # Marcar tests RAG
        if "rag" in item.name.lower():
            item.add_marker(pytest.mark.rag)


def pytest_sessionfinish(session, exitstatus):
    """
    Hook que se ejecuta después de todos los tests
    """
    logger.info("="*80)
    logger.info(f"Test Session Finished - Status: {exitstatus}")
    logger.info("="*80)
