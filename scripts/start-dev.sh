#!/bin/bash

# AI-Penetration-Platform 开发环境启动脚本
# 作者: 老公 (赵志强)
# 日期: 2026-07-16

echo "🚀 AI-Penetration-Platform 开发环境启动脚本"
echo "==============================================="

# 检查Python版本
echo "📋 检查Python版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 检查Node.js版本
echo "📋 检查Node.js版本..."
node --version
if [ $? -ne 0 ]; then
    echo "❌ Node.js 未安装，请先安装Node.js"
    exit 1
fi

# 创建虚拟环境
echo "📋 创建Python虚拟环境..."
cd backend
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ 创建虚拟环境失败"
    exit 1
fi

# 激活虚拟环境
echo "📋 激活虚拟环境..."
source venv/bin/activate

# 安装Python依赖
echo "📋 安装Python依赖..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 安装Python依赖失败"
    exit 1
fi

# 安装前端依赖
echo "📋 安装前端依赖..."
cd ../frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ 安装前端依赖失败"
    exit 1
fi

# 返回项目根目录
cd ..

# 创建环境变量文件
echo "📋 创建环境变量文件..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请根据需要修改配置"
fi

# 创建数据库
echo "📋 初始化数据库..."
cd backend
python -c "from database import init_db; init_db()"
if [ $? -ne 0 ]; then
    echo "❌ 初始化数据库失败"
    exit 1
fi

# 启动后端服务
echo "📋 启动后端服务..."
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端服务
echo "📋 启动前端服务..."
cd ../frontend
npm start &
FRONTEND_PID=$!

# 等待服务启动
echo "📋 等待服务启动..."
sleep 10

# 检查服务状态
echo "📋 检查服务状态..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ 后端服务已启动 (http://localhost:8000)"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID
    exit 1
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务已启动 (http://localhost:3000)"
else
    echo "❌ 前端服务启动失败"
    kill $BACKEND_PID $FRONTEND_PID
    exit 1
fi

echo ""
echo "🎉 开发环境启动成功！"
echo "==============================================="
echo "🌐 前端地址: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "📝 使用说明:"
echo "1. 打开浏览器访问 http://localhost:3000"
echo "2. 使用默认账户登录或注册新账户"
echo "3. 创建扫描目标并启动扫描"
echo "4. 查看扫描结果和报告"
echo ""
echo "🛑 停止服务: Ctrl+C 或运行 ./scripts/stop-dev.sh"
echo ""

# 保存进程ID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 等待用户中断
echo "按 Ctrl+C 停止所有服务..."
wait