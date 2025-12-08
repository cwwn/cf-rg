# 使用官方 Python 基础镜像
FROM python:3.9-slim

# 设置环境变量，防止交互式安装卡住
ENV DEBIAN_FRONTEND=noninteractive

# 适配 Debian 12/13 的源文件路径，并移除废弃的 libgconf-2-4
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制核心代码
COPY app.py .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "-w", "1", "--threads", "4", "--timeout", "120", "-b", "0.0.0.0:5000", "app:app"]
