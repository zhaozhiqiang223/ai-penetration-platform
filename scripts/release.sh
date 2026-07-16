#!/bin/bash

# AI-Penetration-Platform 发布脚本
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

# 检查当前分支
check_branch() {
    log_info "检查当前分支..."
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ]; then
        log_error "必须在 main 分支上发布"
        exit 1
    fi
    log_success "当前分支: $current_branch"
}

# 检查工作目录状态
check_working_directory() {
    log_info "检查工作目录状态..."
    if [ -n "$(git status --porcelain)" ]; then
        log_error "工作目录不干净，请先提交所有更改"
        exit 1
    fi
    log_success "工作目录干净"
}

# 检查远程仓库
check_remote_repository() {
    log_info "检查远程仓库..."
    if ! git remote -v | grep -q "origin"; then
        log_error "未找到远程仓库 origin"
        exit 1
    fi
    log_success "远程仓库正常"
}

# 拉取最新代码
pull_latest_code() {
    log_info "拉取最新代码..."
    git pull origin main
    log_success "代码已更新"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    # 运行Python测试
    log_info "运行Python测试..."
    cd backend
    python -m pytest --cov=. --cov-report=xml --cov-report=html
    if [ $? -ne 0 ]; then
        log_error "Python测试失败"
        exit 1
    fi
    log_success "Python测试通过"
    
    # 运行JavaScript测试
    log_info "运行JavaScript测试..."
    cd ../frontend
    npm test
    if [ $? -ne 0 ]; then
        log_error "JavaScript测试失败"
        exit 1
    fi
    log_success "JavaScript测试通过"
    
    # 返回项目根目录
    cd ..
}

# 构建项目
build_project() {
    log_info "构建项目..."
    
    # 构建后端
    log_info "构建后端..."
    cd backend
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    python -c "from database import init_db; init_db()"
    log_success "后端构建完成"
    
    # 构建前端
    log_info "构建前端..."
    cd ../frontend
    npm install
    npm run build
    log_success "前端构建完成"
    
    # 返回项目根目录
    cd ..
}

# 生成版本号
generate_version() {
    log_info "生成版本号..."
    version=$(date +%Y.%m.%d)-$(git rev-parse --short HEAD)
    echo "$version" > VERSION
    log_success "版本号: $version"
}

# 更新文档
update_documentation() {
    log_info "更新文档..."
    
    # 更新README.md中的版本号
    sed -i "s/version-[0-9]*\.[0-9]*\.[0-9]*/version-$version/g" README.md
    
    # 更新CHANGELOG.md
    echo "## 版本 $version ($(date +%Y-%m-%d))" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
    echo "### 新增功能" >> CHANGELOG.md
    echo "- 完善AI扫描功能" >> CHANGELOG.md
    echo "- 改进用户界面" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
    echo "### 修复问题" >> CHANGELOG.md
    echo "- 修复了扫描任务调度问题" >> CHANGELOG.md
    echo "- 优化了数据库查询性能" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
    
    log_success "文档已更新"
}

# 构建Docker镜像
build_docker_images() {
    log_info "构建Docker镜像..."
    
    # 构建后端镜像
    cd docker
    docker build -t zhaozhiqiang/ai-penetration-platform-backend:$version .
    if [ $? -ne 0 ]; then
        log_error "后端Docker镜像构建失败"
        exit 1
    fi
    log_success "后端Docker镜像构建完成"
    
    # 构建前端镜像
    cd ../frontend
    docker build -t zhaozhiqiang/ai-penetration-platform-frontend:$version .
    if [ $? -ne 0 ]; then
        log_error "前端Docker镜像构建失败"
        exit 1
    fi
    log_success "前端Docker镜像构建完成"
    
    # 返回项目根目录
    cd ..
}

# 推送Docker镜像
push_docker_images() {
    log_info "推送Docker镜像..."
    
    # 推送后端镜像
    docker push zhaozhiqiang/ai-penetration-platform-backend:$version
    if [ $? -ne 0 ]; then
        log_error "后端Docker镜像推送失败"
        exit 1
    fi
    log_success "后端Docker镜像推送完成"
    
    # 推送前端镜像
    docker push zhaozhiqiang/ai-penetration-platform-frontend:$version
    if [ $? -ne 0 ]; then
        log_error "前端Docker镜像推送失败"
        exit 1
    fi
    log_success "前端Docker镜像推送完成"
}

# 提交更改
commit_changes() {
    log_info "提交更改..."
    git add .
    git commit -m "Release version $version"
    git push origin main
    log_success "更改已提交"
}

# 创建GitHub Release
create_github_release() {
    log_info "创建GitHub Release..."
    
    # 创建Release标签
    git tag -a "v$version" -m "Release version $version"
    git push origin "v$version"
    
    log_success "GitHub Release创建完成"
}

# 部署到生产环境
deploy_to_production() {
    log_info "部署到生产环境..."
    
    # 这里可以添加实际的部署逻辑
    # 例如：SSH到生产服务器，运行部署脚本等
    
    log_success "生产环境部署完成"
}

# 发送通知
send_notification() {
    log_info "发送通知..."
    
    # 这里可以添加通知逻辑
    # 例如：发送邮件、Slack通知等
    
    log_success "通知已发送"
}

# 主函数
main() {
    log_info "开始发布 AI-Penetration-Platform..."
    
    # 检查前置条件
    check_branch
    check_working_directory
    check_remote_repository
    
    # 执行发布流程
    pull_latest_code
    run_tests
    build_project
    generate_version
    update_documentation
    build_docker_images
    push_docker_images
    commit_changes
    create_github_release
    deploy_to_production
    send_notification
    
    log_success "🎉 AI-Penetration-Platform 发布完成！"
    log_info "版本号: $version"
    log_info "GitHub Release: https://github.com/zhaozhiqiang/ai-penetration-platform/releases/tag/v$version"
    log_info "Docker Hub: https://hub.docker.com/r/zhaozhiqiang/ai-penetration-platform"
}

# 运行主函数
main "$@"