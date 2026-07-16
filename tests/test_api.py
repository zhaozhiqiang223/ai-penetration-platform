"""
API测试
测试API接口的正确性和完整性
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api.main import app
from backend.database import get_db
from backend.models.target import Target, TargetType, TargetStatus
from backend.models.scan import Scan, ScanType, ScanStatus
from backend.models.user import User

# 创建测试数据库
engine = create_engine("sqlite:///test_api.db")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """覆盖数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)

@pytest.fixture
def db():
    """创建测试数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password",
        full_name="测试用户",
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_target(db, test_user):
    """创建测试目标"""
    target = Target(
        name="测试目标",
        target_type=TargetType.WEB,
        target_url="https://example.com",
        target_ip="192.168.1.100",
        description="测试目标描述",
        status=TargetStatus.ACTIVE,
        created_by=test_user.id
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target

@pytest.fixture
def test_scan(db, test_user, test_target):
    """创建测试扫描"""
    scan = Scan(
        name="安全扫描",
        scan_type=ScanType.WEB,
        target_id=test_target.id,
        user_id=test_user.id,
        status=ScanStatus.PENDING,
        scan_config={"depth": "deep"}
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan

class TestTargetAPI:
    """目标API测试"""
    
    def test_create_target(self, client, db, test_user):
        """测试创建目标"""
        target_data = {
            "name": "新目标",
            "target_type": "web",
            "target_url": "https://newexample.com",
            "target_ip": "192.168.1.200",
            "description": "新目标描述"
        }
        
        response = client.post(
            "/api/v1/targets/",
            json=target_data,
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == target_data["name"]
        assert data["target_type"] == target_data["target_type"]
        assert data["target_url"] == target_data["target_url"]
        assert data["target_ip"] == target_data["target_ip"]
        assert data["description"] == target_data["description"]
        assert data["status"] == "active"
    
    def test_get_targets(self, client, db, test_target):
        """测试获取目标列表"""
        response = client.get(
            "/api/v1/targets/",
            headers={"Authorization": f"Bearer {test_target.created_by}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == test_target.name
    
    def test_get_target(self, client, db, test_target):
        """测试获取单个目标"""
        response = client.get(
            f"/api/v1/targets/{test_target.id}",
            headers={"Authorization": f"Bearer {test_target.created_by}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_target.id
        assert data["name"] == test_target.name
    
    def test_update_target(self, client, db, test_target):
        """测试更新目标"""
        update_data = {
            "name": "更新后的目标",
            "description": "更新后的描述"
        }
        
        response = client.put(
            f"/api/v1/targets/{test_target.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_target.created_by}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["target_url"] == test_target.target_url  # 保持不变
    
    def test_delete_target(self, client, db, test_target):
        """测试删除目标"""
        response = client.delete(
            f"/api/v1/targets/{test_target.id}",
            headers={"Authorization": f"Bearer {test_target.created_by}"}
        )
        
        assert response.status_code == 204
        
        # 验证目标被删除
        get_response = client.get(
            f"/api/v1/targets/{test_target.id}",
            headers={"Authorization": f"Bearer {test_target.created_by}"}
        )
        assert get_response.status_code == 404

class TestScanAPI:
    """扫描API测试"""
    
    def test_create_scan(self, client, db, test_user, test_target):
        """测试创建扫描"""
        scan_data = {
            "name": "新扫描",
            "scan_type": "web",
            "target_id": test_target.id,
            "scan_config": {
                "depth": "deep",
                "include_subdomains": True,
                "timeout": 300
            },
            "priority": "high"
        }
        
        response = client.post(
            "/api/v1/scans/",
            json=scan_data,
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == scan_data["name"]
        assert data["scan_type"] == scan_data["scan_type"]
        assert data["target_id"] == scan_data["target_id"]
        assert data["status"] == "pending"
    
    def test_get_scans(self, client, db, test_scan):
        """测试获取扫描列表"""
        response = client.get(
            "/api/v1/scans/",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == test_scan.name
    
    def test_get_scan(self, client, db, test_scan):
        """测试获取单个扫描"""
        response = client.get(
            f"/api/v1/scans/{test_scan.id}",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_scan.id
        assert data["name"] == test_scan.name
    
    def test_start_scan(self, client, db, test_scan):
        """测试启动扫描"""
        response = client.post(
            f"/api/v1/scans/{test_scan.id}/start",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == test_scan.id
        assert data["status"] == "running"
        assert "task_id" in data
    
    def test_cancel_scan(self, client, db, test_scan):
        """测试取消扫描"""
        # 先启动扫描
        start_response = client.post(
            f"/api/v1/scans/{test_scan.id}/start",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        # 取消扫描
        response = client.post(
            f"/api/v1/scans/{test_scan.id}/cancel",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["scan_id"] == test_scan.id
        assert data["status"] == "cancelled"
    
    def test_get_scan_results(self, client, db, test_scan):
        """测试获取扫描结果"""
        response = client.get(
            f"/api/v1/scans/{test_scan.id}/results",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert "results" in data
        assert "total_findings" in data

class TestUserAPI:
    """用户API测试"""
    
    def test_get_user(self, client, db, test_user):
        """测试获取用户信息"""
        response = client.get(
            f"/api/v1/users/{test_user.id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
    
    def test_get_user_scans(self, client, db, test_user, test_scan):
        """测试获取用户扫描列表"""
        response = client.get(
            f"/api/v1/users/{test_user.id}/scans",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == test_user.id
    
    def test_get_user_targets(self, client, db, test_user, test_target):
        """测试获取用户目标列表"""
        response = client.get(
            f"/api/v1/users/{test_user.id}/targets",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == test_user.id

class TestReportAPI:
    """报告API测试"""
    
    def test_get_scan_report(self, client, db, test_scan):
        """测试获取扫描报告"""
        response = client.get(
            f"/api/v1/scans/{test_scan.id}/report",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "scan_id" in data
        assert "report" in data
        assert "generated_at" in data
    
    def test_download_scan_report(self, client, db, test_scan):
        """测试下载扫描报告"""
        response = client.get(
            f"/api/v1/scans/{test_scan.id}/report/download",
            headers={"Authorization": f"Bearer {test_scan.user_id}"}
        )
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "attachment" in response.headers.get("content-disposition", "")

class TestSystemAPI:
    """系统API测试"""
    
    def test_get_system_status(self, client):
        """测试获取系统状态"""
        response = client.get("/api/v1/system/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "uptime" in data
    
    def test_get_system_metrics(self, client):
        """测试获取系统指标"""
        response = client.get("/api/v1/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "disk_usage" in data
        assert "network_io" in data
    
    def test_get_health_check(self, client):
        """测试健康检查"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert data["status"] == "healthy"

class TestAuthAPI:
    """认证API测试"""
    
    def test_login(self, client, db, test_user):
        """测试登录"""
        login_data = {
            "username": test_user.username,
            "password": "test_password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client, db, test_user):
        """测试登出"""
        # 先登录获取token
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user.username,
            "password": "test_password"
        })
        token = login_response.json()["access_token"]
        
        # 登出
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_get_current_user(self, client, db, test_user):
        """测试获取当前用户"""
        # 先登录获取token
        login_response = client.post("/api/v1/auth/login", json={
            "username": test_user.username,
            "password": "test_password"
        })
        token = login_response.json()["access_token"]
        
        # 获取当前用户
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username

class TestErrorHandling:
    """错误处理测试"""
    
    def test_401_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/targets/")
        assert response.status_code == 401
    
    def test_404_not_found(self, client, test_user):
        """测试资源不存在"""
        response = client.get(
            "/api/v1/targets/99999",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 404
    
    def test_422_validation_error(self, client, test_user):
        """测试验证错误"""
        invalid_data = {
            "name": "",  # 空名称
            "target_type": "invalid_type",  # 无效类型
            "target_url": "invalid-url",  # 无效URL
        }
        
        response = client.post(
            "/api/v1/targets/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__])