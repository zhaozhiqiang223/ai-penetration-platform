"""
模型测试
测试数据模型的正确性和完整性
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models.target import Target, TargetType, TargetStatus
from backend.models.scan import Scan, ScanType, ScanStatus, ScanResult, ScanSeverity
from backend.models.user import User
from backend.models.report import Report, ReportType
from backend.models.knowledge import Vulnerability, VulnerabilityType, VulnerabilitySeverity
from backend.models.monitor import SystemMetrics, Alert

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
def sample_target_data():
    """示例目标数据"""
    return {
        "name": "测试目标",
        "target_type": TargetType.WEB,
        "target_url": "https://example.com",
        "target_ip": "192.168.1.100",
        "description": "测试目标描述",
        "status": TargetStatus.ACTIVE,
        "created_by": 1,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@pytest.fixture
def sample_scan_data():
    """示例扫描数据"""
    return {
        "name": "安全扫描",
        "scan_type": ScanType.WEB,
        "target_id": 1,
        "user_id": 1,
        "scan_config": {
            "scan_depth": "deep",
            "include_subdomains": True,
            "timeout": 300
        },
        "status": ScanStatus.PENDING,
        "priority": "high",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "full_name": "测试用户",
        "role": "user",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

class TestTargetModel:
    """目标模型测试"""
    
    def test_target_creation(self, db, sample_target_data):
        """测试目标创建"""
        target = Target(**sample_target_data)
        db.add(target)
        db.commit()
        db.refresh(target)
        
        assert target.id is not None
        assert target.name == sample_target_data["name"]
        assert target.target_type == sample_target_data["target_type"]
        assert target.target_url == sample_target_data["target_url"]
        assert target.status == sample_target_data["status"]
        assert target.created_by == sample_target_data["created_by"]
    
    def test_target_validation(self, db):
        """测试目标验证"""
        # 测试无效URL
        invalid_target = Target(
            name="无效目标",
            target_type=TargetType.WEB,
            target_url="invalid-url",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        
        with pytest.raises(Exception):
            db.add(invalid_target)
            db.commit()
        
        # 测试有效URL
        valid_target = Target(
            name="有效目标",
            target_type=TargetType.WEB,
            target_url="https://example.com",
            target_ip="192.168.1.100",
            status=TargetStatus.ACTIVE,
            created_by=1
        )
        
        db.add(valid_target)
        db.commit()
        db.refresh(valid_target)
        
        assert valid_target.id is not None

class TestScanModel:
    """扫描模型测试"""
    
    def test_scan_creation(self, db, sample_scan_data):
        """测试扫描创建"""
        scan = Scan(**sample_scan_data)
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        assert scan.id is not None
        assert scan.name == sample_scan_data["name"]
        assert scan.scan_type == sample_scan_data["scan_type"]
        assert scan.target_id == sample_scan_data["target_id"]
        assert scan.user_id == sample_scan_data["user_id"]
        assert scan.status == sample_scan_data["status"]
    
    def test_scan_status_transition(self, db, sample_scan_data):
        """测试扫描状态转换"""
        scan = Scan(**sample_scan_data)
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # 从PENDING到RUNNING
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        db.commit()
        db.refresh(scan)
        
        assert scan.status == ScanStatus.RUNNING
        assert scan.started_at is not None
        
        # 从RUNNING到COMPLETED
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        scan.progress = 100
        db.commit()
        db.refresh(scan)
        
        assert scan.status == ScanStatus.COMPLETED
        assert scan.completed_at is not None
        assert scan.progress == 100

class TestUserModel:
    """用户模型测试"""
    
    def test_user_creation(self, db, sample_user_data):
        """测试用户创建"""
        user = User(**sample_user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.username == sample_user_data["username"]
        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.role == sample_user_data["role"]
        assert user.is_active == sample_user_data["is_active"]
    
    def test_user_password_hashing(self, db, sample_user_data):
        """测试用户密码哈希"""
        user = User(**sample_user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 验证密码不是明文存储
        assert user.password_hash != sample_user_data["password_hash"]
        assert user.password_hash != "hashed_password"

class TestVulnerabilityModel:
    """漏洞模型测试"""
    
    def test_vulnerability_creation(self, db):
        """测试漏洞创建"""
        vulnerability = Vulnerability(
            name="SQL注入漏洞",
            vulnerability_type=VulnerabilityType.INJECTION,
            severity=VulnerabilitySeverity.HIGH,
            description="存在SQL注入漏洞",
            cve_id="CVE-2021-1234",
            reference_urls=["https://example.com/cve/1234"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(vulnerability)
        db.commit()
        db.refresh(vulnerability)
        
        assert vulnerability.id is not None
        assert vulnerability.name == "SQL注入漏洞"
        assert vulnerability.vulnerability_type == VulnerabilityType.INJECTION
        assert vulnerability.severity == VulnerabilitySeverity.HIGH
        assert vulnerability.cve_id == "CVE-2021-1234"

class TestReportModel:
    """报告模型测试"""
    
    def test_report_creation(self, db):
        """测试报告创建"""
        report = Report(
            name="安全扫描报告",
            report_type=ReportType.SCAN,
            content={"summary": "扫描完成", "findings": []},
            generated_by=1,
            generated_at=datetime.utcnow()
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        assert report.id is not None
        assert report.name == "安全扫描报告"
        assert report.report_type == ReportType.SCAN
        assert report.generated_by == 1

class TestSystemMetricsModel:
    """系统指标模型测试"""
    
    def test_system_metrics_creation(self, db):
        """测试系统指标创建"""
        metrics = SystemMetrics(
            cpu_usage=75.5,
            memory_usage=60.2,
            disk_usage=45.8,
            network_io={"in": 1024, "out": 2048},
            timestamp=datetime.utcnow()
        )
        
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        
        assert metrics.id is not None
        assert metrics.cpu_usage == 75.5
        assert metrics.memory_usage == 60.2
        assert metrics.disk_usage == 45.8
        assert metrics.network_io == {"in": 1024, "out": 2048}

class TestAlertModel:
    """告警模型测试"""
    
    def test_alert_creation(self, db):
        """测试告警创建"""
        alert = Alert(
            title="CPU使用率过高",
            message="CPU使用率达到85%",
            severity="high",
            alert_type="system",
            resolved=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        assert alert.id is not None
        assert alert.title == "CPU使用率过高"
        assert alert.message == "CPU使用率达到85%"
        assert alert.severity == "high"
        assert alert.alert_type == "system"
        assert alert.resolved == False

if __name__ == "__main__":
    pytest.main([__file__])