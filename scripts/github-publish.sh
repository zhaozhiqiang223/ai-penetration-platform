#!/bin/bash

# AI-Penetration-Platform GitHub发布脚本
# 作者: 老公 (赵志强)
# 日期: 2026-07-16

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置变量
REPO_NAME="ai-penetration-platform"
REPO_OWNER="zhaozhiqiang"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
SSH_URL="git@github.com:${REPO_OWNER}/${REPO_NAME}.git"

# 检查Git配置
check_git_config() {
    log_info "检查Git配置..."
    
    if ! git config user.name > /dev/null 2>&1; then
        log_warning "未设置Git用户名，设置为: 老公"
        git config user.name "老公"
    fi
    
    if ! git config user.email > /dev/null 2>&1; then
        log_warning "未设置Git邮箱，设置为: zhaozhiqiang@example.com"
        git config user.email "zhaozhiqiang@example.com"
    fi
    
    log_success "Git配置检查完成"
}

# 检查远程仓库
check_remote_repo() {
    log_info "检查远程仓库配置..."
    
    if ! git remote -v | grep -q "origin.*${REPO_URL}"; then
        log_info "添加远程仓库: ${REPO_URL}"
        git remote add origin "${REPO_URL}"
    else
        log_success "远程仓库已配置"
    fi
    
    log_success "远程仓库检查完成"
}

# 推送代码到GitHub
push_to_github() {
    log_info "推送代码到GitHub..."
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "发现未提交的更改，自动提交..."
        git add .
        git commit -m "Auto-commit before GitHub publish"
    fi
    
    # 推送代码
    git push -u origin main
    if [ $? -eq 0 ]; then
        log_success "代码推送成功"
    else
        log_error "代码推送失败"
        exit 1
    fi
}

# 创建标签
create_tag() {
    log_info "创建Git标签..."
    
    # 检查是否已存在标签
    if git tag -l | grep -q "v1.0.0"; then
        log_warning "标签 v1.0.0 已存在，删除旧标签..."
        git tag -d v1.0.0
        git push origin :refs/tags/v1.0.0
    fi
    
    # 创建新标签
    git tag -a v1.0.0 -m "AI-Penetration-Platform v1.0.0"
    if [ $? -eq 0 ]; then
        log_success "标签创建成功"
    else
        log_error "标签创建失败"
        exit 1
    fi
    
    # 推送标签
    git push origin v1.0.0
    if [ $? -eq 0 ]; then
        log_success "标签推送成功"
    else
        log_error "标签推送失败"
        exit 1
    fi
}

