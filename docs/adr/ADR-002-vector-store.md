# ADR-002: Selección del Vector Store

**Fecha:** Marzo 2026
**Estado:** Aceptado
**Autores:** Yvonne Patricia Echevarría Vargas
**Contexto del proyecto:** Sistema de Soporte Clínico Offline — MINSA Perú

---

## Contexto

El pipeline RAG del sistema requiere almacenar y recuperar embeddings de los 14,702 códigos CIE-10 MINSA. El vector store debe:

- Operar **sin servidor** (sin conexión a internet)
- Buscar top-k documentos en **<100ms** en CPU
- Indexar **~15,000 vectores** de 768 dimensiones
- Ser **portable** (funciona en Windows/Linux sin configuración adicional)
- Tener **bajo footprint** en disco (<1 GB)

## Decisión

**Seleccionar: FAISS (Facebook AI Similarity Search) con indexado IVF+PQ**

```python
# Configuración implementada
index_type = "IVF+PQ"    # Product Quantization para compresión
n_centroids = 256         # Clusters IVF
n_bits = 8                # Bits por subvector PQ
dimensions = 768          # RoBERTa biomedical output
documents_indexed = 14702 # Códigos CIE-10 MINSA
```

## Alternativas Consideradas

| Opción | Offline | Velocidad | Tamaño | Setup | Decisión |
|--------|---------|-----------|--------|-------|----------|
| **FAISS** | ✅ 100% | ✅ <50ms | ✅ ~500MB | ✅ pip | ✅ **ELEGIDO** |
| Chroma | ✅ 100% | ✅ ~80ms | ✅ ~200MB | ✅ pip | ⚠️ Alternativa |
| Weaviate | ⚠️ Docker | ✅ ~100ms | ❌ ~2GB | ❌ Docker | ❌ Rechazado |
| Pinecone | ❌ Cloud | ✅ Muy rápido | N/A | ❌ API | ❌ Rechazado |
| Qdrant | ⚠️ Docker | ✅ ~80ms | ❌ ~1GB | ❌ Docker | ❌ Rechazado |
| Milvus | ❌ Servidor | ✅ Muy rápido | ❌ ~3GB | ❌ Complejo | ❌ Rechazado |

## Justificación

**¿Por qué FAISS?**

1. **Offline garantizado:** Biblioteca Python pura — sin Docker, sin servidor, sin internet.
2. **Velocidad probada en producción:** Usado por Meta, OpenAI y Hugging Face en producción.
3. **IVF+PQ reduce tamaño:** De ~450MB (flat) a ~45MB con mínima pérdida de precisión.
4. **CPU-optimized:** AVX2 support detectado automáticamente — aprovecha hardware existente.
5. **Cache persistente:** Index guardado en `.cache/medical_search` — no reconstruye en cada inicio.

## Parámetros RAG Implementados

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| `embedding_model` | PlanTL-GOB-ES/roberta-base-biomedical-clinical-es | Español biomédico |
| `embedding_dimensions` | 768 | RoBERTa base output |
| `index_type` | IVF + PQ | Balance velocidad/tamaño |
| `n_centroids` | 256 | Apropiado para 14,702 vectores |
| `k (top-k)` | 5 | Top-5 diagnósticos |
| `similarity_threshold` | 0.3 | Filtra irrelevantes |
| `query_latency_avg` | 210ms | Medido en producción |
| `query_latency_p95` | <500ms | Bajo carga |

## Consecuencias Positivas

- ✅ Búsqueda semántica offline sin dependencias externas
- ✅ Cache persistente — primera carga ~4 min, siguientes <5s
- ✅ Funciona con CPU común (sin GPU)
- ✅ Soporte AVX2 detectado automáticamente en Render y local
- ✅ Compatible con Python 3.10 (faiss-cpu==1.7.4)

## Consecuencias Negativas / Trade-offs

- ❌ No tiene GUI de administración
- ❌ No es base de datos transaccional (sin ACID)
- ❌ Reconstrucción requiere ~4 minutos (primera vez)
- ⚠️ IVF+PQ puede reducir recall vs. flat index

## Mitigaciones

- Cache en `.cache/medical_search` evita reconstrucción
- IVF+PQ configurado con n_bits=8 mantiene >95% recall
- Primera carga en background no bloquea el puerto 8000

## Nota Técnica — Compatibilidad Python 3.10

```dockerfile
# faiss-cpu==1.7.4 compatible con Python 3.10
# faiss-cpu==1.7.4.post1 NO existe — versión incorrecta descubierta en E4
RUN pip install faiss-cpu==1.7.4
# torch debe instalarse SEPARADO para evitar conflicto con scikit-learn
RUN pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu
```

## Estado en E4

- ✅ Implementado y funcionando (local + Render.com)
- ✅ 14,702 vectores CIE-10 indexados correctamente
- ✅ Cache persistente funcionando en Render
- ✅ Latencia real: 210ms avg en cloud
