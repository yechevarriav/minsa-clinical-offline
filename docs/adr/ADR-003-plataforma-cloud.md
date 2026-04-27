# ADR-003: Selección de Plataforma Cloud para Despliegue

**Fecha:** Abril 2026
**Estado:** Aceptado (temporal)
**Autores:** Yvonne Patricia Echevarría Vargas
**Contexto del proyecto:** Sistema de Soporte Clínico Offline — MINSA Perú — E4 Deployment

---

## Contexto

El E4 requiere desplegar el sistema con URL pública accesible. La arquitectura target original era AWS ECS + Fargate. Sin embargo, durante el período de entrega se presentaron restricciones que obligaron a evaluar alternativas.

**Restricciones identificadas:**
- Cuenta AWS (ID: 499872649000) bloqueada por verificación — no permite lanzar instancias EC2/ECS
- Error específico: `Unable to assume the service linked role` al crear ECS Cluster
- AWS Support contactado vía caso de soporte (Account Verification/Reactivation)
- Deadline de presentación: 26/04/2026 — no hay tiempo de esperar resolución AWS

**Requisitos del despliegue:**
- ≥2 GB RAM (FAISS + RoBERTa + FastAPI)
- Soporte Docker (Dockerfile existente)
- URL pública estable
- Deploy desde GitHub automático
- Costo razonable para demo académico

## Decisión

**Seleccionar: Render.com Web Service Standard ($25/mes)**

URL pública: `https://minsa-clinical-offline.onrender.com`

## Alternativas Consideradas

| Plataforma | RAM | Costo | Docker | Auto-deploy | Estado |
|------------|-----|-------|--------|-------------|--------|
| **AWS ECS Fargate** | 4-8 GB | ~$78/mes | ✅ | ✅ | ❌ Cuenta bloqueada |
| **Render Standard** | 2 GB | $25/mes | ✅ | ✅ | ✅ **ELEGIDO** |
| Railway | 2 GB | $20/mes | ✅ | ✅ | ❌ Incompatibilidad deps |
| Replit Core | 2 GB | $20/mes | ✅ | ✅ | ❌ Precio subió a $20 |
| Google Cloud Run | Variable | >$30/mes | ✅ | ✅ | ❌ Complejidad + costo |
| Azure Container | Variable | >$30/mes | ✅ | ✅ | ❌ Complejidad |
| Fly.io | 256MB-2GB | $3-20/mes | ✅ | ✅ | ❌ RAM insuficiente Free |

## Justificación

**¿Por qué Render.com?**

1. **Deploy inmediato desde Dockerfile:** Detecta automáticamente el Dockerfile y construye sin configuración adicional.
2. **2GB RAM suficiente:** FAISS (500MB) + RoBERTa (500MB) + FastAPI (200MB) = ~1.2GB — cabe en 2GB.
3. **Auto-deploy desde GitHub:** Cada push a main redeploya automáticamente.
4. **URL estable:** Dominio `onrender.com` persistente, sin rotación de IPs.
5. **Precio competitivo:** $25/mes vs $78/mes de AWS — 68% más económico para demo.

## Arquitectura Implementada en Render

```
GitHub push → Render build (Docker) → Deploy
                                         ↓
                              FastAPI arranca (puerto 8000)
                                         ↓
                              FAISS carga en background
                              (~5 min primera vez)
                                         ↓
                              models_ready: true
                              URL pública disponible
```

## Arquitectura Target AWS (cuando se resuelva bloqueo)

```
Internet (HTTPS 443)
    ↓
ALB (Application Load Balancer)
    ↓
ECS Cluster (Fargate) — us-east-1
    └── Task: minsa-clinical (2GB RAM, 1 vCPU)
        └── Container: ECR → minsa-clinical-offline:latest
CloudWatch Logs: /ecs/minsa-clinical
```

**Componentes AWS ya configurados:**
- ✅ IAM: `minsa-github-deploy` con políticas ECR+ECS+ELB
- ✅ ECR: `499872649000.dkr.ecr.us-east-1.amazonaws.com/minsa-clinical-offline`
- ✅ GitHub Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- ❌ ECS Cluster: bloqueado por verificación de cuenta

## Consecuencias Positivas

- ✅ Deploy funcional en <2 horas desde decisión
- ✅ URL pública estable para presentación
- ✅ CI/CD automático desde GitHub
- ✅ Costo $25/mes — dentro del presupuesto demo
- ✅ Sin LLM en cloud (solo búsqueda semántica) — suficiente para demo

## Consecuencias Negativas / Trade-offs

- ❌ Sin Ollama/Llama-2 en cloud (2GB RAM no alcanza para LLM)
- ❌ Sin auto-scaling (plan Standard, 1 instancia fija)
- ❌ Sin SLA enterprise (apropiado para demo, no producción)
- ❌ No es la arquitectura target final (AWS ECS)
- ⚠️ Cold start si servicio inactivo >15 min (plan Free — no aplica a Standard)

## Plan de Migración a AWS

| Paso | Acción | Tiempo estimado |
|------|--------|----------------|
| 1 | Resolver bloqueo cuenta AWS vía Support | 1-3 días hábiles |
| 2 | Crear ECS Cluster `minsa-clinical-prod` | 15 min |
| 3 | Crear Task Definition (2GB RAM, Fargate) | 20 min |
| 4 | Crear ALB + Target Group | 20 min |
| 5 | Crear ECS Service (2 instancias) | 15 min |
| 6 | Actualizar `deploy.yml` con ECS action | 10 min |
| 7 | Actualizar README con URL ALB | 5 min |

## Estado en E4

- ✅ Render.com funcionando: https://minsa-clinical-offline.onrender.com
- ✅ models_ready: true (FAISS + RoBERTa cargados)
- ✅ Búsqueda CIE-10 operativa (resultados reales)
- ✅ Frontend HTML accesible públicamente
- ⏳ AWS pendiente resolución de bloqueo de cuenta
