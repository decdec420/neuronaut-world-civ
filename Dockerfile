# Neuronaut World: the simulation, its API and the /app dashboard.
#
#   docker build -t neuronaut-world .
#   docker run -p 8000:8000 -v neuronaut-data:/data \
#       -e NEURONAUT_ADMIN_TOKEN=change-me neuronaut-world
#
# Then open http://localhost:8000/app. Saves (and autosaves) go to /data/saves.
# For AI-driven agents with Ollama on the host, add:
#   -e USE_LLM_DECISIONS=true -e OLLAMA_BASE_URL=http://host.docker.internal:11434
#   (on Linux also: --add-host=host.docker.internal:host-gateway)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    SAVE_DIR=/data/saves \
    USE_LLM_DECISIONS=false

WORKDIR /app

COPY requirements-minimal.txt .
# Behind a proxy that re-signs TLS, pass its CA as a build secret (it is used
# for this step only and never stored in the image):
#   docker build --secret id=ca,src=/path/to/ca.crt ...
RUN --mount=type=secret,id=ca,required=false \
    if [ -s /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca; fi; \
    pip install -r requirements-minimal.txt

COPY . .

# Run as an unprivileged user; it may write only to /data
RUN useradd --create-home --uid 10001 neuronaut \
    && mkdir -p /data/saves \
    && chown -R neuronaut:neuronaut /data
USER neuronaut
VOLUME ["/data"]

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '8000'), timeout=4)"

CMD ["python", "main.py"]
