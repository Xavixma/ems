ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-python:3.12
FROM ${BUILD_FROM}

ENV LANG C.UTF-8
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY core/ ./core/
COPY integrations/ ./integrations/
COPY ems/run.sh /run.sh
RUN chmod a+x /run.sh