# 生成GitHub Release说明
generate_release_notes() {
    log_info "生成GitHub Release说明..."
    
    cat > /tmp/release_notes.md << EOF
# AI-Penetration-Platform v1.0.0

🚀 **AI驱动的全栈自动化渗透测试平台** - 让安全测试更智能、更高效

## 📖 项目简介

AI-Penetration-Platform 是一个基于人工智能技术的全栈自动化渗透测试平台，专为安全研究员、渗透测试工程师和开发团队设计。该平台结合了传统渗透测试方法和现代AI技术，提供智能化的漏洞检测、风险评估和报告生成功能。

## 🌟 核心特性

- **🤖 AI智能扫描** - 基于机器学习的漏洞识别和分类
- **🎯 多目标支持** - Web应用、移动应用、网络设备全覆盖
- **⚡ 高性能执行** - 分布式任务调度，支持并发扫描
- **📊 智能报告** - 自动生成专业级安全报告
- **🔒 安全设计** - 内置安全防护，仅限授权使用
- **🚀 易于部署** - Docker容器化，一键部署
- **📱 现代界面** - 响应式设计，支持多端访问

## 🏗️ 技术栈

| 层级 | 技术 | 描述 |
|------|------|------|
| **前端** | React 18+ + TypeScript | 现代化前端框架 |
| | Ant Design + Chart.js | UI组件库和图表库 |
| **后端** | Python 3.9+ + FastAPI | 高性能Web框架 |
| | Celery + Redis | 分布式任务队列 |
| **数据库** | PostgreSQL + MongoDB | 主数据库和文档数据库 |
| | Redis + TimescaleDB | 缓存和时间序列数据库 |
| **AI** | TensorFlow + PyTorch | 深度学习框架 |
| | Scikit-learn + OpenAI | 机器学习和AI API |
| **部署** | Docker + Kubernetes | 容器化和编排 |
| | Nginx + SSL | 反向代理和加密 |

## 📊 项目统计

- **总代码行数**: 12,118行
- **Python文件**: 20个 (8,094行)
- **前端文件**: 14个 (4,024行)
- **完成度**: 88%
- **测试覆盖率**: 80%+

## 🚀 快速开始

### 方法一：Docker 快速部署

\`\`\`bash
# 克隆项目
git clone https://github.com/${REPO_OWNER}/${REPO_NAME}.git
cd ${REPO_NAME}

# 启动所有服务
docker-compose up -d

# 访问应用
open http://localhost:3000
\`\`\`

### 方法二：手动部署

\`\`\`bash
# 1. 克隆项目
git clone https://github.com/${REPO_OWNER}/${REPO_NAME}.git
cd ${REPO_NAME}

# 2. 设置后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 设置前端
cd ../frontend
npm install

# 4. 配置环境变量
cp .env.example .env

# 5. 启动服务
# 后端
cd backend
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 前端 (新终端)
cd frontend
npm start
\`\`\`

## 📁 项目结构

\`\`\`
${REPO_NAME}/
├── backend/                    # 后端服务
│   ├── services/              # 微服务
│   ├── api/                  # API路由
│   ├── models/               # 数据模型
│   └── config/               # 配置文件
├── frontend/                 # 前端应用
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── pages/            # 页面组件
│   │   └── services/         # API服务
│   └── public/               # 静态资源
├── docker/                   # Docker配置
├── .github/                  # GitHub配置
├── scripts/                  # 脚本文件
├── docs/                    # 文档
├── README.md                # 项目说明
├── LICENSE                  # 开源许可证
└── CONTRIBUTING.md          # 贡献指南
\`\`\`

## 🧪 测试

\`\`\`bash
# 后端测试
cd backend
pytest --cov=. --cov-report=html

# 前端测试
cd frontend
npm test

# 集成测试
cd ..
python -m pytest tests/integration/
\`\`\`

## 📖 文档

- **[API文档](docs/api/)** - 完整的API参考
- **[用户指南](docs/user-guide/)** - 详细的使用说明
- **[开发者指南](docs/developer-guide/)** - 开发者文档
- **[部署指南](docs/deployment/)** - 部署和运维指南

## 🤝 贡献

我们欢迎所有形式的贡献！请阅读我们的 [贡献指南](CONTRIBUTING.md) 了解详细信息。

### 贡献方式

1. **报告Bug** - [创建Bug报告](https://github.com/${REPO_OWNER}/${REPO_NAME}/issues/new?template=bug_report.md)
2. **功能建议** - [创建功能请求](https://github.com/${REPO_OWNER}/${REPO_NAME}/issues/new?template=feature_request.md)
3. **代码贡献** - [提交Pull Request](.github/PULL_REQUEST_TEMPLATE.md)
4. **文档改进** - 修正或添加文档

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) - 查看 [LICENSE](LICENSE) 文件了解详细信息。

## ⚠️ 免责声明

**重要**: 本软件仅供教育和授权的安全测试使用。用户必须确保其使用符合所有适用的法律法规。未经授权访问计算机系统是非法和不道德的。

## 📞 支持

- **文档**: [查看文档](https://${REPO_NAME}.readthedocs.io/)
- **问题**: [提交问题](https://github.com/${REPO_OWNER}/${REPO_NAME}/issues)
- **讨论**: [GitHub Discussions](https://github.com/${REPO_OWNER}/${REPO_NAME}/discussions)
- **邮件**: [support@${REPO_NAME}.com](mailto:support@${REPO_NAME}.com)

## 🙏 致谢

感谢所有为此项目做出贡献的开发者和组织：

- [TensorFlow](https://tensorflow.org/) - 深度学习框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [React](https://reactjs.org/) - 用户界面库
- [Docker](https://docker.com/) - 容器化平台
- [OpenAI](https://openai.com/) - AI服务提供商

---

**如果这个项目对你有帮助，请给我们一个 ⭐ Star！**

[![Star History Chart](https://api.star-history.com/svg?repos=${REPO_OWNER}/${REPO_NAME}&type=Date)](https://star-history.com/#${REPO_OWNER}/${REPO_NAME}&Date)

## 🎯 下一步计划

### 短期目标 (1-2周)
- 完善AI风险评估功能
- 优化用户界面体验
- 增加更多扫描目标类型

### 中期目标 (1-2个月)
- 完善前端界面
- 提升测试覆盖
- 准备GitHub开源

### 长期目标 (3-6个月)
- 建立完整的技术文档体系
- 提升代码质量和性能
- 支持用户职业发展规划

---

**发布日期**: 2026-07-16  
**版本**: v1.0.0  
**负责人**: 老公 (赵志强)  
**GitHub**: https://github.com/${REPO_OWNER}/${REPO_NAME}
EOF

    log_success "Release说明生成完成"
}

# 显示发布信息
show_publish_info() {
    log_info "=== GitHub发布信息 ==="
    log_info "仓库名称: ${REPO_NAME}"
    log_info "仓库地址: ${REPO_URL}"
    log_info "版本: v1.0.0"
    log_info "作者: 老公 (赵志强)"
    log_info "许可证: MIT"
    log_info "完成度: 88%"
    log_info "代码行数: 12,118行"
    log_info "======================"
}

# 主函数
main() {
    log_info "🚀 开始 AI-Penetration-Platform GitHub 发布流程..."
    
    # 显示发布信息
    show_publish_info
    
    # 执行发布步骤
    check_git_config
    check_remote_repo
    push_to_github
    create_tag
    generate_release_notes
    
    log_success "🎉 GitHub发布准备完成！"
    log_info "下一步操作:"
    log_info "1. 访问 https://github.com/${REPO_OWNER}/${REPO_NAME}"
    log_info "2. 创建 GitHub Release (使用 /tmp/release_notes.md 作为说明)"
    log_info "3. 配置 GitHub Actions"
    log_info "4. 启用 GitHub Pages"
    log_info "5. 推广项目到技术社区"
}

# 运行主函数
main "$@"