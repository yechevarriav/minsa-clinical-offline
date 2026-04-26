"""
Unit Tests - Hybrid Search
Valida: Búsqueda híbrida (NER + semántica + historial)
"""

import pytest
import logging

logger = logging.getLogger(__name__)


class TestHybridSearch:
    """Tests para búsqueda híbrida (NER + semántica + historial)"""

    def test_hybrid_search_returns_results(self, hybrid_search):
        """Búsqueda híbrida debe devolver resultados"""
        result = hybrid_search.search("Tengo fiebre alta", max_results=10)
        assert result['total_found'] > 0, "Should return results"
        assert len(result['results']) > 0, "Should have results"
        logger.info(f"✓ Hybrid search returned {result['total_found']} results")

    def test_hybrid_search_ner_detected(self, hybrid_search):
        """Debe detectar síntomas con NER"""
        result = hybrid_search.search("Me duele la cabeza y tengo fiebre")
        assert len(result['ner_symptoms_detected']) > 0, "Should detect symptoms"
        logger.info(f"✓ NER detected symptoms: {result['ner_symptoms_detected']}")

    def test_hybrid_search_ner_improves_results(self, hybrid_search):
        """Los síntomas detectados por NER deben estar en 'found_by'"""
        result = hybrid_search.search("dolor de cabeza")

        # Al menos algunos resultados deben mencionar NER
        ner_found_results = [r for r in result['results'] if 'NER' in r.get('found_by', [])]
        assert len(ner_found_results) > 0, "NER should find some results"
        logger.info(f"✓ {len(ner_found_results)} results found by NER")

    def test_hybrid_search_relevance_ordered(self, hybrid_search):
        """Resultados deben estar ordenados por relevancia"""
        result = hybrid_search.search("fiebre", max_results=10)

        relevances = [r['relevance'] for r in result['results']]
        # Debe estar en orden descendente
        assert relevances == sorted(relevances, reverse=True), \
            "Results should be ordered by relevance"
        logger.info(f"✓ Results properly ordered by relevance")
