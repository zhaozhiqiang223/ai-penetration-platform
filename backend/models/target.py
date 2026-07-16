from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TargetType(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    NETWORK = "network"
    SYSTEM = "system"
    API = "api"


class TargetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"


class Target(Base):
    __tablename__ = "targets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    target_type = Column(SQLEnum(TargetType), nullable=False)
    target_url = Column(String(1000))
    target_ip = Column(String(45))  # 支持IPv6
    target_port = Column(Integer)
    target_path = Column(String(1000))
    
    # 扫描配置
    scan_config = Column(JSON, default=dict)
    scan_depth = Column(Integer, default=1)
    scan_timeout = Column(Integer, default=3600)
    
    # 目标状态
    status = Column(SQLEnum(TargetStatus), default=TargetStatus.PENDING)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_scanned_at = Column(DateTime)
    next_scan_at = Column(DateTime)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TargetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: TargetType
    target_url: Optional[str] = Field(None, max_length=1000)
    target_ip: Optional[str] = Field(None, max_length=45)
    target_port: Optional[int] = Field(None, ge=1, le=65535)
    target_path: Optional[str] = Field(None, max_length=1000)
    scan_config: Optional[Dict[str, Any]] = None
    scan_depth: int = Field(1, ge=1, le=10)
    scan_timeout: int = Field(3600, ge=60, le=86400)
    tags: Optional[List[str]] = None


class TargetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: Optional[TargetType] = None
    target_url: Optional[str] = Field(None, max_length=1000)
    target_ip: Optional[str] = Field(None, max_length=45)
    target_port: Optional[int] = Field(None, ge=1, le=65535)
    target_path: Optional[str] = Field(None, max_length=1000)
    scan_config: Optional[Dict[str, Any]] = None
    scan_depth: Optional[int] = Field(None, ge=1, le=10)
    scan_timeout: Optional[int] = Field(None, ge=60, le=86400)
    status: Optional[TargetStatus] = None
    tags: Optional[List[str]] = None
    
    @validator('target_url')
    def validate_url_or_ip(cls, v, values):
        target_url = values.get('target_url')
        target_ip = values.get('target_ip')
        
        if not target_url and not target_ip:
            raise ValueError('Either target_url or target_ip must be provided')
        
        if target_url and not target_url.startswith(('http://', 'https://')):
            raise ValueError('target_url must start with http:// or https://')
        
        return v


class TargetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_type: TargetType
    target_url: Optional[str]
    target_ip: Optional[str]
    target_port: Optional[int]
    target_path: Optional[str]
    scan_config: Optional[Dict[str, Any]]
    scan_depth: int
    scan_timeout: int
    status: TargetStatus
    discovered_at: datetime
    last_scanned_at: Optional[datetime]
    next_scan_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TargetListResponse(BaseModel):
    targets: List[TargetResponse]
    total: int
    page: int
    size: int


class TargetDiscoveryRequest(BaseModel):
    target_type: TargetType
    network_range: Optional[str] = None
    scan_method: str = Field(..., regex=r'^(active|passive|hybrid)$')
    discovery_timeout: int = Field(300, ge=60, le=3600)
    exclude_private: bool = True
    exclude_local: bool = True


class TargetDiscoveryResponse(BaseModel):
    discovered_targets: List[TargetResponse]
    scan_time: float
    success_count: int
    error_count: int
    errors: List[str]