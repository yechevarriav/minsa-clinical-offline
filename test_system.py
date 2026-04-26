"""
Test Suite - Sistema de Soporte Clínico Offline MINSA
Tests para validar: NER, búsqueda, feedback, aprendizaje
"""

import sys
import pytest
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def catalog_manager():
    """Cargar catálogo CIE-10 una sola vez"""
    from offline_clinic.core.excel_loader_minsa import CatalogManager

    cm = CatalogManager(
        cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
        procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
    )
    return cm


@pytest.fixture(scope="session")
def ner_extractor():
    """Inicializar NER extractor"""
    from offline_clinic.core.ner_extractor import MedicalNERExtractor
    return MedicalNERExtractor()


@pytest.fixture(scope="session")
def semantic_engine(catalog_manager):
    """Inicializar motor semántico"""
    from offline_clinic.core.semantic_search_medical import MedicalSemanticSearchEngine
    return MedicalSemanticSearchEngine(catalog_manager)


@pytest.fixture(scope="session")
def feedback_db(tmp_path_factory):
    """Crear BD temporal para tests"""
    from offline_clinic.core.feedback_db import FeedbackDB

    db_path = tmp_path_factory.mktemp("data") / "test_feedback.db"
    return FeedbackDB(db_path=str(db_path))


@pytest.fixture(scope="session")
def hybrid_search(catalog_manager, semantic_engine, feedback_db, ner_extractor):
    """Inicializar motor híbrido"""
    from offline_clinic.core.hybrid_search_v4 import HybridSearchV4
    return HybridSearchV4(catalog_manager, semantic_engine, feedback_db, ner_extractor)


# ============================================================================
# TESTS: CATALOGO CIE-10
# ============================================================================

class TestCatalogManager:
    """Tests para cargar y validar catálogo CIE-10"""

    def test_catalog_loaded(self, catalog_manager):
        """Verificar que CIE-10 se cargó correctamente"""
        codes = catalog_manager.get_all_cie10_codes()
        assert len(codes) == 14702, f"Expected 14702 codes, got {len(codes)}"
        logger.info(f"✓ Catalog loaded: {len(codes)} CIE-10 codes")

    def test_procedures_loaded(self, catalog_manager):
        """Verificar que procedimientos se cargaron"""
        procedures = catalog_manager.get_all_procedimientos()
        assert len(procedures) == 12141, f"Expected 12141 procedures, got {len(procedures)}"
        logger.info(f"✓ Procedures loaded: {len(procedures)}")

    def test_validate_valid_code(self, catalog_manager):
        """Validar un código CIE-10 válido"""
        # G43 es MIGRAÑA
        assert catalog_manager.validate_cie10("G43") == True
        logger.info("✓ Valid CIE-10 code validation passed")

    def test_validate_invalid_code(self, catalog_manager):
        """Rechazar código CIE-10 inválido"""
        assert catalog_manager.validate_cie10("ZZ99") == False
        logger.info("✓ Invalid CIE-10 code rejection passed")

    def test_get_diagnosis(self, catalog_manager):
        """Obtener descripción de un código"""
        desc = catalog_manager.get_diagnosis("G43")
        assert "MIGRANA" in desc.upper() or "MIGRAÑA" in desc.upper()
        logger.info(f"✓ Got diagnosis for G43: {desc}")


# ============================================================================
# TESTS: NER (Named Entity Recognition)
# ============================================================================

class TestNERExtractor:
    """Tests para extracción de entidades médicas"""

    def test_ner_fiebre(self, ner_extractor):
        """Detectar síntoma 'fiebre'"""
        symptoms = ner_extractor.extract_symptoms("Tengo fiebre alta")
        assert len(symptoms) > 0, "Should detect fiebre"
        assert any("fiebre" in s['entity'].lower() for s in symptoms)
        logger.info(f"✓ NER detected fiebre: {[s['entity'] for s in symptoms]}")

    def test_ner_dolor_cabeza(self, ner_extractor):
        """Detectar síntoma 'dolor de cabeza'"""
        symptoms = ner_extractor.extract_symptoms("Me duele la cabeza")
        assert len(symptoms) > 0, "Should detect dolor de cabeza"
        found = any("cabeza" in s['entity'].lower() or "dolor" in s['entity'].lower() for s in symptoms)
        assert found, f"Should detect cabeza/dolor, got {[s['entity'] for s in symptoms]}"
        logger.info(f"✓ NER detected dolor de cabeza: {[s['entity'] for s in symptoms]}")

    def test_ner_multiple_symptoms(self, ner_extractor):
        """Detectar múltiples síntomas"""
        symptoms = ner_extractor.extract_symptoms("Tengo fiebre y tos persistente")
        assert len(symptoms) >= 2, f"Should detect at least 2 symptoms, got {len(symptoms)}"
        logger.info(f"✓ NER detected multiple symptoms: {[s['entity'] for s in symptoms]}")

    def test_ner_no_false_positives(self, ner_extractor):
        """No detectar síntomas donde no los hay"""
        symptoms = ner_extractor.extract_symptoms("Hola mundo esto es una prueba")
        assert len(symptoms) == 0, "Should not detect symptoms in random text"
        logger.info("✓ NER correctly ignored non-medical text")

    def test_ner_confidence_score(self, ner_extractor):
        """Verificar que scores tienen valores válidos"""
        symptoms = ner_extractor.extract_symptoms("Tengo fiebre")
        assert all(0 <= s['score'] <= 1 for s in symptoms), "Scores must be between 0 and 1"
        logger.info(f"✓ NER confidence scores valid: {[s['score'] for s in symptoms]}")


