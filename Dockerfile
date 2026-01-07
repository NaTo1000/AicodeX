# Multi-stage build for AicodeX
FROM ubuntu:22.04 as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

# Copy dependency files first for better caching
COPY pyproject.toml package.json Cargo.toml ./
COPY src/aicodex/__init__.py src/aicodex/

# Install dependencies
RUN python3 -m pip install --upgrade pip build
RUN python3 -m pip install -e .[dev]
RUN npm install

# Copy source code
COPY . .

# Build all components
RUN make build-release

# Runtime stage
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built artifacts from builder
COPY --from=builder /build/dist /app/dist
COPY --from=builder /build/target/release/aicodex /app/aicodex

# Install Python package
RUN python3 -m pip install --no-cache-dir dist/*.whl

EXPOSE 8080

CMD ["aicodex"]
