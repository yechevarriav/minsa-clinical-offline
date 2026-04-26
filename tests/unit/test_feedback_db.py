"""
Unit Tests - Feedback Database
Valida: Sistema de feedback y aprendizaje colectivo
"""

import pytest
import logging

logger = logging.getLogger(__name__)


class TestFeedback:
    """Tests para sistema de feedback y aprendizaje"""

    def test_save_feedback(self, feedback_db):
        """Guardar feedback"""
        success = feedback_db.save_selection(
            query="dolor de cabeza",
            selected_code="G43",
            selected_description="G43 - MIGRAÑA"
        )
        assert success == True, "Should save feedback successfully"
        logger.info("✓ Feedback saved successfully")

    def test_get_history(self, feedback_db):
        """Obtener historial de selecciones"""
        # Primero guardar
        feedback_db.save_selection(
            query="fiebre",
            selected_code="R50",
            selected_description="R50 - FIEBRE"
        )

        # Luego recuperar
        history = feedback_db.get_history_for_query("fiebre")
        assert len(history) > 0, "Should retrieve history"
        assert history[0]['code'] == "R50", "Should have correct code"
        logger.info(f"✓ History retrieved: {history}")

    def test_learned_synonyms(self, feedback_db):
        """Sistema debe aprender sinónimos"""
        # Guardar selección
        feedback_db.save_selection(
            query="dolor de cabeza",
            selected_code="G43",
            selected_description="G43 - MIGRAÑA"
        )

        # Debe haber aprendido sinónimos
        synonyms = feedback_db.get_learned_synonyms("dolor de cabeza")
        assert len(synonyms) > 0, "Should have learned synonyms"
        logger.info(f"✓ Learned synonyms: {synonyms}")

    def test_selection_count_increment(self, feedback_db):
        """Contador de selecciones debe incrementar"""
        # Primera vez
        feedback_db.save_selection(
            query="asma",
            selected_code="J45",
            selected_description="J45 - ASMA"
        )

        history1 = feedback_db.get_history_for_query("asma")
        count1 = history1[0]['selection_count'] if history1 else 0

        # Segunda vez (misma query y código)
        feedback_db.save_selection(
            query="asma",
            selected_code="J45",
            selected_description="J45 - ASMA"
        )

        history2 = feedback_db.get_history_for_query("asma")
        count2 = history2[0]['selection_count'] if history2 else 0

        assert count2 > count1, "Selection count should increment"
        logger.info(f"✓ Selection count incremented: {count1} -> {count2}")

    def test_feedback_stats(self, feedback_db):
        """Obtener estadísticas de feedback"""
        stats = feedback_db.get_stats()
        assert 'total_records' in stats, "Should have total_records"
        assert 'learned_synonyms' in stats, "Should have learned_synonyms"
        logger.info(f"✓ Feedback stats: {stats}")
