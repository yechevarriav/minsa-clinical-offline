"""
Unit Tests - RAG Engine
Valida: Componentes individuales del motor RAG
"""

import pytest
import logging

logger = logging.getLogger(__name__)


class TestRAGEngine:
    """Tests unitarios para RAG Engine"""

    def test_rag_initialization(self, rag_engine):
        """RAG Engine debe inicializar correctamente"""
        assert rag_engine is not None
        assert rag_engine.search is not None
        assert rag_engine.model == "llama2:7b"
        logger.info("✓ RAG Engine initialized")

    def test_rag_retrieval_step(self, rag_engine):
        """Paso 1: Retrieval - Recuperar CIE-10"""
        question = "Paciente con fiebre alta"

        result = rag_engine.search.search(question, max_results=5)

        assert result['total_found'] > 0, "Should retrieve CIE-10 codes"
        assert len(result['results']) > 0, "Should have results"

        logger.info(f"✓ Retrieval: Found {len(result['results'])} codes")

    def test_rag_context_building(self, rag_engine):
        """Paso 2: Augmented - Construir contexto"""
        question = "¿Qué hacer con fiebre y tos?"
        retrieved = rag_engine.search.search(question, max_results=3)

        context = rag_engine._build_context(question, retrieved['results'])

        assert len(context) > 0, "Context should not be empty"
        assert question in context, "Context should contain question"
        assert "CIE-10" in context, "Context should mention CIE-10"

        logger.info(f"✓ Context built: {len(context)} chars")

    def test_rag_metrics_calculation(self, rag_engine):
        """Validar cálculo de métricas"""
        question = "Tos persistente"
        result = rag_engine.query(question, use_llm=False)

        metrics = result['metrics']

        # Validar campos de métrica
        assert 'question_length' in metrics
        assert 'num_retrieved_codes' in metrics
        assert 'avg_relevance' in metrics
        assert 'context_length' in metrics
        assert 'elapsed_time_seconds' in metrics

        # Validar rangos
        assert metrics['question_length'] > 0
        assert metrics['num_retrieved_codes'] >= 0
        assert 0 <= metrics['avg_relevance'] <= 1
        assert metrics['context_length'] > 0
        assert metrics['elapsed_time_seconds'] > 0

        logger.info(f"✓ Metrics calculated:")
        logger.info(f"  - Avg relevance: {metrics['avg_relevance']:.3f}")
        logger.info(f"  - Elapsed time: {metrics['elapsed_time_seconds']:.3f}s")
