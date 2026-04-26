"""
FastAPI Main Application - Sistema de Soporte Clinico MINSA
Version 7.0 - Con NER (Named Entity Recognition) para entidades médicas
SIMPLIFICADO: Sin solicitar edad/sexo (no tiene datos en CIE-10)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

catalog_manager = None
semantic_engine = None
feedback_db = None
hybrid_search = None
ner_extractor = None


class SymptomsRequest(BaseModel):
    symptoms: str = Field(..., description="Sintomas en lenguaje natural")
    max_results: Optional[int] = Field(default=10)


class CIE10Result(BaseModel):
    code: str
    description: str
    relevance: float
    from_history: Optional[bool] = False
    history_count: Optional[int] = 0
    found_by: Optional[List[str]] = []


class SymptomsResponse(BaseModel):
    query: str
    results: List[CIE10Result]
    total_found: int
    has_history: bool
    history_count: int
    ner_symptoms_detected: Optional[List[str]] = []


class SearchAllRequest(BaseModel):
    query: str = Field(..., description="Buscar en TODO el catalogo")
    max_results: Optional[int] = Field(default=50)


class FeedbackRequest(BaseModel):
    query: str = Field(..., description="Query original")
    selected_code: str = Field(..., description="Codigo CIE-10 seleccionado")
    selected_description: Optional[str] = Field(default=None)


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    learned_synonyms: Optional[int] = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global catalog_manager, semantic_engine, feedback_db, hybrid_search, ner_extractor

    logger.info("Initializing Soporte Clinico Offline V7.0 (with NER)...")

    try:
        from offline_clinic.core.excel_loader_minsa import CatalogManager
        from offline_clinic.core.semantic_search_medical import MedicalSemanticSearchEngine
        from offline_clinic.core.feedback_db import FeedbackDB
        from offline_clinic.core.hybrid_search_v4 import HybridSearchV4
        from offline_clinic.core.ner_extractor import MedicalNERExtractor

        # 1. Cargar catálogo
        catalog_manager = CatalogManager(
            cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
            procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
        )
        logger.info(f"Loaded {len(catalog_manager.get_all_cie10_codes())} CIE-10 codes")

        # 2. Inicializar NER
        logger.info("Initializing Medical NER...")
        ner_extractor = MedicalNERExtractor()

        # 3. Inicializar búsqueda semántica
        logger.info("Initializing Medical Semantic Search...")
        semantic_engine = MedicalSemanticSearchEngine(catalog_manager)

        # 4. Base de datos de feedback
        feedback_db = FeedbackDB()
        stats = feedback_db.get_stats()
        logger.info(f"Feedback DB stats: {stats}")

        # 5. Motor híbrido con NER
        hybrid_search = HybridSearchV4(catalog_manager, semantic_engine, feedback_db, ner_extractor)

        logger.info("System ready!")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Sistema de Soporte Clinico Offline",
    description="MINSA Peru - Busqueda con NER + Aprendizaje",
    version="7.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Sistema de Soporte Clinico MINSA",
        "version": "7.0.0",
        "features": [
            "NER_medical_entity_recognition",
            "semantic_search_medical",
            "keyword_search",
            "feedback_learning",
            "learned_synonyms"
        ]
    }


@app.get("/health")
async def health():
    stats = feedback_db.get_stats() if feedback_db else {}
    return {
        "status": "healthy",
        "version": "7.0.0",
        "ner_loaded": ner_extractor is not None,
        "semantic_engine": semantic_engine is not None,
        "feedback_db": feedback_db is not None,
        "hybrid_search": hybrid_search is not None,
        "cie10_codes": len(catalog_manager.get_all_cie10_codes()) if catalog_manager else 0,
        "feedback_stats": stats
    }


@app.post("/api/v1/search", response_model=SymptomsResponse)
async def search_by_symptoms(request: SymptomsRequest):
    """
    BUSQUEDA CON NER (Named Entity Recognition)

    Pipeline:
    1. NER detecta entidades médicas (síntomas)
    2. Búsqueda semántica basada en entidades detectadas
    3. Re-ranking por historial de feedback

    Ejemplo:
    Input: "Tengo fiebre alta y dolor de cabeza"
    NER detecta: ["fiebre", "dolor de cabeza"]
    Retorna: códigos CIE-10 relevantes
    """
    if not hybrid_search:
        raise HTTPException(status_code=503, detail="Search engine not ready")

    import time
    start = time.time()

    result = hybrid_search.search(
        query=request.symptoms,
        patient_age=None,  # NO solicitar edad
        patient_sex=None,  # NO solicitar sexo
        max_results=request.max_results
    )

    processing_time = (time.time() - start) * 1000

    logger.info(
        f"NER Search '{request.symptoms}' detected {len(result['ner_symptoms_detected'])} symptoms, "
        f"found {len(result['results'])} results in {processing_time:.0f}ms"
    )

    cie10_results = [
        CIE10Result(
            code=r['code'],
            description=r['description'],
            relevance=r['relevance'],
            from_history=r.get('from_history', False),
            history_count=r.get('history_count', 0),
            found_by=r.get('found_by', [])
        )
        for r in result['results']
    ]

    return SymptomsResponse(
        query=request.symptoms,
        results=cie10_results,
        total_found=result['total_found'],
        has_history=result['has_history'],
        history_count=result['history_count'],
        ner_symptoms_detected=result.get('ner_symptoms_detected', [])
    )


@app.post("/api/v1/search/all")
async def search_all_catalog(request: SearchAllRequest):
    """Buscar en TODO el catálogo CIE-10"""
    if not hybrid_search:
        raise HTTPException(status_code=503, detail="Search engine not ready")

    import time
    start = time.time()

    results = hybrid_search.search_all(
        query=request.query,
        max_results=request.max_results
    )

    processing_time = (time.time() - start) * 1000

    return {
        "query": request.query,
        "results": [
            CIE10Result(
                code=r['code'],
                description=r['description'],
                relevance=r['relevance']
            )
            for r in results
        ],
        "total_found": len(results),
        "processing_time_ms": processing_time
    }


@app.post("/api/v1/feedback", response_model=FeedbackResponse)
async def save_feedback(request: FeedbackRequest):
    """
    Guardar selección + APRENDER

    El sistema:
    1. Guarda la selección en historial
    2. Aprende entidades NER asociadas al código
    3. Mejora futuras búsquedas con esa información
    """
    if not feedback_db:
        raise HTTPException(status_code=503, detail="Feedback DB not ready")

    if not catalog_manager.validate_cie10(request.selected_code):
        raise HTTPException(
            status_code=400,
            detail=f"CIE-10 invalido: {request.selected_code}"
        )

    description = request.selected_description
    if not description:
        description = catalog_manager.get_diagnosis(request.selected_code)

    success = feedback_db.save_selection(
        query=request.query,
        selected_code=request.selected_code,
        selected_description=description,
        patient_age=None,
        patient_sex=None
    )

    if success:
        learned = feedback_db.get_learned_synonyms(request.query)

        return FeedbackResponse(
            success=True,
            message=f"Aprendido: '{request.query}' -> {request.selected_code}",
            learned_synonyms=len(learned)
        )
    else:
        raise HTTPException(status_code=500, detail="Error guardando feedback")


@app.get("/api/v1/ner")
async def test_ner(query: str):
    """
    Endpoint de prueba para NER

    Muestra qué entidades detecta el extractor para un texto
    """
    if not ner_extractor:
        raise HTTPException(status_code=503, detail="NER not ready")

    symptoms = ner_extractor.extract_symptoms(query)

    return {
        "query": query,
        "symptoms_detected": [
            {
                "entity": s['entity'],
                "normalized": s['normalized'],
                "score": s['score'],
                "label": s['label']
            }
            for s in symptoms
        ],
        "total_detected": len(symptoms)
    }


@app.get("/api/v1/stats")
async def get_stats():
    """Estadísticas del sistema y aprendizaje"""
    if not feedback_db:
        raise HTTPException(status_code=503, detail="System not ready")

    return {
        "system": {
            "cie10_codes": len(catalog_manager.get_all_cie10_codes()) if catalog_manager else 0,
            "procedimientos": len(catalog_manager.get_all_procedimientos()) if catalog_manager else 0,
            "ner_model": "Custom Regex Patterns (No external model)"
        },
        "feedback_and_learning": feedback_db.get_stats()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
