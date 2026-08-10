FROM python:3.13-slim@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_ROOT_USER_ACTION=ignore
ENV JEDI_RUNTIME_ROLE=api
ENV JEDI_AUDIT_ROOT=/app/artifacts/audit

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

RUN groupadd --system jedi \
    && useradd --system --gid jedi --home-dir /app --shell /usr/sbin/nologin jedi \
    && mkdir -p /app/artifacts/audit \
    && chown -R jedi:jedi /app

EXPOSE 8000

HEALTHCHECK --start-period=20s --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT:-8000}/health', timeout=3).read()"

USER jedi

CMD ["sh", "-c", "exec uvicorn jedi_devproject.runtime_api:build_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
