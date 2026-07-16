# AI-Penetration-Platform API 文档

## 📖 目录

- [概述](#概述)
- [认证](#认证)
- [扫描管理](#扫描管理)
- [目标管理](#目标管理)
- [结果分析](#结果分析)
- [风险评估](#风险评估)
- [系统管理](#系统管理)
- [错误处理](#错误处理)

## 📋 概述

AI-Penetration-Platform 提供完整的 RESTful API 接口，支持程序化访问所有功能。API 使用 JSON 格式进行数据交换，支持 HTTP/HTTPS 协议。

### 基础信息

- **基础URL**: `http://localhost:8000/api`
- **API版本**: `v1`
- **数据格式**: JSON
- **认证方式**: JWT Bearer Token

### 通用响应格式

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2026-07-17T10:00:00Z"
}
```

### 分页格式

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

## 🔐 认证

### 获取访问令牌

```http
POST /api/auth/login
```

**请求参数**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "message": "登录成功"
}
```

### 刷新访问令牌

```http
POST /api/auth/refresh
```

**请求参数**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 验证令牌

```http
GET /api/auth/verify
```

**请求头**:
```
Authorization: Bearer <access_token>
```

## 📊 扫描管理

### 创建扫描

```http
POST /api/scans
```

**请求头**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "name": "Web应用安全扫描",
  "scan_type": "web",
  "target_type": "url",
  "target_url": "https://example.com",
  "target_ip": "192.168.1.100",
  "target_domain": "example.com",
  "scan_config": {
    "depth": "deep",
    "include_subdomains": true,
    "max_pages": 100,
    "timeout": 300
  }
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Web应用安全扫描",
    "scan_type": "web",
    "target_type": "url",
    "target_url": "https://example.com",
    "status": "pending",
    "created_at": "2026-07-17T10:00:00Z"
  },
  "message": "扫描创建成功"
}
```

### 获取扫描列表

```http
GET /api/scans?page=1&limit=10&status=all&scan_type=web
```

**请求参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 10)
- `status`: 状态过滤 (可选: pending, running, completed, failed, cancelled)
- `scan_type`: 扫描类型过滤 (可选: web, mobile, network)
- `target_type`: 目标类型过滤 (可选: url, ip, domain)
- `date_range`: 日期范围过滤 (可选: [start_date, end_date])

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Web应用安全扫描",
      "scan_type": "web",
      "target_url": "https://example.com",
      "status": "completed",
      "progress": 100,
      "created_at": "2026-07-17T10:00:00Z",
      "completed_at": "2026-07-17T10:30:00Z",
      "total_findings": 15,
      "critical_findings": 2,
      "high_findings": 5,
      "medium_findings": 6,
      "low_findings": 2,
      "info_findings": 0
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

### 获取扫描详情

```http
GET /api/scans/{scan_id}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Web应用安全扫描",
    "scan_type": "web",
    "target_type": "url",
    "target_url": "https://example.com",
    "target_ip": "192.168.1.100",
    "status": "completed",
    "progress": 100,
    "scan_config": {
      "depth": "deep",
      "include_subdomains": true,
      "max_pages": 100,
      "timeout": 300
    },
    "started_at": "2026-07-17T10:00:00Z",
    "completed_at": "2026-07-17T10:30:00Z",
    "actual_duration": 1800,
    "total_findings": 15,
    "critical_findings": 2,
    "high_findings": 5,
    "medium_findings": 6,
    "low_findings": 2,
    "info_findings": 0,
    "risk_score": 75.5,
    "risk_level": "high",
    "created_at": "2026-07-17T10:00:00Z",
    "updated_at": "2026-07-17T10:30:00Z"
  }
}
```

### 启动扫描

```http
POST /api/scans/{scan_id}/start
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "task-123456",
    "scan_id": 1,
    "status": "running",
    "message": "扫描已启动"
  }
}
```

### 暂停扫描

```http
POST /api/scans/{scan_id}/pause
```

### 取消扫描

```http
POST /api/scans/{scan_id}/cancel
```

### 重启扫描

```http
POST /api/scans/{scan_id}/restart
```

### 删除扫描

```http
DELETE /api/scans/{scan_id}
```

## 🎯 目标管理

### 创建目标

```http
POST /api/targets
```

**请求参数**:
```json
{
  "name": "测试目标",
  "target_type": "url",
  "target_url": "https://example.com",
  "target_ip": "192.168.1.100",
  "target_domain": "example.com",
  "description": "测试目标描述",
  "tags": ["web", "test"],
  "priority": "high"
}
```

### 获取目标列表

```http
GET /api/targets?page=1&limit=10&target_type=url
```

### 获取目标详情

```http
GET /api/targets/{target_id}
```

### 更新目标

```http
PUT /api/targets/{target_id}
```

### 删除目标

```http
DELETE /api/targets/{target_id}
```

## 📈 结果分析

### 获取扫描结果

```http
GET /api/scans/{scan_id}/results?page=1&limit=10&severity=critical
```

**请求参数**:
- `page`: 页码 (默认: 1)
- `limit`: 每页数量 (默认: 10)
- `severity`: 严重程度过滤 (可选: critical, high, medium, low, info)
- `type`: 漏洞类型过滤
- `status`: 状态过滤

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "scan_id": 1,
      "title": "SQL注入漏洞",
      "type": "sql_injection",
      "severity": "critical",
      "confidence": 0.95,
      "description": "发现SQL注入漏洞，可能导致数据泄露",
      "evidence": [
        "请求URL: https://example.com/login",
        "请求方法: POST",
        "请求参数: username=admin' OR '1'='1",
        "响应时间: 2.5s"
      ],
      "impact_scope": "single",
      "exploit_difficulty": "low",
      "business_impact": "high",
      "affected_components": ["login page", "user management"],
      "created_at": "2026-07-17T10:15:00Z",
      "updated_at": "2026-07-17T10:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 15,
    "pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

### 获取结果详情

```http
GET /api/scans/{scan_id}/results/{result_id}
```

### 导出结果

```http
GET /api/scans/{scan_id}/export?format=pdf&template=detailed
```

**请求参数**:
- `format`: 导出格式 (可选: pdf, html, json)
- `template`: 报告模板 (可选: simple, detailed, executive)

## 🎯 风险评估

### 获取风险评估

```http
GET /api/scans/{scan_id}/risk-assessment
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "scan_id": 1,
    "risk_score": 75.5,
    "risk_level": "high",
    "risk_factors": [
      {
        "category": "sql_injection",
        "severity": "critical",
        "confidence": 0.95,
        "description": "SQL注入漏洞",
        "evidence": ["test evidence"],
        "impact_score": 8.0,
        "exploitability_score": 7.0
      }
    ],
    "recommendations": [
      "立即修复SQL注入漏洞",
      "加强输入验证",
      "使用参数化查询"
    ],
    "affected_components": ["login page", "user management"],
    "assessment_timestamp": "2026-07-17T10:20:00Z",
    "assessor_version": "1.0.0"
  }
}
```

### 获取风险趋势

```http
GET /api/targets/{target_id}/risk-trends?days=30
```

**请求参数**:
- `days`: 天数 (默认: 30)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "target_id": 1,
    "period_days": 30,
    "assessments_count": 5,
    "trend_data": [
      {
        "date": "2026-07-17T10:00:00Z",
        "risk_score": 65.0,
        "risk_level": "medium",
        "findings_count": 10
      },
      {
        "date": "2026-07-18T10:00:00Z",
        "risk_score": 75.5,
        "risk_level": "high",
        "findings_count": 15
      }
    ],
    "statistics": {
      "average_risk_score": 70.2,
      "max_risk_score": 85.0,
      "min_risk_score": 65.0,
      "risk_score_trend": "increasing"
    }
  }
}
```

