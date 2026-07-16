"""
服务测试
测试业务服务的正确性和完整性
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.services.ai.ai_service import AIScanner
from backend.services.engine.engine_service import EngineService, TaskPriority, TaskStatus
from backend.services.auth.auth_service import AuthService
from backend.services.target.target_service import TargetService
from backend.services.monitor.monitor_service import MonitorService
from backend.database import get_db, CacheManager
from backend.models.target import Target, TargetType, TargetStatus
from backend.models.scan import Scan, ScanType, ScanStatus, ScanResult
from backend.models.user import User

# 创建测试数据库
engine = create_engine("sqlite:///test.db")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def mock_cache():
    """模拟缓存管理器"""
    with patch('backend.database.CacheManager') as mock:
        cache_mock = Mock()
        cache_mock.get = Mock(return_value=None)
        cache_mock.set = Mock()
        cache_mock.delete = Mock()
        mock.return_value = cache_mock
        yield cache_mock

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    mock_session = Mock()
    mock_session.query = Mock()
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()
    return mock_session

class TestAIService:
    """AI扫描服务测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.ai_scanner = AIScanner()
    
    @pytest.mark.asyncio
    async def test_scan_target_web(self, db, mock_cache):
        """测试Web目标扫描"""
        # 创建测试目标
        target = Target(
            name="测试网站",
            target_type=TargetType.WEB,
            target_url="https://example.com",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        
        # 创建测试扫描
        scan = Scan(
            name="安全扫描",
            scan_type=ScanType.WEB,
            target_id=target.id,
            user_id=1,
            status=ScanStatus.PENDING,
            scan_config={"depth": "deep"}
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 模拟扫描任务数据
        task_data = {
            "task_id": "test-task-123",
            "scan_id": scan.id,
            "user_id": 1,
            "target_id": target.id,
            "target_type": TargetType.WEB,
            "target_url": target.target_url,
            "target_ip": target.target_ip,
            "scan_type": ScanType.WEB,
            "scan_config": scan.scan_config,
            "priority": TaskPriority.HIGH,
            "created_at": datetime.utcnow().isoformat(),
            "status": TaskStatus.PENDING
        }
        
        # 执行扫描
        with patch.object(self.ai_scanner, '_scan_web_target') as mock_scan:
            mock_scan.return_value = [
                {
                    "type": "sql_injection",
                    "severity": "high",
                    "confidence": 0.9,
                    "description": "检测到SQL注入漏洞",
                    "evidence": ["test evidence"],
                    "affected_components": ["login page"],
                    "recommendations": ["实施参数化查询"]
                }
            ]
            
            results = await self.ai_scanner.scan_target(scan.id, task_data, db)
            
            assert len(results) == 1
            assert results[0]["type"] == "sql_injection"
            assert results[0]["severity"] == "high"
            assert results[0]["confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_scan_target_mobile(self, db, mock_cache):
        """测试移动应用扫描"""
        # 创建测试目标
        target = Target(
            name="测试应用",
            target_type=TargetType.MOBILE,
            target_url="com.example.test",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        
        # 创建测试扫描
        scan = Scan(
            name="应用扫描",
            scan_type=ScanType.MOBILE,
            target_id=target.id,
            user_id=1,
            status=ScanStatus.PENDING,
            scan_config={"package_name": "com.example.test"}
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 模拟扫描任务数据
        task_data = {
            "task_id": "test-task-456",
            "scan_id": scan.id,
            "user_id": 1,
            "target_id": target.id,
            "target_type": TargetType.MOBILE,
            "target_url": target.target_url,
            "target_ip": target.target_ip,
            "scan_type": ScanType.MOBILE,
            "scan_config": scan.scan_config,
            "priority": TaskPriority.MEDIUM,
            "created_at": datetime.utcnow().isoformat(),
            "status": TaskStatus.PENDING
        }
        
        # 执行扫描
        with patch.object(self.ai_scanner, '_scan_mobile_target') as mock_scan:
            mock_scan.return_value = [
                {
                    "type": "insecure_storage",
                    "severity": "medium",
                    "confidence": 0.8,
                    "description": "检测到不安全的存储",
                    "evidence": ["insecure file storage"],
                    "affected_components": ["data storage"],
                    "recommendations": ["使用加密存储"]
                }
            ]
            
            results = await self.ai_scanner.scan_target(scan.id, task_data, db)
            
            assert len(results) == 1
            assert results[0]["type"] == "insecure_storage"
            assert results[0]["severity"] == "medium"
            assert results[0]["confidence"] == 0.8
    
    @pytest.mark.asyncio
    async def test_scan_target_network(self, db, mock_cache):
        """测试网络设备扫描"""
        # 创建测试目标
        target = Target(
            name="测试设备",
            target_type=TargetType.NETWORK,
            target_url="192.168.1.100",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        
        # 创建测试扫描
        scan = Scan(
            name="网络扫描",
            scan_type=ScanType.NETWORK,
            target_id=target.id,
            user_id=1,
            status=ScanStatus.PENDING,
            scan_config={"ports": [22, 80, 443]}
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 模拟扫描任务数据
        task_data = {
            "task_id": "test-task-789",
            "scan_id": scan.id,
            "user_id": 1,
            "target_id": target.id,
            "target_type": TargetType.NETWORK,
            "target_url": target.target_url,
            "target_ip": target.target_ip,
            "scan_type": ScanType.NETWORK,
            "scan_config": scan.scan_config,
            "priority": TaskPriority.LOW,
            "created_at": datetime.utcnow().isoformat(),
            "status": TaskStatus.PENDING
        }
        
        # 执行扫描
        with patch.object(self.ai_scanner, '_scan_network_target') as mock_scan:
            mock_scan.return_value = [
                {
                    "type": "open_port",
                    "severity": "low",
                    "confidence": 0.7,
                    "description": "检测到开放端口",
                    "evidence": ["port 22 is open"],
                    "affected_components": ["SSH service"],
                    "recommendations": ["检查端口安全性"]
                }
            ]
            
            results = await self.ai_scanner.scan_target(scan.id, task_data, db)
            
            assert len(results) == 1
            assert results[0]["type"] == "open_port"
            assert results[0]["severity"] == "low"
            assert results[0]["confidence"] == 0.7

class TestEngineService:
    """执行引擎服务测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.engine_service = EngineService()
    
    @pytest.mark.asyncio
    async def test_start_scan(self, db, mock_cache):
        """测试启动扫描"""
        # 创建测试目标
        target = Target(
            name="测试目标",
            target_type=TargetType.WEB,
            target_url="https://example.com",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        
        # 创建测试扫描
        scan = Scan(
            name="安全扫描",
            scan_type=ScanType.WEB,
            target_id=target.id,
            user_id=1,
            status=ScanStatus.PENDING,
            scan_config={"depth": "deep"}
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 启动扫描
        result = await self.engine_service.start_scan(scan.id, 1, db)
        
        assert result["scan_id"] == scan.id
        assert result["status"] == TaskStatus.PENDING
        assert "task_id" in result
        
        # 验证扫描状态更新
        updated_scan = db.query(Scan).filter(Scan.id == scan.id).first()
        assert updated_scan.status == ScanStatus.RUNNING
        assert updated_scan.started_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_scan(self, db, mock_cache):
        """测试取消扫描"""
        # 创建测试目标
        target = Target(
            name="测试目标",
            target_type=TargetType.WEB,
            target_url="https://example.com",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        
        # 创建测试扫描
        scan = Scan(
            name="安全扫描",
            scan_type=ScanType.WEB,
            target_id=target.id,
            user_id=1,
            status=ScanStatus.RUNNING,
            scan_config={"depth": "deep"},
            worker_id="test-task-123"
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 取消扫描
        result = await self.engine_service.cancel_scan(scan.id, 1, db)
        
        assert result["scan_id"] == scan.id
        assert result["status"] == TaskStatus.CANCELLED
        
        # 验证扫描状态更新
        updated_scan = db.query(Scan).filter(Scan.id == scan.id).first()
        assert updated_scan.status == ScanStatus.CANCELLED
        assert updated_scan.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_scan_status(self, db, mock_cache):
        """测试获取扫描状态"""
        # 创建测试目标
        target = Target(
            name="测试目标",
            target_type=TargetType.WEB,
            target_url="https://example.com",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        
        # 创建测试扫描
        scan = Scan(
            name="安全扫描",
            scan_type=ScanType.WEB,
            target_id=target.id,
            user_id=1,
            status=ScanStatus.RUNNING,
            scan_config={"depth": "deep"},
            worker_id="test-task-123",
            progress=50
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 获取扫描状态
        status = await self.engine_service.get_scan_status(scan.id, db)
        
        assert status["scan_id"] == scan.id
        assert status["scan_name"] == scan.name
        assert status["scan_type"] == scan.scan_type
        assert status["status"] == scan.status
        assert status["progress"] == scan.progress
        assert status["started_at"] == scan.started_at

class TestAuthService:
    """认证服务测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.auth_service = AuthService()
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "test_password"
        hashed_password = self.auth_service.hash_password(password)
        
        assert hashed_password != password
        assert len(hashed_password) > 20
    
    def test_password_verification(self):
        """测试密码验证"""
        password = "test_password"
        hashed_password = self.auth_service.hash_password(password)
        
        # 验证正确密码
        assert self.auth_service.verify_password(password, hashed_password)
        
        # 验证错误密码
        assert not self.auth_service.verify_password("wrong_password", hashed_password)
    
    def test_generate_token(self):
        """测试生成令牌"""
        user_id = 1
        token = self.auth_service.generate_token(user_id)
        
        assert token is not None
        assert len(token) > 20
        assert isinstance(token, str)
    
    def test_verify_token(self):
        """测试验证令牌"""
        user_id = 1
        token = self.auth_service.generate_token(user_id)
        
        # 验证有效令牌
        verified_user_id = self.auth_service.verify_token(token)
        assert verified_user_id == user_id
        
        # 验证无效令牌
        assert self.auth_service.verify_token("invalid_token") is None

class TestTargetService:
    """目标服务测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.target_service = TargetService()
    
    def test_create_target(self, db):
        """测试创建目标"""
        target_data = {
            "name": "测试目标",
            "target_type": TargetType.WEB,
            "target_url": "https://example.com",
            "target_ip": "192.168.1.100",
            "description": "测试目标描述",
            "created_by": 1
        }
        
        target = self.target_service.create_target(target_data, db)
        
        assert target.id is not None
        assert target.name == target_data["name"]
        assert target.target_type == target_data["target_type"]
        assert target.target_url == target_data["target_url"]
        assert target.target_ip == target_data["target_ip"]
        assert target.status == TargetStatus.ACTIVE
    
    def test_get_target(self, db):
        """测试获取目标"""
        # 创建测试目标
        target_data = {
            "name": "测试目标",
            "target_type": TargetType.WEB,
            "target_url": "https://example.com",
            "target_ip": "192.168.1.100",
            "description": "测试目标描述",
            "created_by": 1
        }
        
        created_target = self.target_service.create_target(target_data, db)
        
        # 获取目标
        target = self.target_service.get_target(created_target.id, db)
        
        assert target is not None
        assert target.id == created_target.id
        assert target.name == created_target.name
    
    def test_update_target(self, db):
        """测试更新目标"""
        # 创建测试目标
        target_data = {
            "name": "测试目标",
            "target_type": TargetType.WEB,
            "target_url": "https://example.com",
            "target_ip": "192.168.1.100",
            "description": "测试目标描述",
            "created_by": 1
        }
        
        created_target = self.target_service.create_target(target_data, db)
        
        # 更新目标
        update_data = {
            "name": "更新后的目标",
            "description": "更新后的描述"
        }
        
        updated_target = self.target_service.update_target(created_target.id, update_data, db)
        
        assert updated_target.name == "更新后的目标"
        assert updated_target.description == "更新后的描述"
        assert updated_target.target_url == "https://example.com"  # 保持不变
    
    def test_delete_target(self, db):
        """测试删除目标"""
        # 创建测试目标
        target_data = {
            "name": "测试目标",
            "target_type": TargetType.WEB,
            "target_url": "https://example.com",
            "target_ip": "192.168.1.100",
            "description": "测试目标描述",
            "created_by": 1
        }
        
        created_target = self.target_service.create_target(target_data, db)
        
        # 删除目标
        self.target_service.delete_target(created_target.id, db)
        
        # 验证目标被删除
        target = self.target_service.get_target(created_target.id, db)
        assert target is None

class TestMonitorService:
    """监控服务测试"""
    
    def setup_method(self):
        """设置测试方法"""
        self.monitor_service = MonitorService()
    
    def test_collect_system_metrics(self):
        """测试收集系统指标"""
        metrics = self.monitor_service.collect_system_metrics()
        
        assert metrics is not None
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics
        assert "network_io" in metrics
        assert "timestamp" in metrics
        
        # 验证指标范围
        assert 0 <= metrics["cpu_usage"] <= 100
        assert 0 <= metrics["memory_usage"] <= 100
        assert 0 <= metrics["disk_usage"] <= 100
    
    def test_check_system_health(self):
        """测试检查系统健康"""
        health_status = self.monitor_service.check_system_health()
        
        assert health_status is not None
        assert "status" in health_status
        assert "checks" in health_status
        assert "timestamp" in health_status
        
        # 验证状态值
        assert health_status["status"] in ["healthy", "warning", "critical"]
    
    def test_create_alert(self, db):
        """测试创建告警"""
        alert_data = {
            "title": "测试告警",
            "message": "这是一个测试告警",
            "severity": "high",
            "alert_type": "system",
            "created_by": 1
        }
        
        alert = self.monitor_service.create_alert(alert_data, db)
        
        assert alert.id is not None
        assert alert.title == alert_data["title"]
        assert alert.message == alert_data["message"]
        assert alert.severity == alert_data["severity"]
        assert alert.alert_type == alert_data["alert_type"]
        assert alert.resolved == False

if __name__ == "__main__":
    pytest.main([__file__])