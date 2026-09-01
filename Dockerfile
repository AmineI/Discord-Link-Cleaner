FROM debian:trixie-slim AS url-sanitize-installer

RUN apt-get update \
  && apt-get install --yes --no-install-recommends ca-certificates curl \
  && curl --proto '=https' --tlsv1.2 --location --silent --show-error --fail \
    --output /tmp/url-sanitize-installer.sh \
    https://github.com/antonio-orionus/url-sanitize/releases/latest/download/url-sanitize-installer.sh \
  && sh /tmp/url-sanitize-installer.sh

FROM python:3.12-slim

# Create a non-root user and set permissions for the data directory
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

WORKDIR /app
ENV DATA_DIR=/data


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV URL_SANITIZE_BIN=/usr/local/bin/url-sanitize-native
COPY --from=url-sanitize-installer /root/.local/bin/url-sanitize /usr/local/bin/url-sanitize-native
# Test url-sanitize
RUN python -c "from url_sanitize import sanitize; print(sanitize('https://example.com/?utm_source=test'))"

COPY --chown=appuser:appuser main.py .

USER appuser
VOLUME ["/data"]
CMD ["python", "main.py"]