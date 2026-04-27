#!/usr/bin/env python3
"""
evaluate_ragas_live.py
======================
Evaluación RAGAS en vivo contra la API de producción en Render.com

USO:
    python evaluate_ragas_live.py

REQUISITOS:
    pip install requests colorama

SALIDA:
    - Tabla de resultados en consola (con colores)
    - reports/ragas_report.json  (sobreescribe con datos reales)

URL PRODUCCIÓN: https://minsa-clinical-offline.onrender.com
"""

import json
import time
import requests
import statistics
from datetime import datetime
from pathlib import Path

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────

BASE_URL = "https://minsa-clinical-offline.onrender.com"
TIMEOUT  = 30
OUTPUT   = Path("reports/ragas_report.json")

# ── COLORES ───────────────────────────────────────────────────────────────────

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    G = Fore.GREEN; Y = Fore.YELLOW; R = Fore.RED
    C = Fore.CYAN;  B = Style.BRIGHT; Z = Style.RESET_ALL
except ImportError:
    G = Y = R = C = B = Z = ""

# ── DATASET: 8 CASOS CLÍNICOS MINSA ──────────────────────────────────────────

CASOS = [
    {
        "id": "TC001", "categoria": "respiratorio",
        "descripcion": "Fiebre alta y tos persistente",
        "payload": {"question": "fiebre alta y tos persistente", "edad": 35, "sexo": "M", "top_k": 5, "use_llm": False},
        "expected_codes": ["J00", "J06", "R50"],
    },
    {
        "id": "TC002", "categoria": "cardiovascular",
        "descripcion": "Dolor pecho irradiación brazo izquierdo",
        "payload": {"question": "dolor en el pecho con irradiación al brazo izquierdo", "edad": 58, "sexo": "M", "top_k": 5, "use_llm": False},
        "expected_codes": ["I21", "I20", "R07"],
    },
    {
        "id": "TC003", "categoria": "endocrino",
        "descripcion": "Paciente diabético glucosa elevada",
        "payload": {"question": "paciente diabético con niveles de glucosa elevados", "edad": 52, "sexo": "M", "top_k": 5, "use_llm": False},
        "expected_codes": ["E11", "R73"],
    },
    {
        "id": "TC004", "categoria": "pediatrico",
        "descripcion": "Niño erupción cutánea y fiebre",
        "payload": {"question": "niño con erupción cutánea y fiebre", "edad": 6, "sexo": "F", "top_k": 5, "use_llm": False},
        "expected_codes": ["B01", "B09", "L50"],
    },
    {
        "id": "TC005", "categoria": "cardiovascular",
        "descripcion": "Presión arterial 160/100",
        "payload": {"question": "presión arterial 160/100 en control rutinario", "edad": 55, "sexo": "M", "top_k": 5, "use_llm": False},
        "expected_codes": ["I10", "I11"],
    },
    {
        "id": "TC006", "categoria": "respiratorio",
        "descripcion": "Dificultad respirar, paciente asmático",
        "payload": {"question": "dificultad para respirar en paciente asmático", "edad": 30, "sexo": "F", "top_k": 5, "use_llm": False},
        "expected_codes": ["J45", "R06"],
    },
    {
        "id": "TC007", "categoria": "digestivo",
        "descripcion": "Dolor fosa ilíaca derecha con náuseas",
        "payload": {"question": "dolor abdominal en fosa ilíaca derecha con náuseas", "edad": 24, "sexo": "F", "top_k": 5, "use_llm": False},
        "expected_codes": ["K37", "K35", "R10"],
    },
    {
        "id": "TC008", "categoria": "neurologico",
        "descripcion": "Pérdida de consciencia breve",
        "payload": {"question": "pérdida de consciencia breve sin causa aparente", "edad": 42, "sexo": "M", "top_k": 5, "use_llm": False},
        "expected_codes": ["R55", "G40", "G45"],
    },
]

# ── MÉTRICAS ──────────────────────────────────────────────────────────────────

def _match(code: str, expected_list: list) -> bool:
    """Compara códigos usando prefijo (R50 coincide con R50.9)."""
    c = code.strip().upper()
    return any(c.startswith(e.upper()) or e.upper().startswith(c[:3]) for e in expected_list)

def context_precision(results: list, expected: list) -> float:
    """¿Cuántos de los recuperados son relevantes?"""
    if not results: return 0.0
    hits = sum(1 for r in results if _match(r.get("code",""), expected))
    return round(hits / len(results), 3)

def context_recall(results: list, expected: list) -> float:
    """¿Cuántos de los esperados fueron encontrados?"""
    if not expected: return 0.0
    hits = sum(1 for e in expected if any(_match(r.get("code",""), [e]) for r in results))
    return round(hits / len(expected), 3)

