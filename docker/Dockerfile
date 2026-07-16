# AI-Penetration-Platform 后端 Dockerfile
# 作者: 老公 (赵志强)
# 日期: 2026-07-16

FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 创建必要的目录
RUN mkdir -p /app/uploads /app/reports /app/logs /app/models/torch /app/models/transformers

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]