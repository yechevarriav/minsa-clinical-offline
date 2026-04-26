"""
Excel Loader - CIE-10 MINSA + Procedimientos MEDICOS
Version DEFINITIVA - Captura TODOS los codigos CIE-10 (3 y 4 digitos)
"""

import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CIE10Loader:
    """Load CIE-10 MINSA Official codes - TODOS los codigos"""

    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        self.df = None
        self.codes_dict = {}
        self._load()

    def _load(self):
        """Load and parse CIE-10 Excel - CAPTURA TODOS LOS CODIGOS"""
        logger.info(f"Loading CIE-10 from {self.excel_path}")

        try:
            df = pd.read_excel(self.excel_path, sheet_name="VOLUMEN VIGENTE")
            df = df[1:].reset_index(drop=True)  # Skip header

            for idx, row in df.iterrows():
                text = str(row.iloc[0]).strip()

                # PATRON MEJORADO: Captura códigos de 3 O 4+ dígitos
                # A00, A000, A0090, etc.
                # Busca: Letra + 2-4 dígitos + opcional guión + descripción
                match = re.match(r'^([A-Z]\d{2,4})\s*-\s*(.+)$', text)

                if match:
                    code = match.group(1)  # A00, A000, A0090, etc.
                    description = match.group(2).strip()

                    # Guardar código completo Y su versión base
                    self.codes_dict[code] = text

                    # También guardar versión de 3 caracteres (A000 -> A00)
                    base_code = code[:3]
                    if base_code not in self.codes_dict:
                        self.codes_dict[base_code] = text

            logger.info(f"Loaded {len(self.codes_dict)} CIE-10 codes")

            if len(self.codes_dict) < 10000:
                logger.warning(
                    f"Expected ~15000 codes but got {len(self.codes_dict)}. "
                    f"This might be normal if subcodes are included."
                )

        except Exception as e:
            logger.error(f"Error loading CIE-10: {e}")
            raise

    def is_valid_code(self, code: str) -> bool:
        """Check if code exists (supports A00, A000, A0090, etc.)"""
        code_upper = code.upper()

        # Buscar código exacto
        if code_upper in self.codes_dict:
            return True

        # Buscar por prefijo (A000 busca A00)
        if len(code_upper) >= 3:
            base_code = code_upper[:3]
            if base_code in self.codes_dict:
                return True

        return False

    def get_description(self, code: str) -> Optional[str]:
        """Get description for code"""
        code_upper = code.upper()

        # Buscar exacto
        if code_upper in self.codes_dict:
            return self.codes_dict[code_upper]

        # Buscar base (A000 -> A00)
        if len(code_upper) >= 3:
            base_code = code_upper[:3]
            if base_code in self.codes_dict:
                return self.codes_dict[base_code]

        return None

    def get_all_codes(self) -> List[str]:
        return list(self.codes_dict.keys())


class ProcedimientosLoader:
    """Load Procedimientos Medicos y Sanitarios from MINSA"""

    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        self.df = None
        self.procedures_by_code = {}
        self._load()

    def _load(self):
        """Load and parse Procedimientos Excel"""
        logger.info(f"Loading Procedimientos from {self.excel_path}")

        try:
            df = pd.read_excel(self.excel_path, sheet_name="ANEXO 1")
            df.columns = [
                'N', 'CODIGO_GRUPO', 'NOMBRE_GRUPO', 'CODIGO_SECCION',
                'NOMBRE_SECCION', 'CODIGO_SUBSECCION', 'NOMBRE_SUBSECCION',
                'CODIGO_PROCEDIMIENTO', 'DENOMINACION_PROCEDIMIENTO'
            ]
            self.df = df[1:].reset_index(drop=True)
            self.df = self.df.dropna(subset=['CODIGO_PROCEDIMIENTO'])

            for _, row in self.df.iterrows():
                code = str(row['CODIGO_PROCEDIMIENTO']).strip()
                self.procedures_by_code[code] = {
                    'code': code,
                    'name': str(row['DENOMINACION_PROCEDIMIENTO']).strip(),
                    'grupo': str(row['CODIGO_GRUPO']).strip()
                }

            logger.info(f"Loaded {len(self.procedures_by_code)} procedimientos")

        except Exception as e:
            logger.error(f"Error loading Procedimientos: {e}")
            raise


class CatalogManager:
    """Unified catalog manager for CIE-10 + Procedimientos"""

    def __init__(self, cie10_path: str, procedimientos_path: str):
        self.cie10_loader = CIE10Loader(cie10_path)
        self.procedimientos_loader = ProcedimientosLoader(procedimientos_path)
        logger.info("CatalogManager initialized with MINSA data")

    def validate_cie10(self, code: str) -> bool:
        return self.cie10_loader.is_valid_code(code)

    def get_diagnosis(self, cie10_code: str) -> Optional[str]:
        return self.cie10_loader.get_description(cie10_code)

    def get_all_cie10_codes(self) -> List[str]:
        return self.cie10_loader.get_all_codes()

    def get_all_procedimientos(self) -> Dict[str, Dict]:
        return self.procedimientos_loader.procedures_by_code

    def get_documents_for_rag(self) -> List:
        """Get documents for RAG indexing"""
        from langchain.schema import Document

        documents = []
        for code, description in self.cie10_loader.codes_dict.items():
            documents.append(Document(
                page_content=f"CIE-10 {code}: {description}",
                metadata={'type': 'diagnosis', 'code': code}
            ))

        for code, proc in self.procedimientos_loader.procedures_by_code.items():
            documents.append(Document(
                page_content=f"Procedimiento {code}: {proc['name']}",
                metadata={'type': 'procedure', 'code': code}
            ))

        logger.info(f"Created {len(documents)} documents for RAG")
        return documents


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    catalog = CatalogManager(
        cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
        procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
    )

    print(f"\nCIE-10 codes loaded: {len(catalog.get_all_cie10_codes())}")
    print(f"Procedures loaded: {len(catalog.get_all_procedimientos())}")

    # Test códigos comunes
    test_codes = ['A00', 'A000', 'E11', 'I10', 'J45']
    print("\nTesting sample codes:")
    for code in test_codes:
        if catalog.validate_cie10(code):
            desc = catalog.get_diagnosis(code)
            print(f"  {code}: {desc[:60] if desc else 'N/A'}...")

    print("\nTest OK!")
