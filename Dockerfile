FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    curl \
    gnupg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN npm install -g genlayer

WORKDIR /app
COPY . /app

RUN python3.12 -m venv .venv

CMD ["bash", "-c", "\
    source .venv/bin/activate && \
    echo '=== Direct Unit Tests ===' && \
    python3.12 -m pytest tests/direct/test_agent_coordination.py -v 2>&1 || true && \
    echo '' && \
    echo '=== Integration Tests ===' && \
    gltest tests/integration/ -v -s 2>&1 || true \
"]
