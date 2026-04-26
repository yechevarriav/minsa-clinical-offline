"""
Feedback Database - Guarda selecciones del médico para mejorar el RAG
Incluye: edad, sexo del paciente y código CIE-10 seleccionado
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = "feedback.db"

def init_feedback_db():
    """Inicializa la base de datos de feedback."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            edad INTEGER,
            sexo TEXT,
            selected_code TEXT,
            selected_description TEXT,
            all_results TEXT,
            timestamp TEXT NOT NULL,
            useful INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Feedback DB inicializada")

def save_feedback(
    query: str,
    selected_code: str,
    selected_description: str,
    all_results: str,
    edad: Optional[int] = None,
    sexo: Optional[str] = None,
    useful: int = 1
):
    """Guarda el feedback del médico."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback
            (query, edad, sexo, selected_code, selected_description, all_results, timestamp, useful)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            query,
            edad,
            sexo,
            selected_code,
            selected_description,
            all_results,
            datetime.now().isoformat(),
            useful
        ))
        conn.commit()
        conn.close()
        logger.info(f"✅ Feedback guardado: {selected_code} para query: {query[:50]}")
        return True
    except Exception as e:
        logger.error(f"❌ Error guardando feedback: {e}")
        return False

def get_feedback_stats():
    """Retorna estadísticas del feedback acumulado."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT selected_code, COUNT(*) as freq FROM feedback GROUP BY selected_code ORDER BY freq DESC LIMIT 10")
        top_codes = cursor.fetchall()
        cursor.execute("SELECT AVG(edad) FROM feedback WHERE edad IS NOT NULL")
        avg_edad = cursor.fetchone()[0]
        conn.close()
        return {
            "total_feedback": total,
            "top_codes": [{"code": c, "frequency": f} for c, f in top_codes],
            "avg_patient_age": round(avg_edad, 1) if avg_edad else None
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo stats: {e}")
        return {}
