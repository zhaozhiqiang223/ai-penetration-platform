#!/bin/bash

# AI-Penetration-Platform 认证推送脚本
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
REPO_URL="https://github.com/zhaozhiqiang223/ai-penetration-platform.git"

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

# 推送代码到GitHub
push_to_github() {
    log_info "推送代码到GitHub..."
    
    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "发现未提交的更改，自动提交..."
        git add .
        git commit -m "Auto-commit before GitHub publish"
    fi
    
    log_info "正在推送代码到GitHub..."
    log_info "请输入你的GitHub用户名和密码或Personal Access Token"
    log_info ""
    
    # 尝试推送
    if git push -u origin main; then
        log_success "代码推送成功！"
    else
        log_error "推送失败，请检查认证信息"
        log_info "可能的原因:"
        log_info "1. GitHub用户名或密码错误"
        log_info "2. 需要使用Personal Access Token"
        log_info "3. 网络连接问题"
        log_info ""
        log_info "建议使用Personal Access Token:"
        log_info "1. 访问 https://github.com/settings/tokens"
        log_info "2. 点击 'Generate new token'"
        log_info "3. 选择 'repo' 权限"
        log_info "4. 复制生成的token"
        log_info "5. 在推送时使用token作为密码"
    fi
}

# 推送标签
push_tags() {
    log_info "推送标签到GitHub..."
    
    if git push origin v1.0.0; then
        log_success "标签推送成功！"
    else
        log_error "标签推送失败，请检查认证信息"
    fi
}

# 显示后续步骤
show_next_steps() {
    log_info "=== 后续步骤 ==="
    log_info "1. 配置GitHub Actions:"
    log_info "   - 进入仓库设置"
    log_info "   - 启用 Actions"
    log_info "   - 复制 .github/workflows/ci.yml 内容"
    log_info ""
    log_info "2. 创建GitHub Release:"
    log_info "   - 进入 Releases 页面"
    log_info "   - 创建 v1.0.0 Release"
    log_info "   - 使用 FINAL_PUBLISH_GUIDE.md 中的说明"
    log_info ""
    log_info "3. 配置GitHub Pages:"
    log_info "   - 进入 Settings -> Pages"
    log_info "   - 选择 GitHub Actions"
    log_info "   - 保存设置"
    log_info ""
    log_info "4. 推广项目:"
    log_info "   - 社交媒体发布"
    log_info "   - 技术博客分享"
    log_info "   - 开发者社区推广"
    log_info "=================="
}

# 主函数
main() {
    log_info "🚀 开始 AI-Penetration-Platform 认证推送流程..."
    
    # 检查Git配置
    check_git_config
    
    # 推送代码
    push_to_github
    
    # 推送标签
    push_tags
    
    # 显示后续步骤
    show_next_steps
    
    log_success "🎉 认证推送流程完成！"
    log_info "请按照后续步骤完成GitHub配置"
}

# 运行主函数
main "$@"