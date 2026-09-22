# Dockerfile
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y curl gnupg python3.14 python3.14-venv && rm -rf /var/lib/apt/lists/*

# Copy local GenLayer SDK (already downloaded by gltest)
COPY ~/.cache/gltest-direct/extracted/v0.3.0-rc7/py-lib-genlayer-std /opt/genlayer-sdk

WORKDIR /app
COPY . /app

# Set PYTHONPATH to use the real GenLayer SDK
ENV PYTHONPATH=/opt/genlayer-sdk/11rhn002yfajawsz7fai6mykznbxkxs6l91iskj5cm82c92qhy3v:$PYTHONPATH

RUN python3.14 -m venv .venv && . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --upgrade genlayer-sdk

CMD ["bash","-c","source .venv/bin/activate && \
    python -m pytest tests/direct/test_agent_coordination.py -v"]
