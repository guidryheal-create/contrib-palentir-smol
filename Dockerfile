# Multi-stage Dockerfile for Palentir OSINT

# Stage 1: Base Python image with dependencies
FROM python:3.12-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY kitten-palentir ./kitten-palentir
COPY . .

# Install dependencies using UV
RUN uv sync --frozen

# Stage 2: API Server
FROM base as api

WORKDIR /app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "kitten_palentir.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 3: Frontend Server
FROM base as frontend

WORKDIR /app

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "kitten_palentir/frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]

# Stage 4: Development
FROM base as development

WORKDIR /app

# Install development dependencies
RUN uv sync --frozen --all-extras

EXPOSE 8000 8501

CMD ["/bin/bash"]

# Stage 5: Production
FROM python:3.12-slim as production

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files from base
COPY --from=base /app/kitten-palentir ./kitten-palentir
COPY --from=base /app/pyproject.toml ./

# Install UV in production image
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install dependencies
RUN uv sync --frozen --no-dev

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "kitten_palentir.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
