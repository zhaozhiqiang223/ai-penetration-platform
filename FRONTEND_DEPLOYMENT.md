# AI自动化渗透测试平台 - 前端部署指南

## 🚀 **快速开始**

### **环境要求**
- **Node.js**: 16.x 或更高版本
- **npm**: 8.x 或更高版本
- **操作系统**: Windows, macOS, Linux

### **安装步骤**

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-penetration-platform/frontend
```

2. **安装依赖**
```bash
npm install
```

3. **启动开发服务器**
```bash
npm start
```

4. **访问应用**
打开浏览器访问: `http://localhost:3000`

## 🔧 **配置说明**

### **环境变量配置**

在项目根目录创建 `.env` 文件：

```env
# API服务地址
REACT_APP_API_URL=http://localhost:8000/api/v1

# 应用名称
REACT_APP_APP_NAME=AI自动化渗透测试平台

# 应用描述
REACT_APP_APP_DESCRIPTION=智能安全评估，自动化渗透测试

# 默认主题
REACT_APP_DEFAULT_THEME=light

# 默认语言
REACT_APP_DEFAULT_LANGUAGE=zh-CN
```

### **API配置**

修改 `src/services/api.js` 文件中的API地址：

```javascript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## 📦 **构建部署**

### **生产环境构建**

```bash
# 构建生产版本
npm run build

# 构建文件位于 build/ 目录
```

### **静态文件部署**

将 `build/` 目录下的文件部署到Web服务器：

```bash
# 使用Nginx部署
sudo cp -r build/* /var/www/ai-penetration-platform/

# 配置Nginx
sudo nano /etc/nginx/sites-available/ai-penetration-platform
```

### **Nginx配置示例**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/ai-penetration-platform;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔒 **安全配置**

### **HTTPS配置**

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    root /var/www/ai-penetration-platform;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **CORS配置**

在 `src/services/api.js` 中配置CORS：

```javascript
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 启用跨域凭证
});
```

## 📱 **移动端适配**

### **响应式设计**

应用已经内置响应式设计，支持：
- 桌面端 (> 1200px)
- 平板端 (768px - 1200px)
- 手机端 (< 768px)

### **移动端优化**

```css
/* 移动端样式优化 */
@media (max-width: 768px) {
  .ant-card {
    margin-bottom: 16px;
  }
  
  .ant-statistic {
    text-align: center;
  }
  
  .ant-table {
    font-size: 12px;
  }
}
```

## 🧪 **测试运行**

### **单元测试**

```bash
# 运行所有测试
npm test

# 运行特定测试
npm test -- --testPathPattern=DashboardPage

# 生成测试覆盖率报告
npm run test:coverage
```

### **端到端测试**

```bash
# 安装Cypress
npm install cypress --save-dev

# 运行Cypress测试
npx cypress open
```

## 📊 **性能优化**

### **代码分割**

```javascript
// 使用React.lazy实现懒加载
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));
const TargetsPage = React.lazy(() => import('./pages/TargetsPage'));
const ScansPage = React.lazy(() => import('./pages/ScansPage'));
```

### **图片优化**

```javascript
// 使用React.lazy加载图片
const LazyImage = React.lazy(() => import('./components/LazyImage'));
```

### **缓存策略**

```javascript
// 配置Service Worker
const serviceWorkerRegistration = await navigator.serviceWorker.register('/sw.js');
```

## 🔧 **故障排除**

### **常见问题**

1. **构建失败**
```bash
# 清除缓存重新构建
rm -rf node_modules
rm -rf package-lock.json
npm install
npm run build
```

2. **API连接失败**
```bash
# 检查API服务是否运行
curl http://localhost:8000/health

# 检查网络连接
ping localhost:8000
```

3. **跨域问题**
```bash
# 在后端配置CORS
# 或使用代理服务器
npm install http-proxy-middleware
```

### **日志调试**

```javascript
// 启用详细日志
localStorage.setItem('debug', 'ai-penetration-platform:*');

// 查看控制台日志
console.log('API Response:', response);
```

## 📞 **技术支持**

### **开发团队**
- **前端开发**: 编程小助手
- **后端开发**: 编程小助手
- **UI设计**: 编程小助手

### **联系方式**
- **GitHub Issues**: [项目Issues页面](https://github.com/your-repo/issues)
- **Email**: support@your-domain.com
- **文档**: [在线文档](https://docs.your-domain.com)

### **社区支持**
- **Stack Overflow**: 标签 `ai-penetration-platform`
- **Discord**: [开发者社区](https://discord.gg/your-community)
- **QQ群**: 123456789

---

**部署完成时间**: 2026-07-16  
**部署版本**: v1.0.0  
**维护状态**: 活跃维护