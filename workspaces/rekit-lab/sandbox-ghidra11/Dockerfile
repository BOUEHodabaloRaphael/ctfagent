FROM debian:stable-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-21-jdk-headless python3 python3-capstone binutils file unzip curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sfL -o /tmp/g.zip https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.4.3_build/ghidra_11.4.3_PUBLIC_20251203.zip \
    && unzip -q /tmp/g.zip -d /opt && rm /tmp/g.zip && ln -s /opt/ghidra_11.4.3_PUBLIC /opt/ghidra
ENV PATH="/opt/ghidra/support:${PATH}"
RUN useradd -m -u 10001 analyst
USER analyst
WORKDIR /home/analyst
