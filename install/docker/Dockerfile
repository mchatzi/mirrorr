FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        rsync \
        openssh-client \
        sudo \
        procps \
        iproute2 \
    && rm -rf /var/lib/apt/lists/*

COPY install/requirements-web.txt /tmp/requirements-web.txt
COPY install/requirements-mirrorr.txt /tmp/requirements-mirrorr.txt

COPY . /opt/mirrorr
RUN rm -rf /opt/mirrorr/app/web/.venv
RUN rm -rf /opt/mirrorr/app/sys/.venv

WORKDIR /opt/mirrorr/app/web
RUN python3 -m venv .venv
RUN .venv/bin/pip install --no-cache-dir \
    -r /tmp/requirements-web.txt

WORKDIR /opt/mirrorr/app/sys
RUN python3 -m venv .venv
RUN .venv/bin/pip install --no-cache-dir \
    -r /tmp/requirements-mirrorr.txt

RUN groupadd --system mirrorr \
    && useradd --system \
        --gid mirrorr \
        --home-dir /opt/mirrorr/data \
        --shell /usr/sbin/nologin \
        mirrorr \
    && mkdir -p /opt/mirrorr/data \
    && chown -R mirrorr:mirrorr /opt/mirrorr

EXPOSE 5000

COPY install/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /opt/mirrorr/app/web
ENTRYPOINT ["/entrypoint.sh"]


ENV GUNICORN_LOG_LEVEL=warning
CMD ["sh", "-c", "exec .venv/bin/gunicorn \
     --bind 0.0.0.0:5000 \
     --workers 1 \
     --threads 4 \
     --log-level \"$GUNICORN_LOG_LEVEL\" \
     mirrorr_web:app"]



