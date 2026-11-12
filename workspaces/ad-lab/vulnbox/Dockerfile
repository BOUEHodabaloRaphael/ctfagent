FROM mirror.gcr.io/library/python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python3", "app.py"]
