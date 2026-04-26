FROM python:3.12-slim

ENV LANG C.UTF-8
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends jq && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY core/ ./core/
COPY integrations/ ./integrations/
COPY ems/run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
