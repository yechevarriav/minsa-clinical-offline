import sys
sys.path.insert(0, 'src')

from offline_clinic.core.excel_loader_minsa import CatalogManager

print("Import CatalogManager OK")

catalog = CatalogManager(
    cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
    procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
)

print(f"CIE-10 codes: {len(catalog.get_all_cie10_codes())}")
print(f"Procedures: {len(catalog.get_all_procedimientos())}")
print("TEST PASSED!")
