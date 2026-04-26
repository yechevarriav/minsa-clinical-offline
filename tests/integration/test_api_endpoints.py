"""
Integration Tests - RAG Engine Direct (Sin API HTTP)
Valida funcionalidad del motor RAG directamente
Nota: Tests de API HTTP son para deployment, aquí testeamos la lógica del RAG
"""

import pytest
import logging

logger = logging.getLogger(__name__)


class TestRAGEngineIntegration:
    """Tests del RAG Engine directamente (sin API FastAPI)"""

    def test_rag_engine_query(self, rag_engine):
        """Test consulta RAG Engine"""
        result = rag_engine.query("¿Qué hacer con fiebre?", use_llm=False)
        assert result is not None
        assert 'retrieved_codes' in result
        assert len(result['retrieved_codes']) > 0
        logger.info("✓ RAG Engine query working")

    def test_rag_engine_ingest(self, rag_engine):
        """Test ingesta de documento"""
        result = rag_engine.ingest_document(
            title="Test Protocol",
            content="This is a test protocol..."
        )
        assert result['status'] == 'ingested'
        assert result['document_id'] is not None
        logger.info("✓ Document ingest working")

    def test_rag_engine_metrics(self, rag_engine):
        """Test métricas del RAG Engine"""
        # Hacer una query
        rag_engine.query("dolor", use_llm=False)

        # Obtener métricas
        metrics = rag_engine.get_metrics_report()
        assert metrics is not None
        assert 'total_queries' in metrics
        assert metrics['total_queries'] > 0
        logger.info("✓ Metrics endpoint working")

    def test_rag_engine_with_multiple_symptoms(self, rag_engine):
        """Test query con múltiples síntomas"""
        result = rag_engine.query(
            "Fiebre alta, tos y dolor de cabeza",
            use_llm=False
        )
        assert result is not None
        assert len(result['retrieved_codes']) > 0
        logger.info("✓ Multiple symptoms query working")

    def test_rag_engine_response_structure(self, rag_engine):
        """Validar estructura completa de respuesta"""
        result = rag_engine.query("dolor", use_llm=False)

        # Validar estructura
        assert isinstance(result['retrieved_codes'], list)
        assert isinstance(result['context'], str)
        assert isinstance(result['metrics'], dict)
        assert isinstance(result['timestamp'], str)

        # Validar cada código recuperado
        for code in result['retrieved_codes']:
            assert 'code' in code
            assert 'description' in code
            assert 'relevance' in code

        logger.info("✓ Response structure validated")

    def test_rag_engine_health_check(self, rag_engine):
        """Test que el sistema está saludable"""
        # Si el RAG Engine inicializa correctamente, el sistema está bien
        assert rag_engine is not None
        assert rag_engine.search is not None
        assert rag_engine.model == "llama2:7b"
        logger.info("✓ System health check passed")
