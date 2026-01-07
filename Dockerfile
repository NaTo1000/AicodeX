# Multi-stage Dockerfile for AicodeX

# Stage 1: Build Rust binary
FROM rust:1.75-slim as rust-builder
WORKDIR /build
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release

# Stage 2: Build Python package
FROM python:3.11-slim as python-builder
WORKDIR /build
COPY pyproject.toml VERSION ./
COPY src/aicodex ./src/aicodex
RUN pip install --no-cache-dir build && \
    python -m build

# Stage 3: Build TypeScript
FROM node:20-alpine as ts-builder
WORKDIR /build
COPY package.json tsconfig.json ./
COPY src/index.ts ./src/
RUN npm ci && \
    npm run build

# Stage 4: Final runtime image
FROM ubuntu:22.04
LABEL org.opencontainers.image.title="AicodeX"
LABEL org.opencontainers.image.description="A companion overlay code engine"
LABEL org.opencontainers.image.source="https://github.com/NaTo1000/AicodeX"
LABEL org.opencontainers.image.licenses="MIT"

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    nodejs \
    npm \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built artifacts
COPY --from=rust-builder /build/target/release/aicodex /usr/local/bin/
COPY --from=python-builder /build/dist/*.whl /tmp/
COPY --from=ts-builder /build/dist /app/dist

# Install Python package
RUN pip3 install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Copy additional files
COPY README.md LICENSE ./

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PATH="/usr/local/bin:${PATH}"

# Default command
CMD ["aicodex"]
