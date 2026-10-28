FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --chown=root:root src/server.py /app/server.py
COPY --chown=root:root src/flag.txt /app/flag.txt

RUN useradd -m -u 1000 ctf && \
    chmod 555 /app && \
    chmod 444 /app/server.py /app/flag.txt

USER ctf

EXPOSE 16767

CMD ["socat", "TCP-LISTEN:16767,reuseaddr,fork", "EXEC:python3 -B -u /app/server.py,pipes,stderr"]