## ⚙️ 系统管理

### 获取引擎状态

```http
GET /api/engine/status
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "engine_status": "running",
    "queue_status": {
      "pending_tasks": 5,
      "running_tasks": 3,
      "max_concurrent_tasks": 10
    },
    "scheduler_status": {
      "pending_tasks": 5,
      "scheduled_tasks": 8,
      "priority_distribution": {
        "critical": 2,
        "high": 3,
        "medium": 2,
        "low": 1
      }
    },
    "running_tasks": [
      {
        "task_id": "task-123456",
        "scan_id": 1,
        "status": "running",
        "progress": 75
      }
    ],
    "statistics": {
      "total_tasks": 100,
      "completed_tasks": 85,
      "failed_tasks": 10,
      "cancelled_tasks": 5,
      "average_execution_time": 1800,
      "throughput": 2.0
    },
    "timestamp": "2026-07-17T10:00:00Z"
  }
}
```

### 获取队列状态

```http
GET /api/engine/queue
```

### 获取任务历史

```http
GET /api/engine/tasks?limit=100
```

### 获取系统统计

```http
GET /api/system/statistics
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_scans": 1000,
    "running_scans": 5,
    "completed_scans": 950,
    "failed_scans": 45,
    "total_findings": 15000,
    "critical_findings": 2000,
    "high_findings": 5000,
    "medium_findings": 6000,
    "low_findings": 1500,
    "info_findings": 500,
    "average_risk_score": 65.5,
    "average_duration": 1800,
    "success_rate": 95.0,
    "today_scans": 10,
    "this_week_scans": 75,
    "this_month_scans": 300
  }
}
```

