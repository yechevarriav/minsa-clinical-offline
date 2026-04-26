"""
feedback_db.py - MINSA Clinical Offline
Versión actualizada: mantiene funciones sueltas + agrega clase FeedbackDB
compatible con HybridSearchV4
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

DB_PATH = "feedback.db"

# ============================================================
# FUNCIONES SUELTAS (compatibilidad con main.py)
# ============================================================

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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            code TEXT NOT NULL,
            selection_count INTEGER DEFAULT 1,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS synonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            synonym TEXT NOT NULL,
            confidence INTEGER DEFAULT 1,
            timestamp TEXT NOT NULL
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
        """, (query, edad, sexo, selected_code, selected_description,
              all_results, datetime.now().isoformat(), useful))
        # También guarda en historial
        cursor.execute("""
            INSERT INTO query_history (query, code, selection_count, timestamp)
            VALUES (?, ?, 1, ?)
        """, (query, selected_code, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.info(f"✅ Feedback guardado: {selected_code}")
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
        cursor.execute("""
            SELECT selected_code, COUNT(*) as freq
            FROM feedback
            GROUP BY selected_code
            ORDER BY freq DESC LIMIT 10
        """)
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


# ============================================================
# CLASE FeedbackDB (requerida por HybridSearchV4)
# ============================================================

class FeedbackDB:
    """
    Clase FeedbackDB compatible con HybridSearchV4.
    Provee métodos para historial de selecciones y sinónimos aprendidos.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa las tablas necesarias."""
        conn = sqlite3.connect(self.db_path)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                code TEXT NOT NULL,
                selection_count INTEGER DEFAULT 1,
                timestamp TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                synonym TEXT NOT NULL,
                confidence INTEGER DEFAULT 1,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def get_history_for_query(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Retorna historial de códigos seleccionados para una query similar.
        Requerido por HybridSearchV4.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT code, SUM(selection_count) as total
                FROM query_history
                WHERE query LIKE ?
                GROUP BY code
                ORDER BY total DESC
                LIMIT ?
            """, (f"%{query[:20]}%", limit))
            rows = cursor.fetchall()
            conn.close()
            return [{"code": r[0], "selection_count": r[1]} for r in rows]
        except Exception as e:
            logger.warning(f"get_history_for_query error: {e}")
            return []

    def get_learned_synonyms(self, query: str, min_confidence: int = 1) -> List[str]:
        """
        Retorna sinónimos aprendidos para una query.
        Requerido por HybridSearchV4.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT synonym FROM synonyms
                WHERE query LIKE ? AND confidence >= ?
                LIMIT 10
            """, (f"%{query[:20]}%", min_confidence))
            rows = cursor.fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception as e:
            logger.warning(f"get_learned_synonyms error: {e}")
            return []

    def get_equivalent_queries(self, query: str, min_confidence: int = 1) -> List[str]:
        """
        Retorna queries equivalentes aprendidas.
        Requerido por HybridSearchV4.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT query FROM query_history
                WHERE query LIKE ? AND query != ?
                LIMIT 5
            """, (f"%{query[:10]}%", query))
            rows = cursor.fetchall()
            conn.close()
            return [r[0] for r in rows]
        except Exception as e:
            logger.warning(f"get_equivalent_queries error: {e}")
            return []

    def save(self, query: str, selected_code: str, selected_description: str,
             edad: Optional[int] = None, sexo: Optional[str] = None):
        """Guarda una selección del médico."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback
                (query, edad, sexo, selected_code, selected_description, all_results, timestamp)
                VALUES (?, ?, ?, ?, ?, '', ?)
            """, (query, edad, sexo, selected_code, selected_description,
                  datetime.now().isoformat()))
            cursor.execute("""
                INSERT INTO query_history (query, code, selection_count, timestamp)
                VALUES (?, ?, 1, ?)
            """, (query, selected_code, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"FeedbackDB.save error: {e}")
            return False
