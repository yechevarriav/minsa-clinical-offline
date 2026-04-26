"""
RAG Engine - Retrieval-Augmented Generation para consultas clínicas
Combina: Búsqueda en CIE-10 + Llama-2 via Ollama
"""

import logging
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Motor RAG para consultas clínicas

    Pipeline:
    1. Usuario pregunta: "¿Qué hacer si el paciente tiene fiebre y tos?"
    2. Retrieval: Buscar CIE-10 relevantes (búsqueda semántica)
    3. Augmented: Pasar contexto al LLM
    4. Generation: Llama-2 genera respuesta clínica
    5. Métricas: Guardar evaluación del LLM
    """

    def __init__(
        self,
        hybrid_search,
        ollama_base_url: str = "http://localhost:11434"
    ):
        """
        Args:
            hybrid_search: Motor de búsqueda híbrida (NER + semántica)
            ollama_base_url: URL del servidor Ollama con Llama-2
        """
        self.search = hybrid_search
        self.ollama_url = ollama_base_url
        self.model = "llama2:7b"
        self.metrics = []

        # Verificar que Ollama está disponible
        self._verify_ollama()

        logger.info(f"RAG Engine initialized (Ollama: {ollama_base_url})")

    def _verify_ollama(self):
        """Verificar que Ollama está corriendo"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info("✓ Ollama is running and accessible")
                return True
            else:
                logger.warning(f"⚠️ Ollama returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Cannot connect to Ollama at {self.ollama_url}")
            logger.error("Make sure Ollama is running: ollama serve")
            return False
        except Exception as e:
            logger.error(f"✗ Error verifying Ollama: {e}")
            return False

    def query(
        self,
        question: str,
        top_k: int = 5,
        use_llm: bool = True
    ) -> Dict:
        """
        Pipeline RAG completo

        Args:
            question: Pregunta clínica del usuario
            top_k: Número de CIE-10 a recuperar
            use_llm: Si False, solo devuelve contexto (sin LLM)

        Returns:
            {
                'question': str,
                'retrieved_codes': List[Dict],  # CIE-10 recuperados
                'context': str,                  # Contexto formateado
                'llm_response': str,            # Respuesta de Llama-2
                'metrics': Dict,                # Métricas de evaluación
                'timestamp': str
            }
        """
        start_time = datetime.now()

        logger.info(f"RAG Query: '{question}'")

        # 1. RETRIEVAL: Buscar CIE-10 relevantes
        logger.info("Step 1: Retrieval (searching CIE-10)...")
        retrieved = self.search.search(question, max_results=top_k)
        retrieved_codes = retrieved['results']

        logger.info(f"  Retrieved {len(retrieved_codes)} CIE-10 codes")

        # 2. AUGMENTED: Construir contexto
        logger.info("Step 2: Augmented (building context)...")
        context = self._build_context(question, retrieved_codes)

        # 3. GENERATION: Llamar a Llama-2
        logger.info("Step 3: Generation (calling Llama-2)...")

        if use_llm:
            llm_response = self._generate_response(question, context)
        else:
            llm_response = None

        # 4. Calcular métricas
        elapsed_time = (datetime.now() - start_time).total_seconds()
        metrics = self._calculate_metrics(
            question=question,
            retrieved_codes=retrieved_codes,
            context=context,
            llm_response=llm_response,
            elapsed_time=elapsed_time
        )

        # Guardar métrica para reporte
        self.metrics.append(metrics)

        result = {
            'question': question,
            'retrieved_codes': [
                {
                    'code': r['code'],
                    'description': r['description'],
                    'relevance': r['relevance']
                }
                for r in retrieved_codes
            ],
            'context': context,
            'llm_response': llm_response,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"✓ RAG query completed in {elapsed_time:.2f}s")

        return result

    def _build_context(
        self,
        question: str,
        retrieved_codes: List[Dict]
    ) -> str:
        """
        Construir contexto para el LLM a partir de CIE-10 recuperados

        Formato:
        ```
        PREGUNTA CLÍNICA:
        ¿Qué hacer si el paciente tiene fiebre y tos?

        CÓDIGOS CIE-10 RELEVANTES:
        1. R50 - FIEBRE (relevancia: 0.92)
        2. R05 - TOS (relevancia: 0.85)
        ...

        PROTOCOLOS MINSA:
        - Para fiebre: [protocolo]
        - Para tos: [protocolo]
        ```
        """
        context = f"""PREGUNTA CLÍNICA:
{question}

CÓDIGOS CIE-10 RELEVANTES ENCONTRADOS:
"""

        for i, code in enumerate(retrieved_codes, 1):
            context += f"\n{i}. {code['code']} - {code['description']}"
            context += f"\n   (Relevancia: {code['relevance']:.2f})"

        context += """

INSTRUCCIONES PARA EL MÉDICO:
- Basarse en los códigos CIE-10 identificados
- Consultar protocolos MINSA correspondientes
- Considerar edad y sexo del paciente (si aplica)
- Siempre verificar con el paciente directamente
- NO hacer diagnósticos, solo sugerencias"""

        return context

    def _generate_response(self, question: str, context: str) -> str:
        """
        Llamar a Llama-2 via Ollama para generar respuesta

        Returns:
            Respuesta generada por Llama-2
        """
        try:
            prompt = f"""Eres un asistente médico experto en medicina clínica peruana.

{context}

PREGUNTA: {question}

RESPUESTA CLÍNICA:"""

            logger.info(f"Calling Llama-2 ({self.model})...")

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                llm_response = data.get('response', '').strip()
                logger.info(f"✓ LLM response generated ({len(llm_response)} chars)")
                return llm_response
            else:
                logger.error(f"LLM error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            logger.error("LLM request timeout (Llama-2 is slow)")
            return None
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None

    def _calculate_metrics(
        self,
        question: str,
        retrieved_codes: List[Dict],
        context: str,
        llm_response: Optional[str],
        elapsed_time: float
    ) -> Dict:
        """
        Calcular métricas de evaluación del RAG

        Métricas:
        - Retrieval: cantidad y relevancia de CIE-10 recuperados
        - Context: longitud del contexto
        - Generation: presencia de respuesta LLM
        - Performance: tiempo total
        """

        # Relevancia promedio de los códigos recuperados
        avg_relevance = (
            sum(r['relevance'] for r in retrieved_codes) / len(retrieved_codes)
            if retrieved_codes else 0.0
        )

        # Cantidad de códigos recuperados
        num_retrieved = len(retrieved_codes)

        # Presencia de LLM
        has_llm = llm_response is not None and len(llm_response) > 0

        metrics = {
            'question_length': len(question),
            'num_retrieved_codes': num_retrieved,
            'avg_relevance': round(avg_relevance, 3),
            'context_length': len(context),
            'llm_generated': has_llm,
            'llm_response_length': len(llm_response) if llm_response else 0,
            'elapsed_time_seconds': round(elapsed_time, 3),
            'timestamp': datetime.now().isoformat()
        }

        return metrics

    def get_metrics_report(self) -> Dict:
        """
        Generar reporte de métricas agregadas

        Returns:
            {
                'total_queries': int,
                'avg_elapsed_time': float,
                'avg_relevance': float,
                'llm_success_rate': float,
                'metrics_by_query': List[Dict]
            }
        """
        if not self.metrics:
            return {
                'total_queries': 0,
                'avg_elapsed_time': 0.0,
                'avg_relevance': 0.0,
                'llm_success_rate': 0.0,
                'metrics_by_query': []
            }

        total = len(self.metrics)
        avg_time = sum(m['elapsed_time_seconds'] for m in self.metrics) / total
        avg_relevance = sum(m['avg_relevance'] for m in self.metrics) / total
        llm_success = sum(1 for m in self.metrics if m['llm_generated']) / total

        report = {
            'total_queries': total,
            'avg_elapsed_time_seconds': round(avg_time, 3),
            'avg_relevance': round(avg_relevance, 3),
            'llm_success_rate': round(llm_success, 3),
            'metrics_by_query': self.metrics
        }

        logger.info(f"Metrics Report: {total} queries, avg relevance {avg_relevance:.3f}")

        return report

    def ingest_document(self, title: str, content: str) -> Dict:
        """
        Ingerir documento clínico (protocolo, guía, etc)

        Para E3, esto es un placeholder que prepara el documento
        para indexación futura en Elasticsearch o similar

        Args:
            title: Título del documento
            content: Contenido del documento

        Returns:
            {
                'status': 'ingested',
                'document_id': str,
                'title': str,
                'content_length': int
            }
        """
        document_id = f"doc_{datetime.now().timestamp()}"

        result = {
            'status': 'ingested',
            'document_id': document_id,
            'title': title,
            'content_length': len(content),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Document ingested: {title} ({document_id})")

        return result


if __name__ == "__main__":
    """Test del RAG Engine"""
    import sys
    sys.path.insert(0, 'src')

    logging.basicConfig(level=logging.INFO)

    # Este es un test que requiere:
    # 1. Motor de búsqueda híbrida funcionando
    # 2. Ollama corriendo con Llama-2

    print("\n" + "="*80)
    print("RAG ENGINE - DEMO")
    print("="*80)
    print("\nNota: Este test requiere:")
    print("1. Motor de búsqueda híbrida (hybrid_search)")
    print("2. Ollama corriendo: ollama serve")
    print("\nTest completo en: tests/test_rag_engine.py")
    print("="*80)
