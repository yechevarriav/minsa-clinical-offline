# ============================================================================
# STAGE 1: Builder
# ============================================================================
FROM python:3.12-slim as builder

WORKDIR /app

# Instalar dependencias del sistema para compilar
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Crear virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt


# ============================================================================
# STAGE 2: Runtime
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias runtime solo
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar venv desde builder
COPY --from=builder /opt/venv /opt/venv

# Copiar código fuente
COPY src/ /app/src/
COPY data/ /app/data/
COPY main.py /app/

# Variables de entorno
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
