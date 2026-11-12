FROM mirror.gcr.io/library/python:3.12-slim
RUN pip install --no-cache-dir flask
WORKDIR /app
COPY app.py .
EXPOSE 9090
CMD ["python3", "app.py"]