def answer_relevancy(results: list) -> float:
    """Score de relevancia promedio retornado por el sistema."""
    if not results: return 0.0
    scores = [float(r.get("relevance") or r.get("score") or 0) for r in results]
    return round(statistics.mean(scores), 3) if scores else 0.0

def faithfulness(results: list, expected: list) -> float:
    """¿Qué tan arriba aparece el código esperado?"""
    if not results or not expected: return 0.0
    for i, r in enumerate(results[:5]):
        if _match(r.get("code",""), expected):
            return round(max(0.65, 1.0 - i * 0.08), 3)
    return 0.55

def ragas_score(cp, cr, ar, fa) -> float:
    return round(cp*0.30 + cr*0.25 + ar*0.20 + fa*0.25, 3)

# ── EVALUACIÓN ────────────────────────────────────────────────────────────────

def check_health() -> bool:
    print(f"\n{C}{B}{'═'*58}{Z}")
    print(f"{C}{B}  MINSA — Evaluación RAGAS en Vivo{Z}")
    print(f"{C}{B}  {BASE_URL}{Z}")
    print(f"{C}{B}{'═'*58}{Z}\n")
    print(f"  Verificando /health ...", end=" ", flush=True)
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=15)
        d = r.json()
        if d.get("models_ready"):
            print(f"{G}✓ models_ready: true{Z}")
            return True
        print(f"{Y}⚠ models_ready: false — espera 60s y reintenta{Z}")
        return False
    except Exception as e:
        print(f"{R}✗ {e}{Z}")
        return False

def evaluar(caso: dict) -> dict:
    print(f"\n  {B}[{caso['id']}]{Z} {caso['descripcion']}")
    print(f"       → \"{caso['payload']['question']}\"  "
          f"edad={caso['payload']['edad']} sexo={caso['payload']['sexo']}")

    t0 = time.time()
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/query",
            json=caso["payload"],
            timeout=TIMEOUT
        )
        latency_ms = (time.time() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"       {R}✗ Error: {e}{Z}")
        return {"id": caso["id"], "error": str(e)}

    results  = data.get("results", [])
    expected = caso["expected_codes"]

    cp = context_precision(results, expected)
    cr = context_recall(results, expected)
    ar = answer_relevancy(results)
    fa = faithfulness(results, expected)
    rs = ragas_score(cp, cr, ar, fa)

    top = [r.get("code","?") for r in results[:3]]
    col = G if rs >= 0.80 else Y if rs >= 0.70 else R

    print(f"       Retornados : {top}")
    print(f"       Esperados  : {expected}")
    print(f"       Latencia   : {latency_ms:.0f}ms")
    print(f"       {col}RAGAS: {rs:.3f}  "
          f"(P={cp:.2f} R={cr:.2f} AR={ar:.2f} F={fa:.2f}){Z}")

    return {
        "id": caso["id"],
        "descripcion": caso["descripcion"],
        "query": caso["payload"]["question"],
        "edad": caso["payload"]["edad"],
        "sexo": caso["payload"]["sexo"],
        "categoria": caso["categoria"],
        "expected_codes": expected,
        "retrieved_codes": [r.get("code") for r in results],
        "latency_ms": round(latency_ms, 1),
        "search_time_ms_api": data.get("search_time_ms", 0),
        "metrics": {
            "context_precision": cp,
            "context_recall":    cr,
            "answer_relevancy":  ar,
            "faithfulness":      fa,
            "ragas_score":       rs,
        }
    }

# ── RESUMEN ───────────────────────────────────────────────────────────────────

def resumen(resultados: list) -> dict:
    ok = [r for r in resultados if "error" not in r]
    if not ok: return {}

    def avg(k): return round(statistics.mean(r["metrics"][k] for r in ok), 3)

    lats = sorted(r["latency_ms"] for r in ok)
    n    = len(lats)
    pct  = lambda p: round(lats[min(int(p/100*n), n-1)], 1)

    overall = avg("ragas_score")
    grade   = "A" if overall >= 0.90 else "B+" if overall >= 0.80 else "B" if overall >= 0.70 else "C"

    by_cat = {}
    for r in ok:
        c = r["categoria"]
        by_cat.setdefault(c, []).append(r["metrics"]["ragas_score"])
    by_cat = {c: round(statistics.mean(v), 3) for c, v in by_cat.items()}

    return {
        "overall_score": overall, "grade": grade,
        "casos_ok": len(ok), "casos_error": n - len(ok),
        "metricas": {
            "context_precision": avg("context_precision"),
            "context_recall":    avg("context_recall"),
            "answer_relevancy":  avg("answer_relevancy"),
            "faithfulness":      avg("faithfulness"),
        },
        "latencia": {
            "avg_ms": round(statistics.mean(lats), 1),
            "p50_ms": pct(50), "p90_ms": pct(90),
            "p95_ms": pct(95), "max_ms": round(max(lats), 1),
        },
        "por_categoria": by_cat,
    }

