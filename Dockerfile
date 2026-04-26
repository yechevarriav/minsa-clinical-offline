FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Instalar todo EXCEPTO torch
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.0 \
    python-multipart==0.0.6 \
    pandas==2.1.3 \
    numpy==1.26.2 \
    openpyxl==3.1.5 \
    requests==2.31.0 \
    sqlalchemy==2.0.23 \
    python-dotenv==1.0.0 \
    python-json-logger==2.0.7 \
    prometheus-client==0.19.0 \
    scikit-learn==1.3.2 \
    faiss-cpu==1.7.4 \
    transformers==4.35.2 \
    sentence-transformers==2.2.2 \
    langchain==0.0.352 \
    langchain-community==0.0.10

# Instalar torch CPU por separado
RUN pip install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

COPY src/ /app/src/
COPY data/ /app/data/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "offline_clinic.main:app", "--host", "0.0.0.0", "--port", "8000"]
