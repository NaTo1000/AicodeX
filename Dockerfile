# AicodeX — hardened, multi-stage build.
#
# Hardening:
#   * multi-stage build keeps build tooling out of the runtime image
#   * pinned, minimal base image (slim) — override with --build-arg for a digest
#   * runs as a non-root user
#   * no secrets, tokens, or credentials are copied into the image
#   * dropped default shell capabilities by running the app, not a shell

# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.11-slim

# ---------------------------------------------------------------------------
# Builder stage — install dependencies into an isolated prefix.
# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Install only what is needed to build wheels.
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Runtime stage — minimal, non-root.
# ---------------------------------------------------------------------------
FROM ${PYTHON_IMAGE} AS runtime

LABEL org.opencontainers.image.title="AicodeX" \
      org.opencontainers.image.description="AicodeX companion overlay code engine" \
      org.opencontainers.image.licenses="SEE LICENSE" \
      org.opencontainers.image.source="https://github.com/NaTo1000/AicodeX"

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a dedicated non-root user.
RUN groupadd --system aicodex && useradd --system --gid aicodex --no-create-home aicodex

COPY --from=builder /opt/venv /opt/venv
COPY src/ /app/src/
COPY edition2/ /app/edition2/
COPY config/ /app/config/

WORKDIR /app
USER aicodex

ENTRYPOINT ["python", "src/main.py"]
CMD ["--help"]
