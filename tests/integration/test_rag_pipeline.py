"""
Integration Tests - RAG Pipeline
Tests end-to-end del pipeline RAG completo (Item 3.7)
Valida: Retrieval + Augmented + Generation
"""

import pytest
import logging
import json
import tempfile

logger = logging.getLogger(__name__)


class TestRAGPipeline:
    """Tests del pipeline RAG completo"""

    def test_rag_full_pipeline_without_llm(self, rag_engine):
        """
        Pipeline RAG completo SIN LLM (más rápido para test)
        Valida: Retrieval + Augmented (sin Generation)
        """
        question = "Paciente con dolor de cabeza y mareo"

        result = rag_engine.query(question, top_k=5, use_llm=False)

        # Validar estructura
        assert 'question' in result
        assert 'retrieved_codes' in result
        assert 'context' in result
        assert 'metrics' in result
        assert 'timestamp' in result

        # Validar contenido
        assert result['question'] == question
        assert len(result['retrieved_codes']) > 0, "Should retrieve codes"
        assert len(result['context']) > 0, "Should build context"
        assert result['llm_response'] is None, "LLM should be None (use_llm=False)"

        logger.info(f"✓ RAG pipeline completed (no LLM)")
        logger.info(f"  Retrieved {len(result['retrieved_codes'])} codes")
        logger.info(f"  Relevance: {result['metrics']['avg_relevance']:.3f}")

    def test_rag_retrieval_with_ner(self, rag_engine):
        """
        Validar que Retrieval usa NER correctamente
        """
        question = "Me duele mucho la cabeza"

        result = rag_engine.query(question, use_llm=False)

        # Debe detectar síntomas con NER
        assert len(result['retrieved_codes']) > 0

        # Top resultado debe ser cefalea/migraña
        top_code = result['retrieved_codes'][0]['code'] if result['retrieved_codes'] else None
        valid_codes = ['G43', 'R51', 'G44']
        is_valid = any(top_code.startswith(code) for code in valid_codes) if top_code else False

        assert is_valid, f"Top result should be cefalea/migraña, got {top_code}"
        logger.info(f"✓ NER improved retrieval: top result = {top_code}")

    def test_rag_context_quality(self, rag_engine):
        """
        Validar que el contexto construido es de buena calidad
        """
        question = "Fiebre alta"
        result = rag_engine.query(question, use_llm=False)

        context = result['context']

        # Validar que contiene elementos esperados
        assert "PREGUNTA" in context.upper()
        assert "CIE-10" in context
        assert "PROTOCOLO" in context.upper()

        # Validar longitud
        assert len(context) > 200, "Context should be substantial"

        logger.info(f"✓ Context quality validated ({len(context)} chars)")

    def test_rag_multiple_queries(self, rag_engine):
        """
        Ejecutar múltiples queries y validar acumulación de métricas
        """
        questions = [
            "Fiebre en niño",
            "Dolor abdominal persistente",
            "Dificultad para respirar",
            "Erupción en la piel",
            "Mareo y nausea"
        ]

        # Resetear métricas para este test
        initial_count = rag_engine.get_metrics_report()['total_queries']

        for question in questions:
            result = rag_engine.query(question, use_llm=False)
            assert result is not None
            assert len(result['retrieved_codes']) > 0

        # Obtener reporte de métricas
        report = rag_engine.get_metrics_report()

        # El reporte puede acumular de tests anteriores, así que solo verificamos incremento
        assert report['total_queries'] >= initial_count + len(questions)
        assert report['avg_elapsed_time_seconds'] > 0
        assert report['avg_relevance'] > 0

        logger.info(f"✓ Executed {len(questions)} queries")
        logger.info(f"  Total queries: {report['total_queries']}")
        logger.info(f"  Avg relevance: {report['avg_relevance']:.3f}")

    def test_rag_metrics_report(self, rag_engine):
        """
        Validar que el reporte de métricas tiene estructura correcta (Item 3.8)
        """
        # Hacer algunas queries
        for q in ["Fiebre", "Tos", "Dolor"]:
            rag_engine.query(q, use_llm=False)

        report = rag_engine.get_metrics_report()

        # Validar estructura
        assert 'total_queries' in report
        assert 'avg_elapsed_time_seconds' in report
        assert 'avg_relevance' in report
        assert 'llm_success_rate' in report
        assert 'metrics_by_query' in report

        # Validar que es serializable a JSON
        json_str = json.dumps(report, indent=2)
        assert len(json_str) > 0

        logger.info(f"✓ Metrics report generated")
        logger.info(f"  {json_str[:200]}...")

    def test_rag_ingest_document(self, rag_engine):
        """
        Validar que se pueden ingerir documentos clínicos
        """
        title = "Protocolo MINSA - Fiebre en Niños"
        content = "Este protocolo describe el manejo de fiebre en población pediátrica..."

        result = rag_engine.ingest_document(title, content)

        assert result['status'] == 'ingested'
        assert result['document_id'] is not None
        assert result['title'] == title
        assert result['content_length'] == len(content)

        logger.info(f"✓ Document ingested: {result['document_id']}")


class TestRAGIntegrationWithFeedback:
    """Tests de integración RAG con sistema de feedback"""

    def test_full_pipeline_with_feedback(self, rag_engine, hybrid_search, feedback_db_session):
        """
        Pipeline completo: búsqueda + feedback + aprendizaje
        """
        # 1. Búsqueda inicial
        result1 = rag_engine.query("dolor de cabeza", top_k=10, use_llm=False)
        assert result1 is not None, "Should have result"
        assert len(result1['retrieved_codes']) > 0, "Should find codes"

        codes_before = [r['code'] for r in result1['retrieved_codes'][:3]]
        logger.info(f"Initial results: {codes_before}")

        # 2. Guardar feedback
        feedback_db_session.save_selection(
            query="dolor de cabeza",
            selected_code="G43",
            selected_description="G43 - MIGRAÑA"
        )

        # 3. Verificar que aprendió
        synonyms = feedback_db_session.get_learned_synonyms("dolor de cabeza")
        assert len(synonyms) > 0, "Should have learned from feedback"
        logger.info(f"Learned synonyms: {synonyms}")

        # 4. Verificar historial
        history = feedback_db_session.get_history_for_query("dolor de cabeza")
        assert len(history) > 0, "Should have history"
        assert history[0]['code'] == "G43", "Should have learned selection"

        logger.info("✓ Full pipeline with feedback completed")


class TestRAGErrorHandling:
    """Tests de manejo de errores en RAG"""

    def test_rag_with_empty_query(self, rag_engine):
        """Manejar query vacía"""
        result = rag_engine.query("", use_llm=False)
        # Debería devolver resultado válido (posiblemente vacío)
        assert result is not None
        logger.info("✓ Handled empty query")

    def test_rag_with_long_query(self, rag_engine):
        """Manejar query muy larga"""
        long_query = "dolor " * 100
        result = rag_engine.query(long_query, use_llm=False)
        assert result is not None
        logger.info("✓ Handled long query")

    def test_rag_with_special_characters(self, rag_engine):
        """Manejar query con caracteres especiales"""
        query = "¿Qué hacer con fiebre, tos y @#$%?"
        result = rag_engine.query(query, use_llm=False)
        assert result is not None
        logger.info("✓ Handled special characters")


# ============================================================================
# PYTEST MARKERS
# ============================================================================

@pytest.mark.integration
@pytest.mark.rag
def test_rag_pipeline_marker(rag_engine):
    """Test marcado como integration y rag"""
    result = rag_engine.query("fiebre", use_llm=False)
    assert result is not None
