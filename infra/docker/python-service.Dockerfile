FROM python:3.12-slim AS builder

ARG SERVICE_DIR
ARG INSTALL_CPU_TORCH=false
ARG TORCH_CPU_INDEX_URL=https://download.pytorch.org/whl/cpu

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /workspace/${SERVICE_DIR}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY ${SERVICE_DIR}/requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:${PATH}"

RUN pip install --upgrade pip \
    && if [ "${INSTALL_CPU_TORCH}" = "true" ]; then \
        pip install --index-url "${TORCH_CPU_INDEX_URL}" torch; \
    fi \
    && pip install -r /tmp/requirements.txt

FROM python:3.12-slim AS runtime

ARG SERVICE_DIR

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace/${SERVICE_DIR}

COPY --from=builder /opt/venv /opt/venv
COPY ${SERVICE_DIR} /workspace/${SERVICE_DIR}

EXPOSE 8000 8001 8002 8003 8004
