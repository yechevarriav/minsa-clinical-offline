"""
Load Tests - Concurrent Users
Prueba de carga con 10+ usuarios concurrentes (Item 3.9)
Valida: Performance bajo carga, estabilidad del sistema
"""

import pytest
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

logger = logging.getLogger(__name__)


class TestLoadConcurrent:
    """Tests de carga con usuarios concurrentes"""

    @pytest.mark.slow
    def test_concurrent_10_users(self, rag_engine):
        """
        Simular 10 usuarios concurrentes haciendo queries
        Validar que el sistema maneja carga sin degradación
        """
        num_users = 10
        queries_per_user = 3

        test_queries = [
            "Fiebre alta",
            "Dolor de cabeza",
            "Tos persistente",
            "Dificultad para respirar",
            "Dolor abdominal",
        ]

        results = []
        start_time = time.time()

        def user_query_task(user_id: int, query: str) -> Dict:
            """Simular un usuario haciendo una query"""
            task_start = time.time()
            try:
                result = rag_engine.query(query, use_llm=False)
                task_elapsed = time.time() - task_start

                return {
                    'user_id': user_id,
                    'query': query,
                    'success': True,
                    'elapsed_time': task_elapsed,
                    'codes_found': len(result['retrieved_codes'])
                }
            except Exception as e:
                task_elapsed = time.time() - task_start
                return {
                    'user_id': user_id,
                    'query': query,
                    'success': False,
                    'elapsed_time': task_elapsed,
                    'error': str(e)
                }

        # Ejecutar queries en paralelo (ThreadPool)
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []

            for user_id in range(num_users):
                for query_idx in range(queries_per_user):
                    query = test_queries[query_idx % len(test_queries)]
                    future = executor.submit(user_query_task, user_id, query)
                    futures.append(future)

            # Recolectar resultados
            for future in as_completed(futures):
                results.append(future.result())

        total_elapsed = time.time() - start_time

        # Análisis de resultados
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        success_rate = len(successful) / len(results) if results else 0
        avg_time = sum(r['elapsed_time'] for r in successful) / len(successful) if successful else 0
        max_time = max(r['elapsed_time'] for r in successful) if successful else 0
        min_time = min(r['elapsed_time'] for r in successful) if successful else 0

        # Validaciones
        assert success_rate >= 0.95, f"Success rate should be ≥95%, got {success_rate*100:.1f}%"
        assert avg_time < 2.0, f"Average time should be <2s, got {avg_time:.3f}s"
        assert max_time < 5.0, f"Max time should be <5s, got {max_time:.3f}s"

        # Logging
        logger.info(f"✓ Load test completed:")
        logger.info(f"  Users: {num_users}")
        logger.info(f"  Total requests: {len(results)}")
        logger.info(f"  Successful: {len(successful)}/{len(results)} ({success_rate*100:.1f}%)")
        logger.info(f"  Total time: {total_elapsed:.2f}s")
        logger.info(f"  Avg response time: {avg_time:.3f}s")
        logger.info(f"  Min/Max response time: {min_time:.3f}s / {max_time:.3f}s")

        if failed:
            logger.warning(f"  Failed requests: {len(failed)}")
            for f in failed[:3]:
                logger.warning(f"    - User {f['user_id']}: {f['error']}")

    @pytest.mark.slow
    def test_concurrent_20_users(self, rag_engine):
        """
        Simular 20 usuarios concurrentes
        Prueba de stress del sistema
        """
        num_users = 20
        queries_per_user = 2

        test_queries = [
            "Fiebre",
            "Tos",
            "Dolor",
            "Mareo",
        ]

        results = []

        def user_query_task(user_id: int, query: str) -> Dict:
            task_start = time.time()
            try:
                result = rag_engine.query(query, use_llm=False)
                return {
                    'user_id': user_id,
                    'success': True,
                    'elapsed_time': time.time() - task_start,
                    'codes': len(result['retrieved_codes'])
                }
            except Exception as e:
                return {
                    'user_id': user_id,
                    'success': False,
                    'elapsed_time': time.time() - task_start,
                    'error': str(e)
                }

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = []
            for user_id in range(num_users):
                for query_idx in range(queries_per_user):
                    query = test_queries[query_idx % len(test_queries)]
                    future = executor.submit(user_query_task, user_id, query)
                    futures.append(future)

            for future in as_completed(futures):
                results.append(future.result())

        successful = [r for r in results if r['success']]
        success_rate = len(successful) / len(results) if results else 0

        assert success_rate >= 0.90, f"Success rate should be ≥90%, got {success_rate*100:.1f}%"
        logger.info(f"✓ Stress test (20 users) passed: {success_rate*100:.1f}% success")

    @pytest.mark.slow
    def test_sustained_load(self, rag_engine):
        """
        Prueba de carga sostenida
        10 usuarios durante 60 segundos
        """
        num_users = 10
        duration_seconds = 60

        test_queries = [
            "Fiebre", "Tos", "Dolor de cabeza",
            "Mareo", "Nausea", "Erupción"
        ]

        results = []
        start_time = time.time()
        query_count = 0

        def user_sustained_load(user_id: int):
            nonlocal query_count
            query_idx = 0
            while time.time() - start_time < duration_seconds:
                query = test_queries[query_idx % len(test_queries)]
                query_idx += 1

                task_start = time.time()
                try:
                    result = rag_engine.query(query, use_llm=False)
                    results.append({
                        'user_id': user_id,
                        'success': True,
                        'elapsed_time': time.time() - task_start
                    })
                except Exception as e:
                    results.append({
                        'user_id': user_id,
                        'success': False,
                        'elapsed_time': time.time() - task_start,
                        'error': str(e)
                    })
                query_count += 1

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(user_sustained_load, i) for i in range(num_users)]
            for future in as_completed(futures):
                pass

        total_time = time.time() - start_time
        successful = [r for r in results if r['success']]
        success_rate = len(successful) / len(results) if results else 0

        logger.info(f"✓ Sustained load test (60s, {num_users} users):")
        logger.info(f"  Total queries: {query_count}")
        logger.info(f"  Successful: {len(successful)}/{len(results)} ({success_rate*100:.1f}%)")
        logger.info(f"  Avg response: {sum(r['elapsed_time'] for r in successful)/len(successful):.3f}s")
        logger.info(f"  Queries/sec: {query_count/total_time:.2f}")


# ============================================================================
# PYTEST MARKERS
# ============================================================================

@pytest.mark.load
@pytest.mark.slow
def test_load_marker(rag_engine):
    """Test marcado como load y slow"""
    result = rag_engine.query("test", use_llm=False)
    assert result is not None
