FROM debian:stable-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-capstone python3-pyelftools binutils upx-ucl file \
    && rm -rf /var/lib/apt/lists/*
# unprivileged user; samples and tools are mounted read-only at run time
RUN useradd -m -u 10001 analyst
USER analyst
WORKDIR /home/analyst
