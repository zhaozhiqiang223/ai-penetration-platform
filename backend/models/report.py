from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ReportType(str, Enum):
    SUMMARY = "summary"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    AUDIT = "audit"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"


class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    MARKDOWN = "markdown"


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 报告配置
    report_config = Column(JSON, default=dict)
    template_id = Column(String(100))
    
    # 报告状态
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.DRAFT)
    progress = Column(Integer, default=0)
    
    # 报告文件
    file_path = Column(String(500))
    file_size = Column(Integer)  # bytes
    file_format = Column(SQLEnum(ReportFormat))
    download_url = Column(String(500))
    
    # 报告内容
    summary = Column(Text)
    executive_summary = Column(Text)
    findings_summary = Column(JSON)
    recommendations = Column(JSON)
    
    # 时间信息
    scheduled_at = Column(DateTime)
    generated_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    shared_with = Column(JSON, default=list)
    
    # 关联
    scan = relationship("Scan", back_populates="reports")
    user = relationship("User")
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportSection(Base):
    __tablename__ = "report_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    section_type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    order = Column(Integer, default=0)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    charts = Column(JSON, default=list)
    tables = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportFinding(Base):
    __tablename__ = "report_findings"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    scan_result_id = Column(Integer, ForeignKey("scan_results.id"), nullable=False)
    
    # 报告中的漏洞信息
    title = Column(String(500), nullable=False)
    description = Column(Text)
    severity = Column(String(20), nullable=False)
    confidence = Column(Integer, default=100)
    
    # 位置信息
    location = Column(String(1000))
    parameter = Column(String(255))
    method = Column(String(100))
    
    # 修复建议
    recommendation = Column(Text)
    affected_components = Column(JSON)
    proof_of_concept = Column(Text)
    references = Column(JSON)
    
    # 报告特有字段
    risk_score = Column(Integer)
    business_impact = Column(Text)
    compliance_status = Column(String(50))
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: ReportType
    scan_id: Optional[int] = None
    report_config: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    shared_with: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ReportUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: Optional[ReportType] = None
    report_config: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    status: Optional[ReportStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    summary: Optional[str] = None
    executive_summary: Optional[str] = None
    findings_summary: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    shared_with: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class ReportResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    report_type: ReportType
    scan_id: Optional[int]
    user_id: int
    report_config: Optional[Dict[str, Any]]
    template_id: Optional[str]
    status: ReportStatus
    progress: int
    file_path: Optional[str]
    file_size: Optional[int]
    file_format: Optional[ReportFormat]
    download_url: Optional[str]
    summary: Optional[str]
    executive_summary: Optional[str]
    findings_summary: Optional[Dict[str, Any]]
    recommendations: Optional[Dict[str, Any]]
    scheduled_at: Optional[datetime]
    generated_at: Optional[datetime]
    expires_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    shared_with: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int
    size: int


class ReportGenerationRequest(BaseModel):
    report_id: int
    template_id: Optional[str] = None
    include_charts: bool = True
    include_raw_data: bool = False
    custom_sections: Optional[List[Dict[str, Any]]] = None
    export_format: ReportFormat = ReportFormat.PDF


class ReportSectionCreate(BaseModel):
    report_id: int
    section_type: str
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    order: int = Field(0, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    charts: Optional[List[Dict[str, Any]]] = None
    tables: Optional[List[Dict[str, Any]]] = None


class ReportSectionResponse(BaseModel):
    id: int
    report_id: int
    section_type: str
    title: str
    content: Optional[str]
    order: int
    metadata: Optional[Dict[str, Any]]
    charts: Optional[List[Dict[str, Any]]]
    tables: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportFindingResponse(BaseModel):
    id: int
    report_id: int
    scan_result_id: int
    title: str
    description: Optional[str]
    severity: str
    confidence: int
    location: Optional[str]
    parameter: Optional[str]
    method: Optional[str]
    recommendation: Optional[str]
    affected_components: Optional[List[str]]
    proof_of_concept: Optional[str]
    references: Optional[List[str]]
    risk_score: Optional[int]
    business_impact: Optional[str]
    compliance_status: Optional[str]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReportTemplate(BaseModel):
    id: str
    name: str
    description: str
    report_type: ReportType
    template_content: Dict[str, Any]
    default_config: Dict[str, Any]
    sections: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ReportStatistics(BaseModel):
    total_reports: int
    completed_reports: int
    failed_reports: int
    generating_reports: int
    draft_reports: int
    pdf_reports: int
    html_reports: int
    json_reports: int
    average_generation_time: float
    most_common_report_type: str
    reports_by_month: Dict[str, int]
    storage_usage: int