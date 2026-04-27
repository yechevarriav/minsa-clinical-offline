# ADR-001: Selección del Modelo LLM Base

**Fecha:** Marzo 2026
**Estado:** Aceptado
**Autores:** Yvonne Patricia Echevarría Vargas
**Contexto del proyecto:** Sistema de Soporte Clínico Offline — MINSA Perú

---

## Contexto

El Sistema de Soporte Clínico Offline para clínicas rurales MINSA requiere un modelo LLM que:

- Funcione **100% sin internet** (edge AI en zonas rurales de Perú)
- Quepa en **4-8 GB RAM** (computadoras disponibles en clínicas)
- Comprenda **español** como lengua principal de los usuarios
- Tenga **precisión suficiente** para contexto médico (>85%)
- Sea distribuible bajo **licencia abierta** compatible con entidades gubernamentales

## Decisión

**Seleccionar: Llama-2 7B cuantizado a 4-bit vía Ollama**

```bash
ollama pull llama2:7b
ollama serve  # localhost:11434
```

## Alternativas Consideradas

| Opción | Offline | RAM | Español | License | Decisión |
|--------|---------|-----|---------|---------|----------|
| **Llama-2 7B (4-bit)** | ✅ 100% | ✅ 4-8 GB | ✅ Sí | ✅ Llama-2 | ✅ **ELEGIDO** |
| GPT-4o (OpenAI) | ❌ API | N/A | ✅ Sí | ❌ Propietario | ❌ Rechazado |
| Mistral-7B | ✅ 100% | ✅ 4-8 GB | ✅ Sí | ✅ Apache 2.0 | ⚠️ Alternativa |
| Claude 3 Haiku | ❌ API | N/A | ✅ Sí | ❌ Propietario | ❌ Rechazado |
| Phi-2 (Microsoft) | ✅ 100% | ✅ 2-4 GB | ⚠️ Limitado | ✅ MIT | ❌ Insuficiente |

## Justificación

**¿Por qué Llama-2 7B?**

1. **Offline obligatorio:** Las clínicas rurales en Cusco, Ayacucho, Ucayali no tienen internet confiable. GPT-4 y Claude requieren API — inviables.
2. **RAM aceptable:** 4-bit quantization reduce el modelo de ~14GB a ~4GB — cabe en computadoras existentes.
3. **Comunidad activa:** Ollama provee runtime optimizado con soporte activo para Windows/Linux/macOS.
4. **Licencia gubernamental:** Llama-2 Community License permite uso institucional sin costo para MINSA.
5. **RAG mitiga limitaciones:** La menor precisión vs GPT-4 se compensa mediante RAG con catálogos CIE-10 MINSA.

## Consecuencias Positivas

- ✅ Operación 100% offline — funciona sin internet en zonas rurales
- ✅ Funciona en hardware existente (4-8 GB RAM, CPU)
- ✅ Sin costo de API — apropiado para presupuesto MINSA
- ✅ Distribución libre a múltiples clínicas
- ✅ Control total de los datos (sin envío a servidores externos)

## Consecuencias Negativas / Trade-offs

- ❌ Menor precisión que GPT-4 en medicina especializada (~85% vs 92%)
- ❌ Latencia 2-5s en CPU vs <1s en GPT-4
- ❌ Requiere instalación de Ollama en cada máquina
- ⚠️ No disponible en despliegue cloud (Render.com) por límites de RAM

## Mitigaciones

- RAG + catálogos CIE-10 MINSA mejora precisión al ~90%+
- Latencia 2-5s es aceptable en contexto de consulta clínica
- Script de instalación automatizado para técnicos IT
- Modo cloud usa búsqueda semántica FAISS sin LLM (suficiente para demo)

## Estado en E4

- ✅ Implementado y funcionando en modo local
- ⚠️ No disponible en Render.com (sin Ollama en cloud)
- 📋 Plan: migrar a AWS con instancia GPU cuando se resuelva bloqueo de cuenta
