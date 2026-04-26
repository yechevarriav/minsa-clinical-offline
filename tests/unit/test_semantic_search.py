"""
Unit Tests - Semantic Search
Valida: Búsqueda semántica con RoBERTa biomedical
"""

import pytest
import logging

logger = logging.getLogger(__name__)


class TestSemanticSearch:
    """Tests para búsqueda semántica"""

    def test_semantic_search_returns_results(self, semantic_engine):
        """Búsqueda semántica debe devolver resultados"""
        results = semantic_engine.search("dolor de cabeza", top_k=10)
        assert len(results) > 0, "Should return results for 'dolor de cabeza'"
        logger.info(f"✓ Semantic search returned {len(results)} results")

    def test_semantic_search_relevant_results(self, semantic_engine):
        """Los resultados deben ser relevantes (G43 o R51 para 'dolor de cabeza')"""
        results = semantic_engine.search("dolor de cabeza", top_k=10)
        codes = [r['code'] for r in results]
        # G43 (MIGRAÑA) o R51 (CEFALEA) deben estar en los primeros 5
        top_5_codes = codes[:5]
        assert "G43" in top_5_codes or "R51" in top_5_codes, \
            f"G43 or R51 should be in top 5, got {top_5_codes}"
        logger.info(f"✓ Top codes for 'dolor de cabeza': {top_5_codes}")

    def test_semantic_search_score_range(self, semantic_engine):
        """Los scores deben estar entre 0 y 1"""
        results = semantic_engine.search("fiebre", top_k=5)
        assert all(0 <= r['score'] <= 1 for r in results), "Scores must be 0-1"
        logger.info(f"✓ Semantic search scores in valid range")

    def test_semantic_search_different_queries(self, semantic_engine):
        """Diferentes queries deben dar resultados diferentes"""
        results1 = semantic_engine.search("fiebre", top_k=5)
        results2 = semantic_engine.search("tos", top_k=5)

        codes1 = {r['code'] for r in results1}
        codes2 = {r['code'] for r in results2}

        # No deben ser idénticos
        assert codes1 != codes2, "Different queries should give different results"
        logger.info(f"✓ Different queries give different results")
