from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VulnerabilityType(str, Enum):
    INJECTION = "injection"
    XSS = "xss"
    CSRF = "csrf"
    SSRF = "ssrf"
    RCE = "rce"
    LFI = "lfi"
    RFI = "rfi"
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    FILE_UPLOAD = "file_upload"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    INFORMATION_DISCLOSURE = "information_disclosure"
    BUSINESS_LOGIC = "business_logic"
    CRYPTOGRAPHY = "cryptography"
    SESSION_MANAGEMENT = "session_management"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    API = "api"
    MOBILE = "mobile"
    NETWORK = "network"
    SYSTEM = "system"
    OTHER = "other"


class VulnerabilitySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    FIXED = "fixed"
    UNDER_REVIEW = "under_review"
    MITIGATED = "mitigated"


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    vulnerability_type = Column(SQLEnum(VulnerabilityType), nullable=False)
    severity = Column(SQLEnum(VulnerabilitySeverity), nullable=False)
    cve_id = Column(String(20), unique=True)
    cwe_id = Column(String(20))
    owasp_top_10 = Column(String(50))
    
    # 漏洞详情
    affected_components = Column(JSON, default=list)
    attack_vectors = Column(JSON, default=list)
    attack_complexity = Column(String(50))
    privileges_required = Column(String(50))
    user_interaction = Column(String(50))
    scope = Column(String(50))
    confidentiality_impact = Column(String(50))
    integrity_impact = Column(String(50))
    availability_impact = Column(String(50))
    
    # 修复信息
    remediation = Column(Text)
    workarounds = Column(Text)
    patches = Column(JSON, default=list)
    references = Column(JSON, default=list)
    
    # 状态信息
    status = Column(SQLEnum(VulnerabilityStatus), default=VulnerabilityStatus.ACTIVE)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    last_updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 统计信息
    occurrence_count = Column(Integer, default=0)
    fixed_count = Column(Integer, default=0)
    mitigation_count = Column(Integer, default=0)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    categories = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    rule_type = Column(String(100), nullable=False)  # scan, detection, prevention, response
    category = Column(String(100), nullable=False)
    
    # 规则内容
    rule_content = Column(Text, nullable=False)
    pattern = Column(String(1000))
    signature = Column(String(1000))
    threshold = Column(Integer)
    conditions = Column(JSON, default=dict)
    
    # 规则配置
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    severity = Column(SQLEnum(VulnerabilitySeverity))
    action = Column(String(100))  # alert, block, log, redirect
    
    # 影响范围
    target_types = Column(JSON, default=list)
    target_components = Column(JSON, default=list)
    affected_versions = Column(JSON, default=list)
    
    # 规则状态
    status = Column(String(50), default="active")
    test_status = Column(String(50), default="untested")
    last_tested_at = Column(DateTime)
    
    # 统计信息
    triggered_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    case_type = Column(String(100), nullable=False)  # penetration, audit, incident, research
    category = Column(String(100), nullable=False)
    
    # 案例信息
    target_info = Column(JSON, default=dict)
    attack_scenario = Column(Text)
    attack_steps = Column(JSON, default=list)
    tools_used = Column(JSON, default=list)
    
    # 结果信息
    findings = Column(JSON, default=list)
    impact_assessment = Column(Text)
    recommendations = Column(Text)
    lessons_learned = Column(Text)
    
    # 状态信息
    status = Column(String(50), default="draft")
    priority = Column(Integer, default=1)
    confidentiality_level = Column(String(50), default="public")
    
    # 时间信息
    occurred_at = Column(DateTime)
    resolved_at = Column(DateTime)
    reported_at = Column(DateTime)
    
    # 关联信息
    related_vulnerabilities = Column(JSON, default=list)
    related_rules = Column(JSON, default=list)
    related_scans = Column(JSON, default=list)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VulnerabilityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    vulnerability_type: VulnerabilityType
    severity: VulnerabilitySeverity
    cve_id: Optional[str] = Field(None, max_length=20)
    cwe_id: Optional[str] = Field(None, max_length=20)
    owasp_top_10: Optional[str] = Field(None, max_length=50)
    affected_components: Optional[List[str]] = None
    attack_vectors: Optional[List[str]] = None
    attack_complexity: Optional[str] = None
    privileges_required: Optional[str] = None
    user_interaction: Optional[str] = None
    scope: Optional[str] = None
    confidentiality_impact: Optional[str] = None
    integrity_impact: Optional[str] = None
    availability_impact: Optional[str] = None
    remediation: Optional[str] = None
    workarounds: Optional[str] = None
    patches: Optional[List[str]] = None
    references: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class VulnerabilityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    vulnerability_type: Optional[VulnerabilityType] = None
    severity: Optional[VulnerabilitySeverity] = None
    cve_id: Optional[str] = Field(None, max_length=20)
    cwe_id: Optional[str] = Field(None, max_length=20)
    owasp_top_10: Optional[str] = Field(None, max_length=50)
    affected_components: Optional[List[str]] = None
    attack_vectors: Optional[List[str]] = None
    attack_complexity: Optional[str] = None
    privileges_required: Optional[str] = None
    user_interaction: Optional[str] = None
    scope: Optional[str] = None
    confidentiality_impact: Optional[str] = None
    integrity_impact: Optional[str] = None
    availability_impact: Optional[str] = None
    remediation: Optional[str] = None
    workarounds: Optional[str] = None
    patches: Optional[List[str]] = None
    references: Optional[List[str]] = None
    status: Optional[VulnerabilityStatus] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class VulnerabilityResponse(BaseModel):
    id: int
    name: str
    description: str
    vulnerability_type: VulnerabilityType
    severity: VulnerabilitySeverity
    cve_id: Optional[str]
    cwe_id: Optional[str]
    owasp_top_10: Optional[str]
    affected_components: Optional[List[str]]
    attack_vectors: Optional[List[str]]
    attack_complexity: Optional[str]
    privileges_required: Optional[str]
    user_interaction: Optional[str]
    scope: Optional[str]
    confidentiality_impact: Optional[str]
    integrity_impact: Optional[str]
    availability_impact: Optional[str]
    remediation: Optional[str]
    workarounds: Optional[str]
    patches: Optional[List[str]]
    references: Optional[List[str]]
    status: VulnerabilityStatus
    discovered_at: datetime
    published_at: Optional[datetime]
    last_updated_at: datetime
    occurrence_count: int
    fixed_count: int
    mitigation_count: int
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    categories: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., regex=r'^(scan|detection|prevention|response)$')
    category: str = Field(..., min_length=1, max_length=100)
    rule_content: str = Field(..., min_length=1)
    pattern: Optional[str] = Field(None, max_length=1000)
    signature: Optional[str] = Field(None, max_length=1000)
    threshold: Optional[int] = Field(None, ge=1)
    conditions: Optional[Dict[str, Any]] = None
    priority: int = Field(1, ge=1, le=10)
    severity: Optional[VulnerabilitySeverity] = None
    action: Optional[str] = Field(None, regex=r'^(alert|block|log|redirect)$')
    target_types: Optional[List[str]] = None
    target_components: Optional[List[str]] = None
    affected_versions: Optional[List[str]] = None
    enabled: bool = True
    tags: Optional[List[str]] = None


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, regex=r'^(scan|detection|prevention|response)$')
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    rule_content: Optional[str] = Field(None, min_length=1)
    pattern: Optional[str] = Field(None, max_length=1000)
    signature: Optional[str] = Field(None, max_length=1000)
    threshold: Optional[int] = Field(None, ge=1)
    conditions: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    severity: Optional[VulnerabilitySeverity] = None
    action: Optional[str] = Field(None, regex=r'^(alert|block|log|redirect)$')
    target_types: Optional[List[str]] = None
    target_components: Optional[List[str]] = None
    affected_versions: Optional[List[str]] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class RuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    rule_type: str
    category: str
    rule_content: str
    pattern: Optional[str]
    signature: Optional[str]
    threshold: Optional[int]
    conditions: Optional[Dict[str, Any]]
    priority: int
    severity: Optional[VulnerabilitySeverity]
    action: Optional[str]
    target_types: Optional[List[str]]
    target_components: Optional[List[str]]
    affected_versions: Optional[List[str]]
    enabled: bool
    status: str
    test_status: str
    last_tested_at: Optional[datetime]
    triggered_count: int
    blocked_count: int
    false_positive_count: int
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    case_type: str = Field(..., regex=r'^(penetration|audit|incident|research)$')
    category: str = Field(..., min_length=1, max_length=100)
    target_info: Optional[Dict[str, Any]] = None
    attack_scenario: Optional[str] = None
    attack_steps: Optional[List[Dict[str, Any]]] = None
    tools_used: Optional[List[str]] = None
    findings: Optional[List[Dict[str, Any]]] = None
    impact_assessment: Optional[str] = None
    recommendations: Optional[str] = None
    lessons_learned: Optional[str] = None
    priority: int = Field(1, ge=1, le=10)
    confidentiality_level: str = Field("public", regex=r'^(public|internal|confidential|secret)$')
    occurred_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    case_type: Optional[str] = Field(None, regex=r'^(penetration|audit|incident|research)$')
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    target_info: Optional[Dict[str, Any]] = None
    attack_scenario: Optional[str] = None
    attack_steps: Optional[List[Dict[str, Any]]] = None
    tools_used: Optional[List[str]] = None
    findings: Optional[List[Dict[str, Any]]] = None
    impact_assessment: Optional[str] = None
    recommendations: Optional[str] = None
    lessons_learned: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    confidentiality_level: Optional[str] = Field(None, regex=r'^(public|internal|confidential|secret)$')
    occurred_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    related_vulnerabilities: Optional[List[str]] = None
    related_rules: Optional[List[str]] = None
    related_scans: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    attachments: Optional[List[str]] = None


class CaseResponse(BaseModel):
    id: int
    title: str
    description: str
    case_type: str
    category: str
    target_info: Optional[Dict[str, Any]]
    attack_scenario: Optional[str]
    attack_steps: Optional[List[Dict[str, Any]]]
    tools_used: Optional[List[str]]
    findings: Optional[List[Dict[str, Any]]]
    impact_assessment: Optional[str]
    recommendations: Optional[str]
    lessons_learned: Optional[str]
    status: str
    priority: int
    confidentiality_level: str
    occurred_at: Optional[datetime]
    resolved_at: Optional[datetime]
    reported_at: Optional[datetime]
    related_vulnerabilities: Optional[List[str]]
    related_rules: Optional[List[str]]
    related_scans: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    attachments: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    search_type: str = Field("all", regex=r'^(all|vulnerabilities|rules|cases)$')
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class KnowledgeSearchResponse(BaseModel):
    vulnerabilities: List[VulnerabilityResponse]
    rules: List[RuleResponse]
    cases: List[CaseResponse]
    total_results: int
    query: str
    search_type: str
    execution_time: float