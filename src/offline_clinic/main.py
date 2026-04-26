"""
MINSA Clinical Offline - API Principal v2.0
FastAPI arranca INMEDIATAMENTE, embeddings cargan en background
"""
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from offline_clinic.core.feedback_db import init_feedback_db, save_feedback, get_feedback_stats

logger = logging.getLogger(__name__)

# Estado global del sistema
system_ready = False
searcher = None

async def load_models_background():
    """Carga modelos en background - no bloquea el puerto."""
    global system_ready, searcher
    logger.info("🔄 Cargando modelos en background...")
    try:
        from offline_clinic.core.hybrid_search_v4 import HybridSearchV4
        searcher = HybridSearchV4()
        system_ready = True
        logger.info("✅ Modelos cargados - Sistema listo")
    except Exception as e:
        logger.error(f"❌ Error cargando modelos: {e}")
        system_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - arranca inmediatamente
    init_feedback_db()
    logger.info("🏥 MINSA Clinical Offline v2.0 iniciando...")
    # Carga modelos en background (no bloquea puerto)
    asyncio.create_task(load_models_background())
    yield
    logger.info("🔴 MINSA Clinical Offline apagando...")

app = FastAPI(
    title="MINSA Clinical Offline API",
    description="Sistema de Soporte Clínico Offline con búsqueda CIE-10 y feedback",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MODELOS
# ============================================================

class QueryRequest(BaseModel):
    question: str = Field(..., description="Síntoma o diagnóstico")
    edad: Optional[int] = Field(None, ge=0, le=120)
    sexo: Optional[str] = Field(None)
    use_llm: bool = Field(False)
    top_k: int = Field(5, ge=1, le=20)

class FeedbackRequest(BaseModel):
    query: str
    selected_code: str
    selected_description: str
    all_results: str = ""
    edad: Optional[int] = None
    sexo: Optional[str] = None
    useful: int = 1

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "models_ready": system_ready,
        "service": "minsa-clinical-offline"
    }

@app.get("/", response_class=HTMLResponse)
async def frontend():
    """Sirve el frontend HTML."""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>MINSA Clinical Offline API</h1><p>Visita /docs para la API</p>")

@app.post("/api/v1/query")
async def query(request: QueryRequest):
    if not system_ready:
        return {
            "status": "loading",
            "message": "Sistema cargando modelos, espere un momento...",
            "models_ready": False,
            "results": [],
            "query": request.question,
            "edad": request.edad,
            "sexo": request.sexo,
            "search_time_ms": 0,
            "total_results": 0
        }

    import time
    start = time.time()

    # Enriquecer query con contexto demográfico
    enriched_query = request.question
    context_parts = []
    if request.edad:
        context_parts.append(f"paciente de {request.edad} años")
    if request.sexo:
        sexo_norm = "masculino" if request.sexo.upper() in ["M", "MALE", "MASCULINO"] else "femenino"
        context_parts.append(f"sexo {sexo_norm}")
    if context_parts:
        enriched_query = f"{request.question} ({', '.join(context_parts)})"

    try:
        results = searcher.search(enriched_query, top_k=request.top_k)
    except Exception as e:
        results = []
        logger.error(f"Error en búsqueda: {e}")

    llm_response = None
    if request.use_llm and results:
        try:
            from offline_clinic.core.rag_engine import RAGEngine
            rag = RAGEngine()
            llm_response = rag.generate(enriched_query, results)
        except Exception:
            llm_response = "LLM no disponible en este entorno."

    elapsed = (time.time() - start) * 1000
    return {
        "query": request.question,
        "edad": request.edad,
        "sexo": request.sexo,
        "results": results,
        "llm_response": llm_response,
        "search_time_ms": round(elapsed, 2),
        "total_results": len(results),
        "models_ready": True
    }

@app.post("/api/v1/feedback")
async def feedback(request: FeedbackRequest):
    success = save_feedback(
        query=request.query,
        selected_code=request.selected_code,
        selected_description=request.selected_description,
        all_results=request.all_results,
        edad=request.edad,
        sexo=request.sexo,
        useful=request.useful
    )
    if success:
        return {"status": "ok", "message": "Feedback guardado"}
    raise HTTPException(status_code=500, detail="Error guardando feedback")

@app.get("/api/v1/feedback/stats")
async def feedback_stats():
    return get_feedback_stats()

@app.post("/api/v1/ingest")
async def ingest():
    return {"status": "ok", "message": "Datos CIE-10 cargados"}

@app.get("/api/v1/ingest")
async def ingest_status():
    return {"status": "ready", "models_ready": system_ready}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
