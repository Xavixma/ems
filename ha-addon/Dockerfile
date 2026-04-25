ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

WORKDIR /app

# aiohttp (pulled by influxdb-client[async]) has C extensions that need
# build tools on Alpine; install and remove in one layer to keep image lean
COPY requirements.txt .
RUN apk add --no-cache gcc musl-dev libffi-dev && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev libffi-dev

# Copy application code.
# Build context must be the project root:
#   docker build -f ha-addon/Dockerfile .
COPY api/ ./api/
COPY core/ ./core/
COPY integrations/ ./integrations/
COPY static/ ./static/

COPY ha-addon/run.sh /run.sh
RUN chmod a+x /run.sh
