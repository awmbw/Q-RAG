FROM python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

ARG WITH_MODELS=1
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
ARG TORCH_VERSION=2.15.0+cpu
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/home/app/.cache/huggingface \
    HF_HUB_OFFLINE=1 \
    TOKENIZERS_PARALLELISM=false \
    QRAG_DEVICE=cpu
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml requirements-baselines.lock requirements-container.lock requirements-container-service.lock ./
COPY src ./src
RUN python -m pip install --no-cache-dir -r requirements-baselines.lock -r requirements-container-service.lock
RUN if [ "$WITH_MODELS" = "1" ]; then python -m pip install --no-cache-dir "torch==$TORCH_VERSION" --index-url "$TORCH_INDEX"; fi
RUN if [ "$WITH_MODELS" = "1" ]; then python -m pip install --no-cache-dir -r requirements-container.lock; fi
RUN python -m pip install --no-cache-dir --no-deps .
RUN useradd --uid 10001 --create-home app && mkdir -p /app/.cache && chown -R 10001:10001 /app/.cache
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]
CMD ["uvicorn", "qrag_service.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
