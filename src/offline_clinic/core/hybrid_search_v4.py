"""
Hybrid Search Engine V4 - CON NER
Búsqueda inteligente basada en entidades médicas detectadas
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class HybridSearchV4:
    """
    Motor de búsqueda que usa NER para entender mejor lo que pide el usuario

    Score = (semantic * 0.30) + (ner_entities * 0.40) + (keywords * 0.15) + (history * 0.15)

    NER tiene mayor peso porque ya sabemos que son entidades médicas relevantes
    """

    BASIC_SYNONYMS = {
        'fiebre': ['febril', 'calentura', 'hipertermia', 'pirexia', 'temperatura'],
        'dolor de cabeza': ['cefalea', 'migrana', 'jaqueca', 'cefalalgia'],
        'cefalea': ['dolor de cabeza', 'migrana', 'jaqueca'],
        'tos': ['tusigeno', 'bronquitis', 'tosiendo'],
        'dificultad respiratoria': ['disnea', 'falta de aire', 'ahogo', 'asma'],
        'disnea': ['falta de aire', 'dificultad respiratoria', 'asma'],
        'dolor abdominal': ['gastralgia', 'dolor de estomago', 'dispepsia'],
        'nausea': ['mareo', 'vomito', 'nauseas', 'arcadas'],
        'vomito': ['emesis', 'nausea', 'vomitar', 'arcadas'],
        'erupcion': ['rash', 'eruption cutanea', 'dermatitis', 'urticaria'],
        'mareo': ['vertigo', 'mareos', 'aturdimiento'],
    }

    def __init__(self, catalog_manager, semantic_engine, feedback_db, ner_extractor):
        self.catalog = catalog_manager
        self.semantic = semantic_engine
        self.feedback = feedback_db
        self.ner = ner_extractor
        self.all_codes = catalog_manager.cie10_loader.codes_dict

        logger.info("Hybrid Search V4 (with NER) initialized")

    def search(
        self,
        query: str,
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
        max_results: int = 10
    ) -> Dict:
        """
        Búsqueda inteligente con NER
        """
        query_clean = query.lower().strip()
        query_normalized = self._normalize(query_clean)

        # 1. EXTRAER ENTIDADES MEDICAS (NER)
        ner_symptoms = self.ner.extract_symptoms(query)
        logger.info(f"NER detected {len(ner_symptoms)} symptoms")

        # 2. Historial de feedback
        history = self.feedback.get_history_for_query(query, limit=5)
        history_codes = {h['code']: h['selection_count'] for h in history}

        # 3. Sinónimos aprendidos
        learned_synonyms = self.feedback.get_learned_synonyms(query, min_confidence=1)
        equivalent_queries = self.feedback.get_equivalent_queries(query, min_confidence=1)

        # 4. Construir queries expandidas (original + NER + learned)
        expanded_terms = self._build_expanded_query(
            query_clean,
            ner_symptoms,
            learned_synonyms,
            equivalent_queries
        )

        logger.info(f"Expanded query terms: {expanded_terms[:8]}")

        # 5. Búsqueda semántica con términos expandidos
        expanded_query = " ".join(expanded_terms[:10])
        semantic_results = self.semantic.search(expanded_query, top_k=30, min_score=0.3)
        semantic_scores = {r['code']: r['score'] for r in semantic_results}

        # 6. BÚSQUEDA POR ENTIDADES NER (NUEVA! - Mayor peso)
        ner_scores = self._search_by_ner_entities(ner_symptoms)

        # 7. Búsqueda por keywords
        keyword_scores = self._keyword_search(
            query_clean,
            query_normalized,
            ner_symptoms,
            learned_synonyms,
            equivalent_queries
        )

        # 8. Combinar scores
        combined_scores = {}
        all_candidates = set()
        all_candidates.update(semantic_scores.keys())
        all_candidates.update(ner_scores.keys())
        all_candidates.update(keyword_scores.keys())
        all_candidates.update(history_codes.keys())

        for code in all_candidates:
            semantic = semantic_scores.get(code, 0.0)
            ner = ner_scores.get(code, 0.0)  # NER tiene mayor peso
            keyword = keyword_scores.get(code, 0.0)
            history_boost = min(history_codes.get(code, 0) * 0.2, 1.0)

            # Score combinado - NER al frente
            combined = (
                ner * 0.40 +           # NER es MUY CONFIABLE (sabemos que es síntoma)
                semantic * 0.30 +      # Semántica segunda
                keyword * 0.15 +       # Keywords tercero
                history_boost * 0.15   # Historial cuarto
            )

            combined_scores[code] = combined

        # 9. Ordenar
        sorted_codes = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 10. Formatear resultados
        results = []
        for code, score in sorted_codes[:max_results]:
            description = self.all_codes.get(code, "")
            from_history = code in history_codes
            history_count = history_codes.get(code, 0)

            # Determinar qué método lo encontró (para debugging)
            found_by = []
            if ner_scores.get(code, 0) > 0:
                found_by.append("NER")
            if semantic_scores.get(code, 0) > 0:
                found_by.append("semantic")
            if history_codes.get(code, 0) > 0:
                found_by.append("history")

            results.append({
                'code': code,
                'description': description,
                'relevance': round(score, 3),
                'score': round(score, 3),
                'from_history': from_history,
                'history_count': history_count,
                'found_by': found_by
            })

        return {
            'results': results,
            'has_history': len(history) > 0,
            'history_count': len(history),
            'ner_symptoms_detected': [s['entity'] for s in ner_symptoms],
            'total_found': len(results)
        }

    def search_all(self, query: str, max_results: int = 50) -> List[Dict]:
        """Buscar en TODO el catálogo"""
        query_normalized = self._normalize(query.lower().strip())

        results = []
        for code, description in self.all_codes.items():
            desc_normalized = self._normalize(description.lower())

            score = 0.0

            words = [w for w in query_normalized.split() if len(w) >= 3]
            for word in words:
                if word in desc_normalized:
                    score += 1.0

            if query_normalized in desc_normalized:
                score += 3.0

            if score > 0:
                results.append({
                    'code': code,
                    'description': description,
                    'relevance': round(score, 3)
                })

        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:max_results]

    def _search_by_ner_entities(self, ner_symptoms: List[Dict]) -> Dict[str, float]:
        """
        BÚSQUEDA DIRECTA POR ENTIDADES NER (NUEVO!)

        Si NER detectó "fiebre", buscamos códigos CIE-10 que contengan
        la palabra "fiebre" o sus sinónimos directamente.

        Este es el método MÁS CONFIABLE porque sabemos 100% que es síntoma.
        """
        scores = {}

        for symptom in ner_symptoms:
            entity = symptom['entity'].lower()
            normalized = symptom['normalized']
            confidence = symptom['score']  # Score del modelo NER

            # Expandir con sinónimos
            synonyms = self.BASIC_SYNONYMS.get(normalized, [])
            search_terms = [normalized] + [self._normalize(s) for s in synonyms]

            # Buscar en CIE-10
            for code, description in self.all_codes.items():
                desc_normalized = self._normalize(description.lower())

                score = 0.0

                # Búsqueda de términos
                for term in search_terms:
                    if term in desc_normalized:
                        # El score depende del confidence del NER
                        score += confidence

                if score > 0:
                    # Boost si es palabra exacta al inicio
                    if desc_normalized.startswith(normalized):
                        score += confidence * 0.5

                    if code not in scores:
                        scores[code] = score
                    else:
                        scores[code] += score

        return scores

    def _build_expanded_query(
        self,
        query: str,
        ner_symptoms: List[Dict],
        learned_synonyms: List[str],
        equivalent_queries: List[str]
    ) -> List[str]:
        """Construir lista expandida de términos para búsqueda semántica"""
        terms = [query]

        # Añadir entidades NER detectadas
        for symptom in ner_symptoms:
            terms.append(symptom['entity'])
            terms.append(symptom['normalized'])

        # Sinónimos básicos
        for symptom in ner_symptoms:
            normalized = symptom['normalized']
            if normalized in self.BASIC_SYNONYMS:
                terms.extend(self.BASIC_SYNONYMS[normalized][:3])

        # Sinónimos aprendidos
        terms.extend(learned_synonyms[:8])

        # Queries equivalentes
        terms.extend(equivalent_queries[:5])

        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_terms = []
        for term in terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)

        return unique_terms

    def _keyword_search(
        self,
        query: str,
        query_normalized: str,
        ner_symptoms: List[Dict],
        learned_synonyms: List[str],
        equivalent_queries: List[str]
    ) -> Dict[str, float]:
        """Búsqueda por keywords mejorada con NER"""
        scores = {}

        # Construir lista de términos
        terms = [query]
        terms.extend([s['entity'].lower() for s in ner_symptoms])
        terms.extend([s['normalized'] for s in ner_symptoms])
        terms.extend(learned_synonyms[:10])
        terms.extend(equivalent_queries[:5])

        terms_normalized = [self._normalize(t) for t in terms]

        for code, description in self.all_codes.items():
            desc_normalized = self._normalize(description.lower())
            score = 0.0

            # Query exacto
            if query_normalized in desc_normalized:
                position = desc_normalized.find(query_normalized)
                position_bonus = 1.0 - (position / max(len(desc_normalized), 1)) * 0.3
                score += 1.5 * position_bonus

            # Términos
            for term in terms_normalized:
                if term != query_normalized and term in desc_normalized:
                    score += 0.7

            # Palabras individuales
            words = [w for w in query_normalized.split() if len(w) >= 3]
            for word in words:
                if word in desc_normalized:
                    score += 0.2

            if score > 0:
                scores[code] = score

        return scores

    def _normalize(self, text: str) -> str:
        """Normalizar texto"""
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
