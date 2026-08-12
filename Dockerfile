FROM python:3.12-slim

# Create a non-root user and set permissions for the data directory
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

WORKDIR /app
ENV DATA_DIR=/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser main.py .

USER appuser
VOLUME ["/data"]
CMD ["python", "main.py"]