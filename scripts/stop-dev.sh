#!/bin/bash

# AI-Penetration-Platform 开发环境停止脚本
# 作者: 老公 (赵志强)
# 日期: 2026-07-16

echo "🛑 AI-Penetration-Platform 开发环境停止脚本"
echo "==============================================="

# 停止后端服务
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "📋 停止后端服务..."
        kill $BACKEND_PID
        echo "✅ 后端服务已停止"
    fi
    rm .backend.pid
fi

# 停止前端服务
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "📋 停止前端服务..."
        kill $FRONTEND_PID
        echo "✅ 前端服务已停止"
    fi
    rm .frontend.pid
fi

# 停止Python虚拟环境
if [ -d "backend/venv" ]; then
    echo "📋 清理Python虚拟环境..."
    rm -rf backend/venv
    echo "✅ Python虚拟环境已清理"
fi

# 停止Node.js依赖
if [ -d "frontend/node_modules" ]; then
    echo "📋 清理Node.js依赖..."
    rm -rf frontend/node_modules
    echo "✅ Node.js依赖已清理"
fi

echo ""
echo "🎉 开发环境已停止！"
echo "==============================================="