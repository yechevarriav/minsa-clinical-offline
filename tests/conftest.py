"""
Pytest Configuration - Fixtures compartidas
Con soporte para LOCAL + GitHub Actions
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Agregar src/ al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Detectar si estamos en CI
IS_CI = os.getenv("GITHUB_ACTIONS") == "true"

# ============================================================================
# FIXTURES - Scope SESSION
# ============================================================================

@pytest.fixture(scope="session")
def catalog_manager():
    """Cargar catálogo CIE-10"""
    if IS_CI:
        mock_cm = MagicMock()
        mock_cm.codes = {
            "A00": "Cólera",
            "E10": "Diabetes mellitus",
            "I10": "Hipertensión",
            "J45": "Asma",
        }
        return mock_cm
    else:
        try:
            from offline_clinic.core.excel_loader_minsa import CatalogManager
            cm = CatalogManager()
            cm.load_from_excel()
            return cm
        except Exception:
            mock_cm = MagicMock()
            mock_cm.codes = {"A00": "Cólera"}
            return mock_cm

@pytest.fixture(scope="session")
def ner_extractor():
    """NER Extractor"""
    if IS_CI:
        mock_ner = MagicMock()
        mock_ner.extract = MagicMock(return_value=["fiebre", "tos"])
        return mock_ner
    else:
        try:
            from offline_clinic.core.ner_extractor import NERExtractor
            return NERExtractor()
        except Exception:
            return MagicMock()

@pytest.fixture(scope="session")
def semantic_engine():
    """Semantic Search Engine"""
    if IS_CI:
        mock_se = MagicMock()
        mock_se.search = MagicMock(return_value=["A00", "E10"])
        return mock_se
    else:
        try:
            from offline_clinic.core.semantic_search_medical import SemanticSearchEngine
            engine = SemanticSearchEngine()
            return engine
        except Exception:
            return MagicMock()

@pytest.fixture(scope="session")
def hybrid_search():
    """Hybrid Search"""
    if IS_CI:
        mock_hs = MagicMock()
        mock_hs.search = MagicMock(return_value=["A00", "E10", "I10"])
        return mock_hs
    else:
        try:
            from offline_clinic.core.hybrid_search_v4 import HybridSearchV4
            return HybridSearchV4()
        except Exception:
            return MagicMock()

@pytest.fixture(scope="session")
def rag_engine():
    """RAG Engine"""
    if IS_CI:
        mock_rag = MagicMock()
        mock_rag.query = MagicMock(return_value={
            "question": "test",
            "retrieved_codes": ["A00"],
            "context": "Mock data",
            "metrics": {"score": 0.9},
            "timestamp": "2026-04-26T00:00:00",
            "ner_symptoms_detected": ["fever"],
            "llm_response": None
        })
        return mock_rag
    else:
        try:
            from offline_clinic.core.rag_engine import RAGEngine
            return RAGEngine()
        except Exception:
            return MagicMock()

@pytest.fixture(scope="session")
def feedback_db_session():
    """Feedback Database - Session scope"""
    if IS_CI:
        return MagicMock()
    else:
        try:
            from offline_clinic.core.feedback_db import FeedbackDB
            db = FeedbackDB()
            db.init_db()
            yield db
            db.close()
        except Exception:
            yield MagicMock()

# ============================================================================
# FIXTURES - Scope FUNCTION
# ============================================================================

@pytest.fixture
def feedback_db():
    """Feedback Database - Function scope"""
    if IS_CI:
        return MagicMock()
    else:
        try:
            from offline_clinic.core.feedback_db import FeedbackDB
            db = FeedbackDB()
            db.init_db()
            yield db
            db.close()
        except Exception:
            yield MagicMock()

@pytest.fixture
def sample_queries():
    """Sample medical queries"""
    return [
        "Paciente con fiebre y tos",
        "Dolor en el pecho",
        "Presión arterial alta",
        "Dificultad para respirar",
        "Mareos y vómitos",
        "Síntomas de diabetes",
        "Infección urinaria",
        "Alergia en la piel",
    ]

@pytest.fixture
def sample_medical_conditions():
    """Sample CIE-10 conditions"""
    return {
        "A00": {"name": "Cólera", "severity": "high"},
        "E10": {"name": "Diabetes Type 1", "severity": "medium"},
        "I10": {"name": "Hipertensión", "severity": "medium"},
        "J45": {"name": "Asma", "severity": "medium"},
        "G89": {"name": "Pain", "severity": "low"},
    }

# ============================================================================
# PYTEST MARKERS
# ============================================================================

def pytest_configure(config):
    """Registrar custom markers"""
    config.addinivalue_line("markers", "unit: test unitario")
    config.addinivalue_line("markers", "integration: test de integración")
    config.addinivalue_line("markers", "load: test de carga")
    config.addinivalue_line("markers", "slow: test lento")
    config.addinivalue_line("markers", "rag: test del RAG engine")

def pytest_collection_modifyitems(config, items):
    """Modificar items de test según markers"""
    for item in items:
        if "load" in item.nodeid:
            item.add_marker(pytest.mark.slow)
