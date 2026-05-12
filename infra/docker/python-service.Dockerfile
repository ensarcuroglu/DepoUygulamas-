FROM python:3.12-slim

ARG SERVICE_DIR

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /workspace/${SERVICE_DIR}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY ${SERVICE_DIR}/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY ${SERVICE_DIR} /workspace/${SERVICE_DIR}

EXPOSE 8000 8001 8002 8003
