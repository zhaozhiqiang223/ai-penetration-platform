from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ScanType(str, Enum):
    VULNERABILITY = "vulnerability"
    PENETRATION = "penetration"
    COMPLIANCE = "compliance"
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ScanSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    scan_type = Column(SQLEnum(ScanType), nullable=False)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False)
    
    # 扫描配置
    scan_config = Column(JSON, default=dict)
    scan_parameters = Column(JSON, default=dict)
    scan_options = Column(JSON, default=dict)
    
    # 状态信息
    status = Column(SQLEnum(ScanStatus), default=ScanStatus.PENDING)
    progress = Column(Integer, default=0)
    
    # 时间信息
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_duration = Column(Integer)  # 秒
    actual_duration = Column(Integer)  # 秒
    
    # 执行信息
    worker_id = Column(String(100))
    task_id = Column(String(100))
    
    # 结果统计
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    info_findings = Column(Integer, default=0)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 关联
    target = relationship("Target", back_populates="scans")
    results = relationship("ScanResult", back_populates="scan")
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScanResult(Base):
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    finding_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(SQLEnum(ScanSeverity), nullable=False)
    confidence = Column(Integer, default=100)  # 0-100
    
    # 位置信息
    location = Column(String(1000))
    parameter = Column(String(255))
    method = Column(String(100))
    headers = Column(JSON)
    cookies = Column(JSON)
    
    # 漏洞详情
    vulnerability_type = Column(String(100))
    cve_id = Column(String(20))
    cwe_id = Column(String(20))
    owasp_top_10 = Column(String(50))
    
    # 修复建议
    recommendation = Column(Text)
    affected_components = Column(JSON)
    proof_of_concept = Column(Text)
    references = Column(JSON)
    
    # 状态
    status = Column(String(50), default="open")
    assigned_to = Column(String(255))
    resolved_at = Column(DateTime)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 关联
    scan = relationship("Scan", back_populates="results")
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scan_type: ScanType
    target_id: int
    scan_config: Optional[Dict[str, Any]] = None
    scan_parameters: Optional[Dict[str, Any]] = None
    scan_options: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = Field(None, ge=60, le=86400)
    tags: Optional[List[str]] = None


class ScanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scan_type: Optional[ScanType] = None
    scan_config: Optional[Dict[str, Any]] = None
    scan_parameters: Optional[Dict[str, Any]] = None
    scan_options: Optional[Dict[str, Any]] = None
    status: Optional[ScanStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    estimated_duration: Optional[int] = Field(None, ge=60, le=86400)
    tags: Optional[List[str]] = None


class ScanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    scan_type: ScanType
    target_id: int
    scan_config: Optional[Dict[str, Any]]
    scan_parameters: Optional[Dict[str, Any]]
    scan_options: Optional[Dict[str, Any]]
    status: ScanStatus
    progress: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    worker_id: Optional[str]
    task_id: Optional[str]
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int
    page: int
    size: int


class ScanStartRequest(BaseModel):
    scan_id: int
    worker_id: Optional[str] = None
    priority: int = Field(1, ge=1, le=10)


class ScanProgressUpdate(BaseModel):
    scan_id: int
    progress: int = Field(..., ge=0, le=100)
    current_step: str
    message: Optional[str] = None
    findings_count: Optional[int] = None


class ScanResultCreate(BaseModel):
    scan_id: int
    finding_type: str
    title: str
    description: Optional[str] = None
    severity: ScanSeverity
    confidence: int = Field(100, ge=0, le=100)
    location: Optional[str] = None
    parameter: Optional[str] = None
    method: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    cookies: Optional[Dict[str, Any]] = None
    vulnerability_type: Optional[str] = None
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_top_10: Optional[str] = None
    recommendation: Optional[str] = None
    affected_components: Optional[List[str]] = None
    proof_of_concept: Optional[str] = None
    references: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ScanResultResponse(BaseModel):
    id: int
    scan_id: int
    finding_type: str
    title: str
    description: Optional[str]
    severity: ScanSeverity
    confidence: int
    location: Optional[str]
    parameter: Optional[str]
    method: Optional[str]
    headers: Optional[Dict[str, Any]]
    cookies: Optional[Dict[str, Any]]
    vulnerability_type: Optional[str]
    cve_id: Optional[str]
    cwe_id: Optional[str]
    owasp_top_10: Optional[str]
    recommendation: Optional[str]
    affected_components: Optional[List[str]]
    proof_of_concept: Optional[str]
    references: Optional[List[str]]
    status: str
    assigned_to: Optional[str]
    resolved_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScanResultListResponse(BaseModel):
    results: List[ScanResultResponse]
    total: int
    page: int
    size: int


class ScanStatistics(BaseModel):
    total_scans: int
    completed_scans: int
    failed_scans: int
    running_scans: int
    pending_scans: int
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    average_scan_duration: float
    scan_success_rate: float