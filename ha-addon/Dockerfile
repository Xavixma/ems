FROM ghcr.io/home-assistant/aarch64-base-python:3.12

ENV LANG C.UTF-8
WORKDIR /app

COPY requirements.txt .
RUN apk add --no-cache gcc musl-dev libffi-dev && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev libffi-dev

COPY api/ ./api/
COPY core/ ./core/
COPY integrations/ ./integrations/
COPY ha-addon/run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
