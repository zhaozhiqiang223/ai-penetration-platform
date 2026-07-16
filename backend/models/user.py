from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    VIEWER = "viewer"
    SUPER_USER = "super_user"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # 用户角色和权限
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 个人信息
    avatar_url = Column(String(500))
    bio = Column(Text)
    phone = Column(String(20))
    department = Column(String(100))
    position = Column(String(100))
    
    # 偏好设置
    preferences = Column(JSON, default=dict)
    language = Column(String(10), default="zh-CN")
    timezone = Column(String(50), default="Asia/Shanghai")
    
    # 安全设置
    two_factor_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # 权限设置
    permissions = Column(JSON, default=list)
    teams = Column(JSON, default=list)
    
    # 元数据
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.VIEWER
    department: Optional[str] = None
    position: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    language: str = Field("zh-CN", min_length=2, max_length=10)
    timezone: str = Field("Asia/Shanghai", min_length=2, max_length=50)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    timezone: Optional[str] = Field(None, min_length=2, max_length=50)
    two_factor_enabled: Optional[bool] = None
    permissions: Optional[List[str]] = None
    teams: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str]
    bio: Optional[str]
    phone: Optional[str]
    department: Optional[str]
    position: Optional[str]
    preferences: Optional[Dict[str, Any]]
    language: str
    timezone: str
    two_factor_enabled: bool
    last_login: Optional[datetime]
    login_attempts: int
    locked_until: Optional[datetime]
    permissions: Optional[List[str]]
    teams: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int


class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: bool = False


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    exp: Optional[int] = None


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class TwoFactorSetup(BaseModel):
    secret: str
    qr_code_url: str
    backup_codes: List[str]


class TwoFactorVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class UserStatistics(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    suspended_users: int
    admin_users: int
    analyst_users: int
    auditor_users: int
    viewer_users: int
    super_users: int
    login_last_24h: int
    login_last_7d: int
    login_last_30d: int