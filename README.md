# Proyecto Final AI/LLM

**Programa:** AI-LLM Solution Architect
**Curso:** 5 — Proyecto Final de Arquitectura e Integración AI/LLM
**Documento:** Plantilla Oficial de Documentación del Proyecto

---

## 📋 Información General del Proyecto

| Campo                           | Valor                                                                                             |
| ------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Nombre del Proyecto**         | Sistema de Soporte Clínico Offline: Diagnósticos + Procedimientos para Clínicas Rurales MINSA     |
| **Participante(s)**             | Yvonne Patricia Echevarria Vargas                                                                 |
| **Instructor**                  | Andrés Rojas                                                                                      |
| **Cohorte / Edición**           | Cohorte 2026-A                                                                                    |
| **Fecha de Inicio**             | 10/03/2026                                                                                        |
| **Fecha de Entrega Final**      | 31/05/2026                                                                                        |
| **Versión del Documento**       | v1.0 - Capítulos 1-2 (S1-S2)                                                                      |
| **Estado del Proyecto**         | En Planificación - Especificación de Requerimientos                                               |
| **Repositorio GitHub/GitLab**   | https://github.com/yechevarriav/minsa-clinical-offline                                            |
| **Entorno Cloud**               | AWS (región Sudamérica) + Edge (computadoras locales)                                             |
| **Stack Tecnológico Principal** | Python 3.11, LangChain, Claude 3.5 Sonnet, Llama 7B (cuantizado), FAISS, FastAPI, SQLite, FHIR R4 |

---

> ⚠️ **Instrucciones Generales**
>
> 1. Complete **TODOS** los campos marcados. El texto en _cursiva_ son instrucciones — reemplácelas con su contenido real.
> 2. Mantenga consistencia en nomenclatura, versiones y referencias cruzadas entre secciones.
> 3. Los diagramas deben insertarse como imágenes de alta resolución (mínimo 150 dpi).
> 4. Cite todas las fuentes técnicas en formato **IEEE** o **APA**.
> 5. La documentación debe reflejar el estado **REAL** del proyecto, no el ideal. Sea preciso y honesto.
> 6. Entregue este archivo `.md` en el repositorio Git del proyecto, junto con el PDF generado.

---

## Tabla de Contenidos