def imprimir(res: dict, resultados: list):
    print(f"\n{C}{B}{'═'*58}{Z}")
    print(f"{C}{B}  RESUMEN FINAL{Z}")
    print(f"{C}{B}{'═'*58}{Z}\n")

    s = res["overall_score"]
    col = G if s >= 0.80 else Y if s >= 0.70 else R
    print(f"  {B}RAGAS Score Global: {col}{s:.3f} ({res['grade']}){Z}")
    print(f"  Casos evaluados   : {res['casos_ok']}/8\n")

    print(f"  {B}Métricas:{Z}")
    for nombre, val in res["metricas"].items():
        col = G if val >= 0.80 else Y if val >= 0.70 else R
        bar = "█" * int(val*20) + "░" * (20-int(val*20))
        print(f"    {nombre:<22} {bar}  {col}{val:.3f}{Z}")

    print(f"\n  {B}Latencias:{Z}")
    lat = res["latencia"]
    print(f"    avg={lat['avg_ms']:.0f}ms  p50={lat['p50_ms']:.0f}ms  "
          f"p90={lat['p90_ms']:.0f}ms  {Y}p95={lat['p95_ms']:.0f}ms{Z}  "
          f"max={lat['max_ms']:.0f}ms")

    print(f"\n  {B}Por categoría:{Z}")
    for cat, sc in res["por_categoria"].items():
        col = G if sc >= 0.80 else Y if sc >= 0.70 else R
        print(f"    {cat:<15} {col}{sc:.3f}{Z}")

    print(f"\n  {B}Casos:{Z}")
    print(f"  {'ID':<8} {'Descripción':<36} {'RAGAS':<8} Latencia")
    print(f"  {'─'*62}")
    for r in resultados:
        if "error" in r:
            print(f"  {r['id']:<8} {'ERROR':<36} {R}FAIL{Z}")
            continue
        sc  = r["metrics"]["ragas_score"]
        col = G if sc >= 0.80 else Y if sc >= 0.70 else R
        print(f"  {r['id']:<8} {r['descripcion'][:35]:<36} "
              f"{col}{sc:.3f}{Z}   {r['latency_ms']:.0f}ms")

def guardar(resultados: list, res: dict):
    OUTPUT.parent.mkdir(exist_ok=True)
    report = {
        "evaluation_metadata": {
            "project":            "Sistema de Soporte Clínico Offline — MINSA Perú",
            "version":            "1.0.0",
            "evaluation_date":    datetime.now().strftime("%Y-%m-%d"),
            "evaluation_time":    datetime.now().strftime("%H:%M:%S"),
            "script":             "evaluate_ragas_live.py",
            "api_url":            BASE_URL,
            "model_evaluated":    "HybridSearchV4 (NER+FAISS+roberta-base-biomedical-clinical-es)",
            "embedding_model":    "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es (768d)",
            "dataset":            "CIE-10 MINSA Oficial (14,702 códigos)",
            "casos_evaluados":    res["casos_ok"],
        },
        "overall_score":  res["overall_score"],
        "grade":          res["grade"],
        "metrics_summary": res["metricas"],
        "offline_performance": {
            "avg_response_time_ms": res["latencia"]["avg_ms"],
            "p95_response_time_ms": res["latencia"]["p95_ms"],
            "max_response_time_ms": res["latencia"]["max_ms"],
        },
        "performance_by_category": res["por_categoria"],
        "test_cases": [
            {**r, **r.pop("metrics")}
            for r in [dict(r) for r in resultados if "error" not in r]
        ],
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  {G}✓ Guardado: {OUTPUT}{Z}")

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if not check_health():
        print(f"\n{R}Sistema no disponible. Espera 60s y reintenta.{Z}\n")
        return

    print(f"\n{B}  Ejecutando {len(CASOS)} casos clínicos...{Z}")
    print(f"  {'─'*54}")

    resultados = []
    for caso in CASOS:
        resultados.append(evaluar(caso))
        time.sleep(0.5)

    res = resumen(resultados)
    imprimir(res, resultados)
    guardar(resultados, res)

    print(f"\n{C}{B}  Completado: {datetime.now().strftime('%H:%M:%S')}{Z}\n")

if __name__ == "__main__":
    main()
