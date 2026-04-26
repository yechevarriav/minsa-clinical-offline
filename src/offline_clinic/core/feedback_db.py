"""
Feedback Database - SQLite para guardar selecciones del usuario
Sistema de aprendizaje colectivo MINSA
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class FeedbackDB:
    """
    Base de datos SQLite con APRENDIZAJE DE SINONIMOS
    """

    def __init__(self, db_path: str = ".cache/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Crear tablas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tabla 1: Historial de selecciones (re-ranking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    query_normalized TEXT NOT NULL,
                    selected_code TEXT NOT NULL,
                    selected_description TEXT,
                    patient_age INTEGER,
                    patient_sex TEXT,
                    selection_count INTEGER DEFAULT 1,
                    last_selected DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(query_normalized, selected_code)
                )
            """)

            # Tabla 2: SINONIMOS APRENDIDOS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_synonyms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_term TEXT NOT NULL,
                    medical_term TEXT NOT NULL,
                    cie10_code TEXT NOT NULL,
                    confidence INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_term, medical_term)
                )
            """)

            # Tabla 3: Mapeo query -> queries equivalentes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_equivalences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_a TEXT NOT NULL,
                    query_b TEXT NOT NULL,
                    confidence INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(query_a, query_b)
                )
            """)

            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query ON search_history(query_normalized)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_term ON learned_synonyms(user_term)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_a ON query_equivalences(query_a)")

            conn.commit()

        logger.info(f"FeedbackDB initialized at {self.db_path}")

    def save_selection(
        self,
        query: str,
        selected_code: str,
        selected_description: str,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None
    ) -> bool:
        """
        Guardar seleccion + APRENDER SINONIMOS automaticamente
        """
        query_normalized = self._normalize(query)
        now = datetime.now().isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. Guardar en historial (re-ranking)
                cursor.execute("""
                    INSERT INTO search_history
                    (query, query_normalized, selected_code, selected_description,
                     patient_age, patient_sex, last_selected)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(query_normalized, selected_code) DO UPDATE SET
                        selection_count = selection_count + 1,
                        last_selected = excluded.last_selected
                """, (
                    query, query_normalized, selected_code, selected_description,
                    patient_age, patient_sex, now
                ))

                # 2. APRENDER SINONIMOS
                self._learn_synonyms(
                    cursor,
                    query_normalized,
                    selected_code,
                    selected_description
                )

                # 3. Aprender queries equivalentes
                self._learn_query_equivalences(
                    cursor,
                    query_normalized,
                    selected_code
                )

                conn.commit()

                logger.info(
                    f"Saved feedback + learned: '{query}' -> {selected_code}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            return False

    def _learn_synonyms(
        self,
        cursor: sqlite3.Cursor,
        query_normalized: str,
        selected_code: str,
        selected_description: str
    ):
        """
        APRENDER SINONIMOS automaticamente
        """
        if not selected_description:
            return

        # Extraer palabras clave del query del usuario
        user_words = self._extract_keywords(query_normalized)

        # Extraer palabras medicas de la descripcion CIE-10
        description_clean = re.sub(r'^[A-Z]\d+\w*\s*-\s*', '', selected_description)
        description_normalized = self._normalize(description_clean.lower())
        medical_words = self._extract_keywords(description_normalized)

        # Crear pares (palabra_usuario -> palabra_medica)
        for user_word in user_words:
            for medical_word in medical_words:
                if user_word != medical_word and len(user_word) >= 3 and len(medical_word) >= 3:
                    try:
                        cursor.execute("""
                            INSERT INTO learned_synonyms
                            (user_term, medical_term, cie10_code)
                            VALUES (?, ?, ?)
                            ON CONFLICT(user_term, medical_term) DO UPDATE SET
                                confidence = confidence + 1
                        """, (user_word, medical_word, selected_code))
                    except Exception as e:
                        logger.debug(f"Sinónimo skip: {e}")

    def _learn_query_equivalences(
        self,
        cursor: sqlite3.Cursor,
        query_normalized: str,
        selected_code: str
    ):
        """
        Aprender que dos queries diferentes pueden referirse al mismo codigo
        """
        try:
            # Buscar otras queries que llevaron al mismo codigo
            cursor.execute("""
                SELECT DISTINCT query_normalized
                FROM search_history
                WHERE selected_code = ? AND query_normalized != ?
            """, (selected_code, query_normalized))

            equivalent_queries = [row[0] for row in cursor.fetchall()]

            # Crear equivalencias
            for other_query in equivalent_queries:
                # Ordenar para evitar duplicados (a < b)
                q_a, q_b = sorted([query_normalized, other_query])

                cursor.execute("""
                    INSERT INTO query_equivalences (query_a, query_b)
                    VALUES (?, ?)
                    ON CONFLICT(query_a, query_b) DO UPDATE SET
                        confidence = confidence + 1
                """, (q_a, q_b))

        except Exception as e:
            logger.debug(f"Equivalence skip: {e}")

    def get_history_for_query(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict]:
        """Obtener codigos previamente seleccionados para una query"""
        query_normalized = self._normalize(query)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        selected_code,
                        selected_description,
                        selection_count,
                        last_selected
                    FROM search_history
                    WHERE query_normalized = ?
                    ORDER BY selection_count DESC, last_selected DESC
                    LIMIT ?
                """, (query_normalized, limit))

                return [
                    {
                        'code': row['selected_code'],
                        'description': row['selected_description'],
                        'selection_count': row['selection_count'],
                        'last_selected': row['last_selected']
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def get_learned_synonyms(self, query: str, min_confidence: int = 1) -> List[str]:
        """
        Obtener SINONIMOS APRENDIDOS para una query
        """
        query_normalized = self._normalize(query)
        words = self._extract_keywords(query_normalized)

        if not words:
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Buscar sinonimos para cada palabra
                placeholders = ','.join(['?'] * len(words))
                cursor.execute(f"""
                    SELECT DISTINCT medical_term, SUM(confidence) as total_conf
                    FROM learned_synonyms
                    WHERE user_term IN ({placeholders})
                    GROUP BY medical_term
                    HAVING total_conf >= ?
                    ORDER BY total_conf DESC
                    LIMIT 20
                """, words + [min_confidence])

                synonyms = [row[0] for row in cursor.fetchall()]

                if synonyms:
                    logger.info(f"Learned synonyms for '{query}': {synonyms[:5]}")

                return synonyms

        except Exception as e:
            logger.error(f"Failed to get synonyms: {e}")
            return []

    def get_equivalent_queries(self, query: str, min_confidence: int = 1) -> List[str]:
        """Obtener queries equivalentes aprendidas"""
        query_normalized = self._normalize(query)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        CASE
                            WHEN query_a = ? THEN query_b
                            ELSE query_a
                        END as equivalent,
                        confidence
                    FROM query_equivalences
                    WHERE (query_a = ? OR query_b = ?) AND confidence >= ?
                    ORDER BY confidence DESC
                    LIMIT 10
                """, (query_normalized, query_normalized, query_normalized, min_confidence))

                return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get equivalent queries: {e}")
            return []

    def get_stats(self) -> Dict:
        """Estadisticas del feedback y aprendizaje"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM search_history")
                total_records = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT query_normalized) FROM search_history")
                unique_queries = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM learned_synonyms")
                total_synonyms = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM query_equivalences")
                total_equivalences = cursor.fetchone()[0]

                cursor.execute("SELECT SUM(selection_count) FROM search_history")
                total_selections = cursor.fetchone()[0] or 0

                return {
                    'total_records': total_records,
                    'unique_queries': unique_queries,
                    'total_selections': total_selections,
                    'learned_synonyms': total_synonyms,
                    'learned_equivalences': total_equivalences
                }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def _normalize(self, text: str) -> str:
        """Lowercase + sin tildes"""
        text = text.lower().strip()
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _extract_keywords(self, text: str) -> List[str]:
        """Extraer palabras clave (sin stopwords)"""
        stopwords = {
            'de', 'la', 'el', 'en', 'con', 'por', 'para', 'y', 'o', 'del',
            'a', 'los', 'las', 'un', 'una', 'muy', 'mas', 'menos', 'que',
            'se', 'es', 'no', 'si', 'me', 'mi', 'le', 'lo', 'al', 'su',
            'no', 'otra', 'otro', 'sin', 'con', 'segun', 'tal', 'tan',
            'o', 'u', 'e', 'i'
        }

        # Quitar caracteres especiales y dividir
        words = re.findall(r'\b[a-z]+\b', text.lower())

        # Filtrar stopwords y palabras muy cortas
        return [w for w in words if w not in stopwords and len(w) >= 3]
