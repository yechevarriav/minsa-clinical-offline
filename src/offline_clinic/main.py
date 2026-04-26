"""
FastAPI Main Application - Sistema de Soporte Clinico MINSA
Version 8.0 - Con RAG Pipeline (Retrieval-Augmented Generation)
Endpoints: /query (RAG), /ingest (documentos), /health
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import logging
import json
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
rag_engine = None


# ============================================================================
# SCHEMAS
# ============================================================================

class QueryRequest(BaseModel):
    question: str = Field(..., description="Pregunta clínica en lenguaje natural")
    use_llm: Optional[bool] = Field(default=True, description="Usar Llama-2 LLM")


class QueryResponse(BaseModel):
    question: str
    retrieved_codes: List[dict]
    context: str
    llm_response: Optional[str]
    metrics: dict
    timestamp: str


class IngestRequest(BaseModel):
    title: str = Field(..., description="Título del documento")
    content: str = Field(..., description="Contenido del documento")


class IngestResponse(BaseModel):
    status: str
    document_id: str
    title: str
    content_length: int


class HealthResponse(BaseModel):
    status: str
    version: str
    components: dict
    rag_engine: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    global catalog_manager, semantic_engine, feedback_db, hybrid_search, ner_extractor, rag_engine

    logger.info("Initializing Soporte Clinico Offline V8.0 (with RAG)...")

    try:
        from offline_clinic.core.excel_loader_minsa import CatalogManager
        from offline_clinic.core.semantic_search_medical import MedicalSemanticSearchEngine
        from offline_clinic.core.feedback_db import FeedbackDB
        from offline_clinic.core.hybrid_search_v4 import HybridSearchV4
        from offline_clinic.core.ner_extractor import MedicalNERExtractor
        from offline_clinic.core.rag_engine import RAGEngine

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

        # 5. Motor híbrido
        hybrid_search = HybridSearchV4(catalog_manager, semantic_engine, feedback_db, ner_extractor)

        # 6. RAG ENGINE (NUEVO!)
        logger.info("Initializing RAG Engine...")
        rag_engine = RAGEngine(hybrid_search, ollama_base_url="http://localhost:11434")

        logger.info("System ready!")

    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise

    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Sistema de Soporte Clinico Offline",
    description="MINSA Peru - RAG + Llama-2 + NER",
    version="8.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "Sistema de Soporte Clinico MINSA",
        "version": "8.0.0",
        "features": [
            "NER_medical_entity_recognition",
            "RAG_retrieval_augmented_generation",
            "Llama2_LLM_inference",
            "semantic_search_medical",
            "feedback_learning"
        ],
        "endpoints": {
            "query": "POST /api/v1/query - RAG pipeline (búsqueda + LLM)",
            "ingest": "POST /api/v1/ingest - Ingerir documentos",
            "health": "GET /health - Estado del sistema",
            "metrics": "GET /api/v1/metrics - Métricas del RAG"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Estado del sistema y componentes"""

    # Verificar Ollama
    ollama_available = rag_engine._verify_ollama() if rag_engine else False

    return HealthResponse(
        status="healthy",
        version="8.0.0",
        components={
            "catalog_loaded": catalog_manager is not None,
            "ner_loaded": ner_extractor is not None,
            "semantic_engine": semantic_engine is not None,
            "feedback_db": feedback_db is not None,
            "hybrid_search": hybrid_search is not None,
            "cie10_codes": len(catalog_manager.get_all_cie10_codes()) if catalog_manager else 0,
        },
        rag_engine={
            "loaded": rag_engine is not None,
            "ollama_available": ollama_available,
            "model": "llama2:7b"
        }
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def rag_query(request: QueryRequest):
    """
    PIPELINE RAG COMPLETO

    1. Retrieval: Busca CIE-10 relevantes con NER + búsqueda semántica
    2. Augmented: Construye contexto clínico
    3. Generation: Llama-2 genera respuesta basada en CIE-10

    Ejemplo:
    ```json
    {
        "question": "¿Qué hacer si el paciente tiene fiebre y tos?",
        "use_llm": true
    }
    ```

    Respuesta:
    ```json
    {
        "question": "¿Qué hacer si el paciente tiene fiebre y tos?",
        "retrieved_codes": [
            {"code": "R50", "description": "FIEBRE", "relevance": 0.92},
            {"code": "R05", "description": "TOS", "relevance": 0.85}
        ],
        "context": "...",
        "llm_response": "Basándose en los códigos CIE-10 identificados...",
        "metrics": {...}
    }
    ```
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    import time
    start = time.time()

    try:
        result = rag_engine.query(
            question=request.question,
            top_k=5,
            use_llm=request.use_llm
        )

        processing_time = (time.time() - start) * 1000

        logger.info(
            f"RAG Query completed in {processing_time:.0f}ms - "
            f"Retrieved {len(result['retrieved_codes'])} codes, "
            f"LLM: {result['llm_response'] is not None}"
        )

        return QueryResponse(
            question=result['question'],
            retrieved_codes=result['retrieved_codes'],
            context=result['context'],
            llm_response=result['llm_response'],
            metrics=result['metrics'],
            timestamp=result['timestamp']
        )

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    """
    Ingerir documento clínico (protocolo, guía, manual)

    Para E3, esto prepara documentos para indexación futura
    en motores como Elasticsearch o Pinecone.

    Ejemplo:
    ```json
    {
        "title": "Protocolo MINSA - Manejo de Fiebre en Niños",
        "content": "..."
    }
    ```
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    try:
        result = rag_engine.ingest_document(
            title=request.title,
            content=request.content
        )

        return IngestResponse(
            status=result['status'],
            document_id=result['document_id'],
            title=result['title'],
            content_length=result['content_length']
        )

    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
async def get_metrics():
    """
    Reporte de métricas del RAG

    Devuelve:
    - total_queries: Número total de queries procesadas
    - avg_elapsed_time_seconds: Tiempo promedio de query
    - avg_relevance: Relevancia promedio de CIE-10 recuperados
    - llm_success_rate: Porcentaje de queries donde LLM generó respuesta
    - metrics_by_query: Detalles de cada query
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not ready")

    metrics_report = rag_engine.get_metrics_report()

    return {
        "status": "ok",
        "metrics": metrics_report,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


@app.get("/api/v1/stats")
async def get_stats():
    """Estadísticas del sistema y feedback"""
    if not feedback_db:
        raise HTTPException(status_code=503, detail="System not ready")

    return {
        "system": {
            "cie10_codes": len(catalog_manager.get_all_cie10_codes()) if catalog_manager else 0,
            "procedimientos": len(catalog_manager.get_all_procedimientos()) if catalog_manager else 0,
            "ner_patterns": 13,
            "embedding_model": "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es",
            "llm_model": "llama2:7b (via Ollama)"
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