### 获取用户信息

```http
GET /api/user/profile
```

### 更新用户信息

```http
PUT /api/user/profile
```

### 获取系统日志

```http
GET /api/system/logs?level=error&limit=100
```

**请求参数**:
- `level`: 日志级别 (可选: error, warn, info, debug)
- `limit`: 数量限制 (默认: 100)

## 🔒 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "target_url",
      "message": "URL格式不正确"
    }
  },
  "timestamp": "2026-07-17T10:00:00Z"
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |
| `SERVICE_UNAVAILABLE` | 503 | 服务不可用 |

### 错误处理示例

```http
GET /api/scans/999
```

**响应示例**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "扫描任务不存在",
    "details": {
      "scan_id": 999
    }
  },
  "timestamp": "2026-07-17T10:00:00Z"
}
```

## 📝 使用示例

### Python 示例

```python
import requests
import json

# 基础URL
BASE_URL = "http://localhost:8000/api"

# 1. 登录获取token
login_data = {
    "username": "admin",
    "password": "admin123"
}

response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
token = response.json()["data"]["access_token"]

# 2. 设置请求头
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 3. 创建扫描
scan_data = {
    "name": "API测试扫描",
    "scan_type": "web",
    "target_type": "url",
    "target_url": "https://example.com",
    "scan_config": {
        "depth": "medium",
        "include_subdomains": False
    }
}

response = requests.post(f"{BASE_URL}/scans", json=scan_data, headers=headers)
scan_id = response.json()["data"]["id"]

# 4. 启动扫描
response = requests.post(f"{BASE_URL}/scans/{scan_id}/start", headers=headers)

# 5. 监控扫描状态
while True:
    response = requests.get(f"{BASE_URL}/scans/{scan_id}", headers=headers)
    scan_status = response.json()["data"]["status"]
    
    if scan_status == "completed":
        print("扫描完成")
        break
    elif scan_status == "failed":
        print("扫描失败")
        break
    
    print(f"扫描进度: {response.json()['data']['progress']}%")
    time.sleep(10)

# 6. 获取扫描结果
response = requests.get(f"{BASE_URL}/scans/{scan_id}/results", headers=headers)
results = response.json()["data"]

print(f"发现漏洞: {len(results)}个")
for result in results:
    print(f"- {result['title']} ({result['severity']})")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000/api';

// 1. 登录获取token
async function login() {
    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: 'admin',
            password: 'admin123'
        })
    });
    
    const data = await response.json();
    return data.data.access_token;
}

// 2. 创建扫描
async function createScan(token) {
    const response = await fetch(`${BASE_URL}/scans`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: '前端测试扫描',
            scan_type: 'web',
            target_type: 'url',
            target_url: 'https://example.com',
            scan_config: {
                depth: 'shallow',
                include_subdomains: false
            }
        })
    });
    
    const data = await response.json();
    return data.data.id;
}

// 3. 启动扫描
async function startScan(token, scanId) {
    const response = await fetch(`${BASE_URL}/scans/${scanId}/start`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    return response.json();
}

// 使用示例
async function main() {
    try {
        const token = await login();
        const scanId = await createScan(token);
        await startScan(token, scanId);
        
        console.log('扫描创建并启动成功');
    } catch (error) {
        console.error('操作失败:', error);
    }
}

main();
```

---

**注意**: 本文档适用于AI-Penetration-Platform版本1.0.0。如有更新，请参考最新版本的API文档。