- [1. Resumen Ejecutivo](#1-resumen-ejecutivo)
- [2. Análisis y Especificación de Requerimientos](#2-análisis-y-especificación-de-requerimientos)
- [3. Diseño de Arquitectura AI/LLM](#3-diseño-de-arquitectura-aillm)
- [4. Diseño de APIs y Conectores](#4-diseño-de-apis-y-conectores)
- [5. Seguridad, Cumplimiento y Ética](#5-seguridad-cumplimiento-y-ética)
- [6. Implementación y Configuración de Infraestructura](#6-implementación-y-configuración-de-infraestructura)
- [7. Estrategia de Pruebas y Resultados](#7-estrategia-de-pruebas-y-resultados)
- [8. Despliegue, Escalabilidad y Costos](#8-despliegue-escalabilidad-y-costos)
- [9. Observabilidad y Monitoreo](#9-observabilidad-y-monitoreo)
- [10. Resultados, Conclusiones y Trabajo Futuro](#10-resultados-conclusiones-y-trabajo-futuro)
- [11. Rúbrica de Evaluación](#11-rúbrica-de-evaluación)
- [12. Referencias y Bibliografía](#12-referencias-y-bibliografía)
- [Anexos](#anexos)

---

## 1. Resumen Ejecutivo

_Síntesis ejecutiva del proyecto que debe permitir a un lector técnico-gerencial comprender el alcance, la propuesta de valor, el enfoque arquitectónico y los resultados principales en no más de **600 palabras**._

### 1.1 Propuesta de Valor y Problema que Resuelve

**PROBLEMA EMPRESARIAL:**

En Perú, ~40% de clínicas y sucursales MINSA en zonas rurales (Cusco, Ayacucho, Ucayali, Amazonía) no tienen acceso confiable a internet. Sin embargo, disponen de computadoras (8GB+ RAM) con conectividad ocasional (WiFi nocturna).

**Situación Actual (AS-IS):**

- Médicos toman decisiones diagnósticas sin referencia estructurada
- Clasificación manual de diagnósticos CIE-10: 5-10 minutos/consulta
- 35% de diagnósticos iniciales son inconsistentes con protocolos MINSA
- Procedimientos no se registran en RENHICE (sistema central)
- Cuando hay internet, cargar RENHICE toma > 30s (conexión débil)

**Impacto Cuantificado:**

- 8,000-20,000 consultas/día en sucursales rurales sin referencia estructurada
- Cada error diagnóstico requiere re-consulta (duplica costo)
- 4-6 horas/día de tiempo médico en búsquedas manuales
- Inconsistencia de datos en RENHICE = auditorías fallidas

**Solución AI/LLM Propuesta (TO-BE):**

Sistema offline que:

1. Sugiere diagnósticos válidos (CIE-10 OMS 2024) en < 3s basado en síntomas
2. Recupera procedimientos indicados (CIE-9-MC MINSA) para cada diagnóstico
3. Funciona 100% sin internet (edge AI)
4. Se sincroniza automáticamente con RENHICE cuando hay conexión
5. Registra cada sugerencia para feedback loop (mejora v1.1 central)

**¿Por qué AI/LLM y no solución tradicional?**

- Búsqueda SQL estática: No entiende síntomas en lenguaje natural
- API REST a central: Requiere internet constante (inviable en zonas rurales)
- LLM offline comprimido: Comprende contexto, funciona offline, genera sugerencias precisas

**ROI esperado:**

- Reducción tiempo consulta: 8 min → 2 min (75% ahorro)
- Consistencia diagnóstica: +40%
- Adopción RENHICE: +60%
- Costo operacional: < USD $150/mes (vs. USD $500+ conexión satelital)

### 1.2 Alcance y Delimitación

_Defina con precisión qué está IN SCOPE y qué está OUT OF SCOPE para la versión entregada._

### 1.2 Alcance y Delimitación

| ✅ EN SCOPE                                                   | ❌ OUT OF SCOPE                                             |
| ------------------------------------------------------------- | ----------------------------------------------------------- |
| API REST para consultas diagnósticas (síntomas → CIE-10)      | Fine-tuning del LLM en sucursal (congelado v1.0)            |
| RAG local indexado con diagnósticos CIE-10 + procedimientos   | Interfaz web compleja (solo API + CLI)                      |
| Sugerencia automática procedimientos CIE-9-MC indicados       | Integración real-time con RENHICE (sync async semanal)      |
| Despliegue offline en computadora local (Windows/Linux)       | Soporte multiidioma más allá español e inglés               |
| Sincronización semanal con servidor central (logs + feedback) | Análisis predictivo (comorbilidades, recurrencia)           |
| Interfaz CLI para técnico de IT (deploy, config)              | Entrenamiento de modelo local (usar Llama 7B pre-entrenado) |
| Logging de todas las consultas (mejora v1.1)                  | SLA enterprise > 99.9% (MVP con 99.5%)                      |
| Soporte idiomas: Español e Inglés (datos OMS públicos)        | Integración con sistemas externos (farmacia, laboratorio)   |

### 1.3 Indicadores Clave de Éxito (KPIs del Proyecto)

### 1.3 Indicadores Clave de Éxito (KPIs del Proyecto)

| KPI / Métrica                       | Línea Base | Meta Objetivo | Resultado Obtenido     |
| ----------------------------------- | ---------- | ------------- | ---------------------- |
| Latencia búsqueda CIE-10 (p95)      | N/A        | < 3 segundos  | _[Completar al final]_ |
| Precisión sugerencias diagnósticas  | N/A        | >= 90%        | _[Completar al final]_ |
| Disponibilidad offline (uptime)     | N/A        | >= 99.5%      | _[Completar al final]_ |
| Precisión RAG (RAGAS faithfulness)  | N/A        | >= 88%        | _[Completar al final]_ |
| Tasa aceptación médicos (uso real)  | 0%         | >= 80%        | _[Completar al final]_ |
| Tamaño instalación total            | N/A        | <= 2 GB       | _[Completar al final]_ |
| Costo operacional mensual (central) | N/A        | < USD $150    | _[Completar al final]_ |
| Tiempo sincronización (semanal)     | N/A        | < 5 minutos   | _[Completar al final]_ |

---

## 2. Análisis y Especificación de Requerimientos

### 2.1 Contexto del Caso de Uso Empresarial

**ANÁLISIS 5W+H:**

**WHO (¿Quién usa el sistema?)**

- Médicos en clínicas rurales MINSA sin internet estable
- Enfermeras para triage inicial de pacientes
- Técnicos de IT en sucursal (mantenimiento, actualizaciones)
- Servidor central MINSA (mejora y redistribución de modelos)

**WHAT (¿Qué debe hacer?)**

- Usuario ingresa síntomas O código CIE-10
- Sistema RAG busca diagnósticos similares en índice local
- Sugiere CIE-10 más probable + procedimientos indicados (CIE-9-MC)
- Registra sugerencia en base local para sincronización posterior

**WHY (¿Por qué AI/LLM y no solución tradicional?)**

- Búsqueda manual en PDF: 5-10 min/consulta (LLM: < 3s)
- SQL estática: No entiende síntomas en lenguaje natural ("dolor pecho + disnea")
- API REST a central: Requiere internet constante (inviable en zonas rurales)
- LLM offline comprimido: Comprende contexto, funciona offline, genera sugerencias precisas

**WHERE (¿Dónde se despliega?)**

- Computadora local en sucursal MINSA (Windows/Linux)
- RAM: 8GB mínimo | SSD: 2GB disponibles
- Red: Conexión a internet ocasional (WiFi nocturna, no crítica)

**WHEN (¿Con qué frecuencia y volumen?)**

- Volumen: 20-50 consultas/día por sucursal
- Picos horarios: 9-12am y 2-4pm (horarios de atención)
- Sincronización: 1 vez semanal (martes-viernes 22:00)

**HOW (¿Cómo se mide el éxito?)**

- Latencia p95: < 3 segundos
- Precisión diagnósticos: >= 90% (validación con médicos reales)
- Uptake: >= 80% médicos usando sistema en mes 1
- Disponibilidad: 99.5% uptime (solo desconexiones planificadas)

### 2.2 Requerimientos Funcionales

| ID     | Descripción del Requerimiento                                                                                | Prioridad | Criterio de Aceptación                                 |
| ------ | ------------------------------------------------------------------------------------------------------------ | --------- | ------------------------------------------------------ |
| RF-001 | El sistema DEBE procesar síntomas en lenguaje natural (ej: "dolor pecho + disnea") y generar JSON parseable  | Alta      | Entrada < 500 caracteres → JSON válido en < 1.5s       |
| RF-002 | El sistema DEBE recuperar diagnósticos CIE-10 similares del vector store local usando búsqueda semántica     | Alta      | Top-5 resultados con similarity >= 0.7 en < 2s         |
| RF-003 | El sistema DEBE sugerir procedimientos indicados (CIE-9-MC) para cada diagnóstico recuperado                 | Alta      | Mínimo 3 procedimientos sugeridos con relevancia       |
| RF-004 | El sistema DEBE aceptar entrada de código CIE-10 directo y validar contra lista OMS 2024                     | Media     | Validación en < 500ms, error si código inválido        |
| RF-005 | El sistema DEBE registrar cada consulta (síntomas, diagnósticos sugeridos, timestamp) en base de datos local | Alta      | Registro completo en SQLite con timestamp sincronizado |
| RF-006 | El sistema DEBE sincronizar con servidor central MINSA una vez semanal, enviando logs + feedback             | Alta      | Sync completado en < 5 minutos sin perder registros    |
| RF-007 | El sistema DEBE soportar interfaz CLI para técnico IT (deploy, iniciar servicio, listar logs)                | Media     | Comandos funcionales: start, stop, status, logs        |
| RF-008 | El sistema DEBE aceptar feedback del médico ("diagnóstico correcto/incorrecto") para mejorar modelo v1.1     | Media     | Feedback registrado y sincronizado en próximo ciclo    |

### 2.3 Requerimientos No Funcionales

### 2.3 Requerimientos No Funcionales

| ID      | Categoría      | Descripción                                | Métrica / Umbral                                |
| ------- | -------------- | ------------------------------------------ | ----------------------------------------------- |
| RNF-001 | Rendimiento    | Latencia búsqueda CIE-10 extremo a extremo | p95 < 3s bajo carga normal (10 consultas/min)   |
| RNF-002 | Escalabilidad  | Manejar múltiples consultas simultáneas    | 5+ consultas concurrentes sin degradación       |
| RNF-003 | Seguridad      | Autenticación de usuario en sucursal       | Sistema local sin requerir conexión             |
| RNF-004 | Disponibilidad | Uptime offline garantizado                 | >= 99.5% (solo desconexiones planificadas)      |
| RNF-005 | Cumplimiento   | Regulaciones sanitarias aplicables         | GDPR (datos pacientes), FHIR R4 compliance      |
| RNF-006 | Observabilidad | Logging de todas las consultas             | Logs estructurados JSON, búsqueda por timestamp |
| RNF-007 | Almacenamiento | Tamaño total instalación                   | <= 2 GB (modelo + datos + runtime)              |
| RNF-008 | Sincronización | Tiempo de sync semanal con central         | < 5 minutos sin bloquear operación local        |
| RNF-009 | Portabilidad   | Funciona en Windows y Linux                | Docker opcional, instalación standalone         |
| RNF-010 | Resiliencia    | Manejo de fallos de conexión               | Modo degradado si falla internet (offline full) |

### 2.4 Restricciones y Supuestos

### 2.4 Restricciones y Supuestos

| Restricciones                                    | Supuestos                                             |
| ------------------------------------------------ | ----------------------------------------------------- |
| Presupuesto cloud central: USD $150-200/mes      | Sucursales tienen computadora con 8GB+ RAM disponible |
| Modelo LLM debe caber en <= 2GB RAM              | Conexión internet disponible 1 vez semanal (noche)    |
| No se permite almacenamiento de PII en logs      | CIE-10 y CIE-9-MC estándares no cambiarán en 6 meses  |
| Sincronización debe ser asincrónica (no bloquea) | Médicos adoptarán sistema en fase piloto              |
| Sin fine-tuning local (congelado v1.0)           | Catálogos públicos OMS disponibles para descarga      |
| Soporte solo español e inglés (v1.0)             | Sistema puede fallar gracefully sin afectar operación |
| No integración real-time con RENHICE (async)     | Técnicos IT tienen capacitación mínima para deploy    |

---

## 3. Diseño de Arquitectura AI/LLM

### 3.1 Diagrama de Arquitectura General (Nivel C4 — Contexto y Contenedor)

> 📌 **Instrucción:** Inserte aquí el diagrama de arquitectura de alto nivel. Herramientas recomendadas: Lucidchart, Draw.io, Miro, o AWS Architecture Diagram.
>
> El diagrama **DEBE** incluir: (1) Usuarios/Actores externos, (2) Capa de presentación/API, (3) Servicios de orquestación LLM, (4) Fuentes de datos y vector stores, (5) Servicios cloud, (6) Componentes de seguridad e identidad.
>
> Resolución mínima: 150 dpi. Formato: PNG o SVG.

```
[ INSERTE DIAGRAMA DE ARQUITECTURA GENERAL AQUÍ ]
```

_Figura 1. Diagrama de Arquitectura General — [Nombre del Proyecto] v[X.X]_

### 3.2 Descripción de Componentes Arquitectónicos

### 3.2 Descripción de Componentes Arquitectónicos

| Componente           | Tecnología / Servicio                     | Responsabilidad Principal                            | Justificación de Selección                          |
| -------------------- | ----------------------------------------- | ---------------------------------------------------- | --------------------------------------------------- |
| API REST Local       | FastAPI (Python 3.11)                     | Exposición de endpoints diagnóstico/procedimiento    | Ligero, portable, funciona sin dependencias pesadas |
| Orquestador LLM      | LangChain + FAISS                         | Gestión RAG, recuperación semántica, sugerencias     | LangChain maduro para RAG, FAISS es CPU-friendly    |
| Modelo LLM Local     | Llama 7B cuantizado (int4, ~150MB)        | Inferencia offline de diagnósticos/procedimientos    | Pequeño, funciona en CPU, precisión > 85%           |
| Embeddings Local     | Sentence-Transformers (distilbert, ~50MB) | Conversión síntomas → vectores para búsqueda         | Rápido en CPU, sin conexión necesaria               |
| Vector Store Local   | FAISS (indexado en SQLite)                | Almacenamiento catálogos CIE-10 + procedimientos     | Búsqueda < 100ms, CPU-only, sin servidor            |
| Base Datos Local     | SQLite (< 500MB)                          | Registro consultas, feedback, logs de sincronización | Portable, sin setup, ACID compliant                 |
| Sincronización       | Rsync + SSH / S3 SDK                      | Envío logs/feedback a central, descarga modelos v1.1 | Eficiente, solo cambios, tolerante a fallos         |
| CLI Management       | Python Click + Systemd/Windows Service    | Iniciar/parar servicio, listar logs, configurar sync | Simple, sin GUI, ideal técnicos IT rurales          |
| Observabilidad Local | Logs JSON + SQLite                        | Trazas consultas, errores, sincronización            | Offline, searchable, bajo overhead                  |

### 3.2b Stack Central (Servidor MINSA)

| Componente             | Tecnología                                         | Responsabilidad                              | Notas                                   |
| ---------------------- | -------------------------------------------------- | -------------------------------------------- | --------------------------------------- |
| API Central            | FastAPI / Django REST                              | Recibe sync de sucursales, entrena modelos   | Almacena logs centralizados             |
| LLM Entrenamiento      | Claude 3.5 Sonnet API (entrenamiento + evaluación) | Mejora continua de modelo central            | Fine-tuning opcional en v1.1            |
| Vector Store Central   | Weaviate / Pinecone                                | Índice maestro diagnósticos + procedimientos | Respaldo centralizado                   |
| Database Central       | PostgreSQL                                         | Almacenamiento logs, feedback, versiones     | RENHICE source of truth                 |
| CI/CD                  | GitHub Actions / Jenkins                           | Deploy de nuevas versiones a sucursales      | Compresión + cuantización automática    |
| Observabilidad Central | Prometheus + Grafana                               | Monitoreo salud sistema distribuido          | Alertas si sucursal sin sync > 1 semana |

### 3.3 Diagrama de Flujo de Datos e Integración

_Inserte diagrama de secuencia o flujo de datos que muestre el ciclo completo de una solicitud: desde el input del usuario hasta la respuesta final, incluyendo pasos de RAG, validación, logging y respuesta._

```
[ INSERTE DIAGRAMA DE FLUJO DE DATOS / SECUENCIA AQUÍ ]
```

_Figura 2. Flujo de Datos — Ciclo de Request/Response en [Nombre del Proyecto]_

### 3.4 Estrategia de Diseño de Prompts y RAG

**System Prompt Base:**

_Documente el system prompt que guía el comportamiento del modelo. Incluya: rol, restricciones, formato de respuesta esperado, y manejo de casos fuera de alcance._

```
Eres un asistente experto en [dominio] para [empresa/contexto]. Tu función es [descripción precisa].

RESTRICCIONES:
  - Solo responde en base al contexto proporcionado. Si no tienes información suficiente,
    indica "No tengo información sobre eso."
  - No generes contenido que viole [regulación/política].
  - Responde siempre en [idioma] con un tono [formal/técnico/etc.].

FORMATO DE RESPUESTA: [Especificar estructura esperada: JSON / Markdown / texto libre / etc.]
```

### 3.4 Arquitectura física (equivalencias por nube)

| Capa             | AWS                   | GCP                   | Azure                |
| ---------------- | --------------------- | --------------------- | -------------------- |
| Ingesta          | Lambda / ECS          | Cloud Run / Functions | Azure Functions      |
| Raw (Bronze)     | S3                    | GCS                   | ADLS Gen2            |
| Transform        | Glue / EMR            | Dataflow / Dataproc   | Synapse / Databricks |
| Curated (Silver) | S3 Parquet            | GCS Parquet           | ADLS Parquet         |
| Serving (Gold)   | Athena / Redshift     | BigQuery              | Synapse SQL          |
| Orquestación     | Step Functions / MWAA | Composer / Workflows  | ADF                  |
| Observabilidad   | CloudWatch            | Cloud Monitoring      | Azure Monitor        |

---

**Estrategia de Recuperación (RAG):**

_Describa: tipo de chunking, tamaño de chunks, overlap, modelo de embeddings utilizado, función de similitud (cosine/dot), número de documentos recuperados (top-k), y estrategia de re-ranking si aplica._

---

## 4. Diseño de APIs y Conectores

### 4.1 Especificación de Endpoints (API REST / GraphQL)

_Para cada endpoint principal, complete la siguiente tabla. En un proyecto maduro se adjunta el archivo OpenAPI/Swagger como anexo._

| Endpoint         | Método | Descripción                                | Request Body / Params                                               | Response Schema                                                                   |
| ---------------- | ------ | ------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `/api/v1/query`  | `POST` | Envía una consulta al LLM con contexto RAG | `{"query": string, "session_id": string, "context_filter": object}` | `{"response": string, "sources": array, "tokens_used": int, "latency_ms": float}` |
| `/api/v1/ingest` | `POST` | Carga documentos al vector store           | `{"documents": array, "metadata": object}`                          | `{"status": string, "indexed_docs": int, "errors": array}`                        |
| `/api/v1/health` | `GET`  | Health check del sistema                   | N/A                                                                 | `{"status": "healthy\|degraded", "components": object}`                           |
| _[Endpoint]_     |        |                                            |                                                                     |                                                                                   |

### 4.2 Autenticación y Autorización

| Campo                      | Descripción                                                 |
| -------------------------- | ----------------------------------------------------------- |
| **Mecanismo Auth**         | Ej. JWT Bearer Token con OAuth 2.0 via Azure AD             |
| **Proveedor de Identidad** | Ej. AWS Cognito / Okta / Auth0                              |
| **Gestión de Secrets**     | Ej. AWS Secrets Manager / HashiCorp Vault / Azure Key Vault |
| **Rate Limiting**          | Ej. 100 req/min por usuario, 1000 req/min global            |
| **Roles definidos**        | Ej. `admin`, `analyst`, `readonly` — Adjunte matriz RBAC    |

### 4.3 Conectores de Fuentes de Datos

| Fuente de Datos       | Tipo                        | Conector/SDK          | Frecuencia de Sync     | Manejo de Errores           |
| --------------------- | --------------------------- | --------------------- | ---------------------- | --------------------------- |
| Base de datos CRM     | SQL — PostgreSQL            | psycopg2 / SQLAlchemy | Tiempo real (CDC)      | Retry x3, dead-letter queue |
| SharePoint / OneDrive | Documentos no-estructurados | Microsoft Graph API   | Batch diario 02:00 UTC | Alertas email + log         |
| _[Fuente]_            |                             |                       |                        |                             |

---

## 5. Seguridad, Cumplimiento y Ética

### 5.1 Modelo de Amenazas y Controles de Seguridad

| Amenaza / Riesgo   | Vector de Ataque                 | Nivel       | Control Implementado                | Justificación Técnica                                                              |
| ------------------ | -------------------------------- | ----------- | ----------------------------------- | ---------------------------------------------------------------------------------- |
| Prompt Injection   | Input malicioso del usuario      | **ALTO**    | Input sanitization + guardrails LLM | Validación de input, detección de patrones de inyección con regex + LLM classifier |
| Data Leakage       | Respuestas con PII no autorizado | **ALTO**    | Output filtering + PII redaction    | Integración con AWS Comprehend PII detection o equivalente                         |
| API Key Exposure   | Repositorio público / logs       | **CRÍTICO** | Secrets Manager + SAST CI/CD        | Pre-commit hooks, rotación automática de keys                                      |
| DoS / Abuso de API | Volumen excesivo de requests     | **MEDIO**   | Rate limiting + WAF                 | API Gateway throttling + AWS WAF / CloudFlare                                      |
| _[Amenaza]_        |                                  |             |                                     |                                                                                    |

### 5.2 Cumplimiento Regulatorio

| Regulación             | Requerimiento Aplicable                                               | Control Implementado      | Evidencia                 |
| ---------------------- | --------------------------------------------------------------------- | ------------------------- | ------------------------- |
| GDPR (si aplica)       | Derecho al olvido, consentimiento explícito, notificación de breaches | _[Medidas implementadas]_ | _[Link a política / log]_ |
| ISO 27001 / SOC 2      | Gestión de accesos, auditoría, continuidad del negocio                | _[Controles]_             | _[Evidencia]_             |
| Política Interna de IA | Uso responsable de IA, revisión humana de decisiones críticas         | _[Definir]_               | _[Evidencia]_             |
| _[Otra regulación]_    |                                                                       |                           |                           |

### 5.3 Marco Ético de la Solución AI

| Dimensión Ética         | Riesgo Identificado                                          | Mecanismo de Mitigación                                               |
| ----------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------- |
| Sesgos algorítmicos     | El modelo puede perpetuar sesgos del corpus de entrenamiento | Evaluación periódica de outputs + dataset de benchmarking de equidad  |
| Transparencia           | Los usuarios pueden no saber que interactúan con IA          | Disclosure explícito en interfaz + mecanismo de escalamiento a humano |
| Alucinaciones           | El modelo puede generar información falsa con confianza alta | RAG + citación de fuentes + umbral de confianza mínimo configurable   |
| Privacidad de datos     | Inputs del usuario podrían usarse para reentrenamiento       | Opt-out explícito, cero retention policy en APIs de terceros          |
| _[Dimensión adicional]_ |                                                              |                                                                       |

---

## 6. Implementación y Configuración de Infraestructura

### 6.1 Stack Tecnológico y Justificación

| Capa             | Tecnología Seleccionada             | Alternativas Evaluadas             | Razón de Selección                                                                      |
| ---------------- | ----------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------- |
| LLM Provider     | Ej. OpenAI GPT-4o                   | Anthropic Claude 3, Gemini 1.5 Pro | Ej. Mejor relación contexto/precio, ecosystem maduro, soporte function calling avanzado |
| Orquestación     | Ej. LangChain v0.2                  | LlamaIndex, Semantic Kernel        | _[Justificación técnica]_                                                               |
| Backend API      | Ej. FastAPI + Python 3.11           | Flask, Django, Node.js             | _[Justificación]_                                                                       |
| Embeddings       | Ej. text-embedding-3-large          | all-MiniLM-L6-v2, Cohere Embed     | _[Dimensionalidad, performance, costo]_                                                 |
| Vector DB        | _[Ej. Pinecone / Weaviate]_         | _[Alternativas]_                   | _[Justificación]_                                                                       |
| Cloud Provider   | _[AWS / Azure / GCP]_               | _[Alternativas]_                   | _[Justificación]_                                                                       |
| Containerización | Docker + Kubernetes (EKS/AKS/GKE)   | ECS, Cloud Run                     | _[Justificación]_                                                                       |
| CI/CD            | GitHub Actions / GitLab CI          | _[Alternativas]_                   | _[Justificación]_                                                                       |
| Observabilidad   | _[Langfuse / CloudWatch / Grafana]_ | _[Alternativas]_                   | _[Justificación]_                                                                       |

### 6.2 Estructura del Repositorio

```
repo-ai-llm-proyecto/
├── README.md                    # Descripción del proyecto y guía de inicio rápido
├── docs/                        # Documentación técnica
│   ├── architecture/            # Diagramas de arquitectura (PNG, Draw.io, Lucidchart)
│   ├── adr/                     # Architecture Decision Records
│   └── api/                     # OpenAPI/Swagger specs
├── src/                         # Código fuente principal
│   ├── api/                     # Endpoints y routers (FastAPI / Express)
│   ├── core/                    # Lógica de negocio, orquestación LLM
│   ├── rag/                     # Pipeline RAG: ingestion, chunking, retrieval
│   ├── security/                # Guardrails, validación de input/output
│   └── utils/                   # Utilidades compartidas
├── infrastructure/              # IaC (Terraform, CDK, Bicep)
├── tests/                       # Pruebas unitarias, integración, E2E, de carga
├── notebooks/                   # Jupyter notebooks de exploración y evaluación
├── .github/workflows/           # Pipelines CI/CD
├── docker-compose.yml           # Entorno local de desarrollo
├── requirements.txt             # Dependencias Python
└── .env.example                 # Variables de entorno (NUNCA commitear .env real)
```

### 6.3 Variables de Entorno y Configuración

| Variable de Entorno | Descripción                                   | Gestión / Almacenamiento                          |
| ------------------- | --------------------------------------------- | ------------------------------------------------- |
| `OPENAI_API_KEY`    | Clave de autenticación con la API de OpenAI   | AWS Secrets Manager — rotación automática 90 días |
| `VECTOR_DB_URL`     | Endpoint del vector store                     | Parameter Store (SecureString)                    |
| `DATABASE_URL`      | String de conexión a base de datos relacional | Secrets Manager — encriptado con KMS              |
| `LOG_LEVEL`         | Nivel de logging (INFO/DEBUG/WARNING/ERROR)   | Variable de entorno en contenedor — no sensitiva  |
| _[Variable]_        |                                               |                                                   |

---

## 7. Estrategia de Pruebas y Resultados

### 7.1 Plan de Pruebas

| Tipo de Prueba      | Alcance                                                    | Herramienta                   | Criterio de Aceptación                | Estado       |
| ------------------- | ---------------------------------------------------------- | ----------------------------- | ------------------------------------- | ------------ |
| Unitarias           | Funciones de chunking, embeddings, retrievers              | pytest + unittest             | Cobertura > 80%                       | ⬜ Pendiente |
| Integración         | Pipeline RAG end-to-end, APIs internas                     | pytest + Docker Compose       | Todos los flujos críticos validados   | ⬜ Pendiente |
| Rendimiento / Carga | Endpoint `/api/v1/query` bajo carga concurrente            | Locust / k6 / Artillery       | p95 < 2s con 50 usuarios concurrentes | ⬜ Pendiente |
| Seguridad           | OWASP Top 10 para APIs, prompt injection                   | OWASP ZAP + tests manuales    | 0 vulnerabilidades críticas o altas   | ⬜ Pendiente |
| LLM Evaluation      | Calidad de respuestas: coherencia, relevancia, factualidad | RAGAS / LangSmith / Promptfoo | Faithfulness > 0.85, Relevance > 0.80 | ⬜ Pendiente |
| E2E / Aceptación    | Flujos completos desde UI/API hasta respuesta              | Playwright / Postman          | 100% de casos de uso críticos pasan   | ⬜ Pendiente |

### 7.2 Resultados de Pruebas de Rendimiento

_Incluya gráficas y tablas de resultados. Las capturas de pantalla de dashboards (k6, Locust, CloudWatch) deben insertarse como figuras._

| Métrica             | 10 Usuarios Concurrentes | 50 Usuarios | 100 Usuarios | Meta Objetivo |
| ------------------- | ------------------------ | ----------- | ------------ | ------------- |
| Latencia p50 (ms)   | _[XXX]_                  | _[XXX]_     | _[XXX]_      | < 1,000 ms    |
| Latencia p95 (ms)   | _[XXX]_                  | _[XXX]_     | _[XXX]_      | < 2,000 ms    |
| Latencia p99 (ms)   | _[XXX]_                  | _[XXX]_     | _[XXX]_      | < 4,000 ms    |
| Tasa de error (%)   | _[XXX]_                  | _[XXX]_     | _[XXX]_      | < 1%          |
| Throughput (RPS)    | _[XXX]_                  | _[XXX]_     | _[XXX]_      | _[Definir]_   |
| Tokens promedio/req | _[XXX]_                  | _[XXX]_     | _[XXX]_      | _[Definir]_   |

### 7.3 Evaluación de Calidad LLM (LLM-as-Judge)

_Documente los resultados de evaluación con RAGAS, LangSmith, o evaluación manual estructurada._

| Métrica RAGAS / Custom               | Score Obtenido | Score Mínimo Aceptable | ¿Cumple? | Observaciones |
| ------------------------------------ | -------------- | ---------------------- | -------- | ------------- |
| Faithfulness (fidelidad al contexto) | _[0.XX]_       | 0.85                   | ✅ / ❌  |               |
| Answer Relevancy                     | _[0.XX]_       | 0.80                   | ✅ / ❌  |               |
| Context Precision                    | _[0.XX]_       | 0.75                   | ✅ / ❌  |               |
| Context Recall                       | _[0.XX]_       | 0.75                   | ✅ / ❌  |               |
| Hallucination Rate                   | _[X%]_         | < 5%                   | ✅ / ❌  |               |
| _[Métrica personalizada]_            |                |                        |          |               |

---

## 8. Despliegue, Escalabilidad y Costos

### 8.1 Estrategia de Despliegue

| Campo                        | Descripción                                                        |
| ---------------------------- | ------------------------------------------------------------------ |
| **Estrategia de Despliegue** | Ej. Blue-Green deployment con AWS CodeDeploy                       |
| **Herramienta CI/CD**        | Ej. GitHub Actions — workflows: build, test, security-scan, deploy |
| **Infrastructure as Code**   | Ej. Terraform v1.8 — módulos cloud en `/infrastructure/`           |
| **Entornos**                 | Development → Staging → Production                                 |
| **Rollback Strategy**        | Ej. Automático vía health check failure — rollback en < 5 min      |
| **Container Registry**       | Ej. Amazon ECR / GitHub Container Registry / Azure ACR             |
| **Versioning**               | Semantic Versioning (MAJOR.MINOR.PATCH) + Git tags en releases     |

### 8.2 Configuración de Escalabilidad

| Componente                   | Mínimo de Instancias | Máximo de Instancias | Trigger de Auto-Scaling              |
| ---------------------------- | -------------------- | -------------------- | ------------------------------------ |
| API Service (K8s Deployment) | 2 pods               | 20 pods              | CPU > 70% durante 2 min \| RPS > 100 |
| Worker / Background Jobs     | 1 pod                | 10 pods              | Queue length > 100 mensajes          |
| _[Otro componente]_          |                      |                      |                                      |

### 8.3 Análisis y Optimización de Costos

| Servicio / Componente      | Costo Estimado/mes | Costo Real/mes    | Unidad de Medida | Optimización Aplicada                  |
| -------------------------- | ------------------ | ----------------- | ---------------- | -------------------------------------- |
| OpenAI API (input tokens)  | USD $_[XXX]_       | USD $_[XXX]_      | Por 1M tokens    | Prompt caching, compresión de contexto |
| OpenAI API (output tokens) | USD $_[XXX]_       | USD $_[XXX]_      | Por 1M tokens    | Streaming, max_tokens limit            |
| Vector DB                  | USD $_[XXX]_       | USD $_[XXX]_      | Por unidades/mes | _[Optimización]_                       |
| Compute (EKS/AKS/GKE)      | USD $_[XXX]_       | USD $_[XXX]_      | Por hora         | Spot instances, right-sizing           |
| Almacenamiento             | USD $_[XXX]_       | USD $_[XXX]_      | Por GB/mes       | Lifecycle policies, compresión         |
| **TOTAL ESTIMADO**         | **USD $_[TOTAL]_** | **USD $_[REAL]_** |                  |                                        |

---

## 9. Observabilidad y Monitoreo

### 9.1 Stack de Observabilidad

| Categoría                  | Solución Implementada                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------- |
| **Logging**                | Ej. AWS CloudWatch Logs + structured JSON logging con Python `logging` module         |
| **Métricas**               | Ej. Prometheus + Grafana — métricas custom de LLM (token count, latencia, error rate) |
| **Trazabilidad (Tracing)** | Ej. AWS X-Ray / OpenTelemetry + Langfuse para trazas de prompts/respuestas            |
| **Alertas**                | Ej. CloudWatch Alarms → SNS → PagerDuty / Slack webhook                               |
| **Dashboard LLM**          | Ej. Langfuse / LangSmith / Phoenix Arize — evaluación continua de calidad             |
| **SLO/SLA Monitoring**     | Ej. Latencia p95 < 2s medida cada 1 min — alertas si 3 violaciones consecutivas       |

### 9.2 Métricas Clave Monitoreadas

| Métrica                       | Tipo          | Umbral de Alerta         | Acción Automática / Escalamiento          |
| ----------------------------- | ------------- | ------------------------ | ----------------------------------------- |
| Latencia p95 de API           | Rendimiento   | > 2,500 ms               | Auto-scaling trigger + notificación Slack |
| Tasa de error de API          | Confiabilidad | > 2%                     | PagerDuty alert + rollback automático     |
| Tokens consumidos/hora        | Costo         | > 80% del budget mensual | Email al equipo + throttling de requests  |
| Hallucination Rate (LLM Eval) | Calidad       | > 10%                    | Revisión manual + retraining pipeline     |
| Vector Store Query Latency    | Rendimiento   | > 500 ms                 | Cache warming + índice rebuild            |
| _[Métrica custom]_            |               |                          |                                           |

---

## 10. Resultados, Conclusiones y Trabajo Futuro

### 10.1 Resultados Obtenidos vs. Objetivos

| Objetivo               | Meta Planificada    | Resultado Real    | Estado                                  |
| ---------------------- | ------------------- | ----------------- | --------------------------------------- |
| Latencia de respuesta  | p95 < 2 segundos    | _[X.XX] segundos_ | ✅ Logrado / ⚠️ Parcial / ❌ No logrado |
| Calidad de respuestas  | Faithfulness > 0.85 | _[0.XX]_          |                                         |
| Cobertura de pruebas   | > 80%               | _[XX]%_           |                                         |
| Costo operacional      | < USD $_[X]_/mes    | USD $_[Y]_/mes    |                                         |
| _[Objetivo adicional]_ |                     |                   |                                         |

### 10.2 Conclusiones Técnicas

_Mínimo 300 palabras. Responda: ¿Qué funcionó bien y por qué? ¿Qué no funcionó y cuáles fueron los obstáculos? ¿Qué decisiones arquitectónicas resultaron acertadas? ¿Cuáles cambiaría? ¿Qué aprendizajes aplica a proyectos futuros?_

### 10.3 Lecciones Aprendidas

| Categoría                | Lección Aprendida          | Aplicación Futura                                |
| ------------------------ | -------------------------- | ------------------------------------------------ |
| Diseño de Prompts        | _[Descripción de lección]_ | _[Cómo aplicaría esto en el siguiente proyecto]_ |
| Arquitectura de Datos    | _[Descripción]_            | _[Aplicación]_                                   |
| Gestión del Proyecto     | _[Descripción]_            | _[Aplicación]_                                   |
| Seguridad / Cumplimiento | _[Descripción]_            | _[Aplicación]_                                   |
| _[Categoría]_            |                            |                                                  |

### 10.4 Hoja de Ruta — Trabajo Futuro

| Horizonte                 | Mejora / Feature Planeada                                                       | Justificación                  | Complejidad Estimada |
| ------------------------- | ------------------------------------------------------------------------------- | ------------------------------ | -------------------- |
| Corto Plazo (1–3 meses)   | _[Ej. Fine-tuning del modelo con datos propios de la empresa]_                  | _[Mejora esperada en calidad]_ | Alta / Media / Baja  |
| Mediano Plazo (3–6 meses) | _[Ej. Multi-modal: soporte para imágenes y documentos escaneados vía OCR]_      | _[Impacto]_                    |                      |
| Largo Plazo (6–12 meses)  | _[Ej. Sistema de agentes autónomos multi-step para automatización de procesos]_ | _[Impacto]_                    |                      |

---

## 11. Rúbrica de Evaluación

_La puntuación máxima es **4.0** por criterio. El promedio ponderado determina la nota final del módulo._

| Criterio                               | Excepcional (4)                                                                                                                                              | Competente (3)                                                                                                     | En Desarrollo (2)                                                                                          | Insuficiente (1)                                                                              |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **Análisis de Requerimientos** (10%)   | Requerimientos funcionales y no funcionales completamente especificados, priorizados con criterios de aceptación medibles, trazables a objetivos de negocio. | Requerimientos bien documentados con criterios de aceptación. Pequeños gaps en trazabilidad.                       | Requerimientos incompletos o sin criterios de aceptación claros. Falta de priorización.                    | Requerimientos ausentes, genéricos o sin relación con el caso de uso real.                    |
| **Diseño Arquitectónico** (25%)        | Arquitectura técnicamente sólida, completamente justificada, con diagramas C4, decisiones de diseño documentadas (ADRs), y consideración de trade-offs.      | Arquitectura correcta con diagramas claros. Justificaciones presentes pero con algunas decisiones sin fundamentar. | Arquitectura básica presente. Diagramas incompletos. Pocas o ninguna justificación de decisiones técnicas. | Sin diagrama de arquitectura coherente. Componentes mal definidos o sin integración aparente. |
| **Implementación Técnica** (25%)       | Código funcional, modular, bien documentado, con manejo de errores robusto, pruebas con cobertura > 80%, y siguiendo principios SOLID / Clean Architecture.  | Código funcional con estructura razonable. Pruebas básicas presentes (> 50% cobertura). Documentación parcial.     | Código funcional pero monolítico, sin pruebas o con cobertura muy baja (< 30%). Errores sin manejo.        | Código no funcional, sin estructura, sin pruebas, o no disponible en repositorio.             |
| **Seguridad y Cumplimiento** (15%)     | Modelo de amenazas completo, todos los controles implementados y validados, cumplimiento regulatorio documentado con evidencias, marco ético exhaustivo.     | Principales controles de seguridad implementados. Cumplimiento parcialmente documentado. Análisis ético presente.  | Consideraciones de seguridad básicas. Sin validación de cumplimiento. Análisis ético superficial.          | Sin controles de seguridad. Sin consideraciones de cumplimiento ni ética.                     |
| **Pruebas y Validación** (15%)         | Plan de pruebas completo ejecutado. Métricas de rendimiento y calidad LLM documentadas. Todos los KPIs medidos con evidencias.                               | Pruebas funcionales y de rendimiento ejecutadas. Métricas parcialmente reportadas.                                 | Solo pruebas funcionales básicas. Sin pruebas de carga o evaluación LLM. Métricas escasas.                 | Sin evidencia de pruebas realizadas o resultados no disponibles.                              |
| **Documentación y Presentación** (10%) | Documento técnico completo, profesional y preciso. Presentación oral clara, con demo funcional, manejo experto de preguntas técnicas.                        | Documentación completa con pocos errores. Presentación clara con demo. Respuestas adecuadas.                       | Documentación incompleta o con inconsistencias. Presentación básica. Dificultades en preguntas técnicas.   | Documentación ausente o irrelevante. Presentación confusa o sin demo funcional.               |

### Escala de Calificación

| Rango                     | Equivalencia                           |
| ------------------------- | -------------------------------------- |
| 3.6 – 4.0 — Excepcional   | ✅ Aprobado con Distinción             |
| 3.0 – 3.5 — Competente    | ✅ Aprobado                            |
| 2.0 – 2.9 — En Desarrollo | ⚠️ Condicional — revisión requerida    |
| < 2.0 — Insuficiente      | ❌ Reprobado — nueva entrega requerida |

---

### 11.1 Criterios de evaluación

**_Evaluación técnica (70%)_**
| Criterio | Peso |
| ----------------------- | ---- |
| Diseño de arquitectura | 20% |
| Implementación | 20% |
| Almacenamiento en cloud | 15% |
| Automatización | 10% |
| Calidad del código (validacion por 3 IAs) | 5% |

---

**_Conceptual (30%)._**
| Criterio | Peso |
| --------------------- | ---- |
| Justificación técnica | 15% |
| Claridad documental | 10% |
| Defensa de decisiones | 5% |

---

### 11.2 Entregables oficiales

- 👨‍💻Código funcional
- 🏛️Arquitectura documentada
- ☁️Datos en la nube
- 📃README técnico
- 🎥Video de no mas de 30 minutos donde se evidencie el funcionamiento del proyecto

---

## 12. Referencias y Bibliografía

_Liste todas las fuentes citadas en el documento en formato **IEEE** o **APA**. Mínimo **10 referencias** técnicas. Incluya: documentación oficial de APIs/SDKs, papers académicos, libros técnicos, y recursos del curso._

1. M. Kleppmann, _Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems_. Sebastopol, CA: O'Reilly Media, 2017.
2. B. Beyer, C. Jones, J. Petoff, and N. R. Murphy, _Site Reliability Engineering: How Google Runs Production Systems_. Sebastopol, CA: O'Reilly Media, 2016.
3. OpenAI, "GPT-4 Technical Report," arXiv preprint arXiv:2303.08774, 2023. [Online]. Available: https://arxiv.org/abs/2303.08774
4. P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in _Proc. NeurIPS 2020_, vol. 33, pp. 9459–9474.
5. L. Moroney, _AI and Machine Learning for Coders_. Sebastopol, CA: O'Reilly Media, 2020.
6. B. Wilder, _Cloud Architecture Patterns_. Sebastopol, CA: O'Reilly Media, 2012.
7. A. García Serrano, _Inteligencia Artificial: Fundamentos, Práctica y Aplicaciones_. Madrid: RC Libros, 2016.
8. LangChain, "LangChain Documentation v0.2," [Online]. Available: https://python.langchain.com/docs
9. _[Agregue referencia adicional — artículo, documentación oficial, paper]_
10. _[Agregue referencia adicional]_

---

## Anexos

### Anexo A — Architecture Decision Records (ADR)

Utilice una plantilla ADR para documentar cada decisión arquitectónica clave. Mínimo **3 ADRs** requeridos.

```markdown
# ADR-001: [Título descriptivo de la decisión]

**Fecha:** DD/MM/AAAA
**Estado:** Propuesto / Aceptado / Rechazado / Deprecado
**Autores:** [Nombre(s)]

## Contexto

[Describa la situación y el problema que motivó esta decisión arquitectónica.]

## Decisión

[Describa la decisión tomada y cómo resuelve el problema.]

## Consecuencias Positivas

- [Beneficio 1]
- [Beneficio 2]

## Consecuencias Negativas / Trade-offs

- [Desventaja o deuda técnica 1]

## Alternativas Consideradas

- **Opción A:** [Descripción] — Descartada porque [razón]
- **Opción B:** [Descripción] — Descartada porque [razón]
```

---

### Anexo B — Glosario de Términos Técnicos

| Término                                  | Definición                                                                                                                                                                                                 |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RAG** (Retrieval-Augmented Generation) | Técnica que combina recuperación de información relevante de una base de conocimiento externa con la generación de texto de un LLM, reduciendo alucinaciones y mejorando la factualidad de las respuestas. |
| **LLM** (Large Language Model)           | Modelo de lenguaje de gran escala entrenado con enormes corpus de texto usando arquitecturas Transformer, capaz de generar, resumir, traducir y razonar con lenguaje natural.                              |
| **Embeddings**                           | Representaciones vectoriales densas de texto que capturan relaciones semánticas, permitiendo búsqueda por similitud en espacios de alta dimensionalidad.                                                   |
| **Vector Store**                         | Base de datos especializada en almacenar y recuperar eficientemente vectores de alta dimensionalidad mediante algoritmos ANN (Approximate Nearest Neighbors) como HNSW o IVF.                              |
| **Prompt Engineering**                   | Disciplina de diseño y optimización de instrucciones para guiar el comportamiento de LLMs hacia resultados deseados de forma consistente y controlada.                                                     |
| **Guardrails**                           | Mecanismos de control que validan, filtran o restringen los inputs y outputs de un sistema LLM para garantizar seguridad, cumplimiento y adherencia a políticas.                                           |
| **Hallucination**                        | Fenómeno en el que un LLM genera información factualmente incorrecta o inventada con aparente confianza, sin base en los datos de entrenamiento o el contexto provisto.                                    |
| **Fine-tuning**                          | Proceso de ajuste de los pesos de un modelo pre-entrenado sobre un dataset específico del dominio para mejorar su rendimiento en tareas particulares.                                                      |
| **ADR** (Architecture Decision Record)   | Documento que captura una decisión arquitectónica importante, incluyendo contexto, opciones evaluadas, decisión tomada y consecuencias.                                                                    |
| **RAGAS**                                | Framework de evaluación automatizada de pipelines RAG que mide faithfulness, answer relevancy, context precision y context recall.                                                                         |
| _[Término adicional]_                    | _[Definición]_                                                                                                                                                                                             |

---

### Anexo C — Checklist de Entrega Final

Marque cada ítem antes de hacer la entrega final:

- [ ] Documento Markdown completado en todas sus secciones
- [ ] Repositorio Git con código fuente, notebooks y configuración IaC
- [ ] `README.md` del repositorio con instrucciones de despliegue local
- [ ] Diagramas de arquitectura en alta resolución (PNG/SVG en `/docs/architecture/`)
- [ ] ADRs documentados para al menos 3 decisiones arquitectónicas clave (en `/docs/adr/`)
- [ ] Especificación OpenAPI/Swagger del API (YAML/JSON en `/docs/api/`)
- [ ] Reporte de pruebas de rendimiento (k6/Locust outputs)
- [ ] Reporte de evaluación LLM (RAGAS o equivalente)
- [ ] Análisis de costos completo con datos reales del entorno cloud
- [ ] Presentación de diapositivas para la defensa oral (15–20 slides)
- [ ] Video demo del sistema funcionando (máx. 5 minutos — link a YouTube/Drive)
- [ ] Evidencias de pruebas de seguridad (OWASP ZAP reporte o equivalente)

---

_— Fin del Documento —_
_Programa AI-LLM Solution Architect | Curso 5: Proyecto Final_