# ============================================================================
# TESTS: BÚSQUEDA SEMANTICA
# ============================================================================

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


# ============================================================================
# TESTS: BÚSQUEDA HIBRIDA
# ============================================================================

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


# ============================================================================
# TESTS: FEEDBACK Y APRENDIZAJE
# ============================================================================

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


# ============================================================================
# TESTS: INTEGRACION (End-to-End)
# ============================================================================

class TestIntegration:
    """Tests de integración completa del sistema"""

    def test_full_pipeline_dolor_cabeza(self, hybrid_search, feedback_db):
        """Pipeline completo: búsqueda + feedback + reaprendizaje"""

        # 1. Búsqueda inicial
        result1 = hybrid_search.search("dolor de cabeza", max_results=10)
        assert result1['total_found'] > 0, "Should find results"

        codes_before = [r['code'] for r in result1['results'][:3]]
        logger.info(f"Initial results: {codes_before}")

        # 2. Guardar feedback (usuario selecciona G43)
        feedback_db.save_selection(
            query="dolor de cabeza",
            selected_code="G43",
            selected_description="G43 - MIGRAÑA"
        )

        # 3. Verificar que aprendió
        synonyms = feedback_db.get_learned_synonyms("dolor de cabeza")
        assert len(synonyms) > 0, "Should have learned from feedback"
        logger.info(f"Learned synonyms: {synonyms}")

        # 4. Búsqueda similar debería beneficiarse del feedback
        history = feedback_db.get_history_for_query("dolor de cabeza")
        assert len(history) > 0, "Should have history"
        assert history[0]['code'] == "G43", "Should have learned selection"

        logger.info("✓ Full pipeline test passed")

    def test_ner_improves_search_accuracy(self, hybrid_search):
        """NER debe mejorar precisión de búsqueda"""

        # Query coloquial
        query = "Me duele mucho la cabeza"
        result = hybrid_search.search(query, max_results=5)

        # Debe detectar síntomas
        assert len(result['ner_symptoms_detected']) > 0, "Should detect symptoms"

        # Top resultado debe ser cefalea/migraña (o sus subcategorías)
        top_code = result['results'][0]['code'] if result['results'] else None
        # Validar que empiece con G43, R51 o G44 (puede ser G440, G441, etc)
        valid_codes = ['G43', 'R51', 'G44']
        is_valid = any(top_code.startswith(code) for code in valid_codes) if top_code else False
        assert is_valid, \
            f"Top result should be cefalea/migraña, got {top_code}"

        logger.info(f"✓ NER improved accuracy: top result = {top_code}")


# ============================================================================
# TESTS: PERFORMANCE
# ============================================================================

class TestPerformance:
    """Tests para verificar performance"""

    def test_search_latency(self, hybrid_search):
        """Búsqueda debe ser rápida (<500ms)"""
        import time

        start = time.time()
        result = hybrid_search.search("fiebre", max_results=10)
        elapsed = (time.time() - start) * 1000

        assert elapsed < 500, f"Search took {elapsed}ms, should be <500ms"
        logger.info(f"✓ Search latency: {elapsed:.0f}ms")

    def test_multiple_searches_performance(self, hybrid_search):
        """Múltiples búsquedas consecutivas deben ser rápidas"""
        import time

        queries = ["fiebre", "tos", "dolor", "mareo", "cansancio"]
        times = []

        for query in queries:
            start = time.time()
            hybrid_search.search(query, max_results=5)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        assert avg_time < 500, f"Average search time {avg_time}ms should be <500ms"
        logger.info(f"✓ Multiple searches average: {avg_time:.0f}ms")


# ============================================================================
# EJECUTAR TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
