FROM --platform=linux/amd64 ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive

# 安装基础编译工具、Git 及 Python3
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    build-essential \
    python3 \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 锁定并安装 Go 1.10.8 (amd64)
RUN wget https://go.dev/dl/go1.10.8.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.10.8.linux-amd64.tar.gz && \
    rm go1.10.8.linux-amd64.tar.gz

# 配置 Go 环境变量
ENV GOROOT=/usr/local/go
ENV GOPATH=/go
ENV PATH="${GOROOT}/bin:${GOPATH}/bin:${PATH}"

WORKDIR /workspace

CMD ["/bin/bash"]