FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build data artifacts into the image so startup is instant
RUN python -m ingest.fetch_mit && \
    python -m ingest.parse_courses && \
    python -m ingest.embed_courses

EXPOSE 8000
CMD ["./start.sh"]
