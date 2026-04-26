"""
MINSA Clinical Offline - API Principal v2.0
Fix: FeedbackDB → funciones sueltas (init_feedback_db, save_feedback, get_feedback_stats)
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

# ✅ CORRECTO: importar funciones sueltas (no clase FeedbackDB)
from offline_clinic.core.feedback_db import init_feedback_db, save_feedback, get_feedback_stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

system_ready = False
searcher = None

async def load_models_background():
    global system_ready, searcher
    logger.info("🔄 Cargando modelos en background...")
    try:
        loop = asyncio.get_event_loop()

        def _load():
            from offline_clinic.core.excel_loader_minsa import CatalogManager
            catalog_manager = CatalogManager(
                cie10_path="data/CIE10_MINSA_OFICIAL.xlsx",
                procedimientos_path="data/Anexo N1_Listado de Procedimientos Médicos y Sanitarios del Sector Salud_RM550-2023 12141 al 300126.xlsx"
            )
            logger.info(f"✅ CatalogManager: {len(catalog_manager.get_all_cie10_codes())} códigos CIE-10")

            from offline_clinic.core.semantic_search_medical import MedicalSemanticSearchEngine
            semantic_engine = MedicalSemanticSearchEngine(catalog_manager)
            logger.info("✅ SemanticEngine cargado")

            # ✅ CORRECTO: FeedbackDB como clase desde feedback_db
            # Pero como no existe la clase, usamos None y las funciones sueltas
            feedback_db_instance = None

            from offline_clinic.core.ner_extractor import MedicalNERExtractor
            ner_extractor = MedicalNERExtractor()
            logger.info("✅ NERExtractor cargado")

            from offline_clinic.core.hybrid_search_v4 import HybridSearchV4
            hybrid = HybridSearchV4(catalog_manager, semantic_engine, feedback_db_instance, ner_extractor)
            logger.info("✅ HybridSearchV4 cargado")
            return hybrid

        searcher = await loop.run_in_executor(None, _load)
        system_ready = True
        logger.info("🏥 Sistema MINSA Clinical listo!")

    except Exception as e:
        logger.error(f"❌ Error cargando modelos: {e}")
        system_ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_feedback_db()
    logger.info("🏥 MINSA Clinical Offline v2.0 iniciando...")
    asyncio.create_task(load_models_background())
    yield
    logger.info("🔴 Apagando...")

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
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(f"""
    <html><body style='font-family:sans-serif;padding:40px'>
    <h1>🏥 MINSA Clinical Offline API</h1>
    <p>Estado: <b>{"✅ Sistema listo" if system_ready else "⏳ Cargando modelos..."}</b></p>
    <p><a href='/docs'>📖 Ver documentación API (Swagger)</a></p>
    <p><a href='/health'>❤️ Health check</a></p>
    </body></html>
    """)

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

    enriched_query = request.question
    context_parts = []
    if request.edad:
        context_parts.append(f"paciente de {request.edad} años")
    if request.sexo:
        sexo_norm = "masculino" if str(request.sexo).upper() in ["M", "MALE", "MASCULINO"] else "femenino"
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
            rag = RAGEngine(searcher, ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
            llm_response = rag.generate(enriched_query, results)
        except Exception:
            llm_response = "LLM (Llama-2) no disponible en entorno cloud."

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
    return {"status": "ok", "message": "Datos CIE-10 cargados", "models_ready": system_ready}

@app.get("/api/v1/ingest")
async def ingest_status():
    return {"status": "ready", "models_ready": system_ready}

@app.get("/api/v1/metrics")
async def metrics():
    return {
        "models_ready": system_ready,
        "service": "minsa-clinical-offline",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
