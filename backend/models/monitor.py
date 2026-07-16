from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AlertType(str, Enum):
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"
    SCAN = "scan"
    USER = "user"
    BUSINESS = "business"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
   escalated = "escalated"


class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    metric_type = Column(String(50))
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 元数据
    source = Column(String(100))
    host = Column(String(100))
    service = Column(String(100))
    component = Column(String(100))
    
    # 标签
    tags = Column(JSON, default=list)
    dimensions = Column(JSON, default=dict)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    
    # 告警规则
    rule_id = Column(String(100))
    rule_name = Column(String(255))
    condition = Column(String(500))
    threshold = Column(Float)
    
    # 告警状态
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN)
    
    # 时间信息
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    escalated_at = Column(DateTime)
    
    # 处理信息
    assigned_to = Column(String(255))
    resolution_notes = Column(Text)
    action_taken = Column(Text)
    
    # 影响范围
    affected_targets = Column(JSON, default=list)
    affected_scans = Column(JSON, default=list)
    affected_users = Column(JSON, default=list)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemHealth(Base):
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    component_name = Column(String(100), nullable=False, index=True)
    component_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    health_score = Column(Integer, nullable=False)
    
    # 性能指标
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    network_usage = Column(Float)
    
    # 响应时间
    response_time = Column(Float)
    throughput = Column(Float)
    
    # 错误率
    error_rate = Column(Float)
    
    # 时间信息
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    username = Column(String(100))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    
    # 操作详情
    details = Column(JSON, default=dict)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    session_id = Column(String(100))
    
    # 结果信息
    status = Column(String(50), default="success")
    error_message = Column(Text)
    
    # 时间信息
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    
    # 时间信息
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 应用信息
    service_name = Column(String(100))
    endpoint = Column(String(500))
    method = Column(String(10))
    
    # 性能指标
    response_time = Column(Float)
    throughput = Column(Float)
    error_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # 系统信息
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    network_usage = Column(Float)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)


class Dashboard(Base):
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    owner_id = Column(Integer)
    
    # 仪表板配置
    layout = Column(JSON, default=dict)
    widgets = Column(JSON, default=list)
    filters = Column(JSON, default=dict)
    
    # 公开设置
    is_public = Column(Boolean, default=False)
    shared_with = Column(JSON, default=list)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Widget(Base):
    __tablename__ = "widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    widget_type = Column(String(100), nullable=False)
    position = Column(JSON, default=dict)
    size = Column(JSON, default=dict)
    
    # 配置
    config = Column(JSON, default=dict)
    data_source = Column(String(500))
    query = Column(Text)
    
    # 样式
    style = Column(JSON, default=dict)
    theme = Column(String(50))
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    condition: Optional[str] = None
    threshold: Optional[float] = None
    affected_targets: Optional[List[str]] = None
    affected_scans: Optional[List[str]] = None
    affected_users: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    alert_type: Optional[AlertType] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    action_taken: Optional[str] = None
    affected_targets: Optional[List[str]] = None
    affected_scans: Optional[List[str]] = None
    affected_users: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    alert_type: AlertType
    severity: AlertSeverity
    rule_id: Optional[str]
    rule_name: Optional[str]
    condition: Optional[str]
    threshold: Optional[float]
    status: AlertStatus
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    escalated_at: Optional[datetime]
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    action_taken: Optional[str]
    affected_targets: Optional[List[str]]
    affected_scans: Optional[List[str]]
    affected_users: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    attachments: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    size: int


class SystemMetricsCreate(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=100)
    metric_value: float = Field(..., gt=0)
    metric_unit: Optional[str] = Field(None, max_length=50)
    metric_type: Optional[str] = Field(None, max_length=50)
    source: Optional[str] = Field(None, max_length=100)
    host: Optional[str] = Field(None, max_length=100)
    service: Optional[str] = Field(None, max_length=100)
    component: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    dimensions: Optional[Dict[str, Any]] = None


class SystemMetricsResponse(BaseModel):
    id: int
    metric_name: str
    metric_value: float
    metric_unit: Optional[str]
    metric_type: Optional[str]
    timestamp: datetime
    source: Optional[str]
    host: Optional[str]
    service: Optional[str]
    component: Optional[str]
    tags: Optional[List[str]]
    dimensions: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SystemHealthResponse(BaseModel):
    id: int
    component_name: str
    component_type: str
    status: str
    health_score: int
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    network_usage: Optional[float]
    response_time: Optional[float]
    throughput: Optional[float]
    error_rate: Optional[float]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    status: str
    error_message: Optional[str]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PerformanceMetricsResponse(BaseModel):
    id: int
    metric_name: str
    metric_value: float
    metric_unit: Optional[str]
    timestamp: datetime
    service_name: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    response_time: Optional[float]
    throughput: Optional[float]
    error_count: int
    success_count: int
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    network_usage: Optional[float]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: Optional[int]
    layout: Optional[Dict[str, Any]]
    widgets: Optional[List[Dict[str, Any]]]
    filters: Optional[Dict[str, Any]]
    is_public: bool
    shared_with: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WidgetResponse(BaseModel):
    id: int
    dashboard_id: int
    name: str
    widget_type: str
    position: Optional[Dict[str, Any]]
    size: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    data_source: Optional[str]
    query: Optional[str]
    style: Optional[Dict[str, Any]]
    theme: Optional[str]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertStatistics(BaseModel):
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    info_alerts: int
    open_alerts: int
    in_progress_alerts: int
    resolved_alerts: int
    dismissed_alerts: int
    escalated_alerts: int
    average_resolution_time: float
    alerts_by_type: Dict[str, int]
    alerts_by_severity: Dict[str, int]
    alerts_by_day: Dict[str, int]
    alert_trend: List[Dict[str, Any]]


class SystemStatistics(BaseModel):
    total_metrics: int
    system_uptime: float
    average_cpu_usage: float
    average_memory_usage: float
    average_disk_usage: float
    average_network_usage: float
    error_rate: float
    success_rate: float
    response_time_avg: float
    response_time_95th: float
    response_time_99th: float
    throughput_avg: float
    throughput_peak: float
    system_health_score: int
    components_health: Dict[str, int]