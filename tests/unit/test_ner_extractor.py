"""
Unit Tests - NER Extractor
Valida: Extracción de entidades médicas (síntomas)
"""

import pytest
import logging

logger = logging.getLogger(__name__)


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
