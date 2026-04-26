"""
Unit Tests - CatalogManager
Valida: Carga, validación y consulta de CIE-10 y procedimientos
"""

import pytest
import logging

logger = logging.getLogger(__name__)


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
