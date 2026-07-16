import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "AI Penetration Testing Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ai_penetration"
    db_user: str = "postgres"
    db_password: str = "password"
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # MongoDB配置
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_db: str = "ai_penetration"
    mongodb_username: Optional[str] = None
    mongodb_password: Optional[str] = None
    
    # 安全配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # AI模型配置
    model_path: str = "./models"
    gpu_enabled: bool = False
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    
    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    celery_task_serializer: str = "json"
    celery_result_serializer: str = "json"
    celery_accept_content: list = ["json"]
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # CORS配置
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    cors_methods: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list = ["*"]
    
    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list = [
        ".py", ".txt", ".json", ".xml", ".html", ".js", 
        ".php", ".java", ".go", ".rb", ".pl", ".sh",
        ".apk", ".ipa", ".exe", ".dll", ".so", ".dylib"
    ]
    
    # 扫描配置
    scan_timeout: int = 3600  # 1小时
    max_concurrent_scans: int = 10
    scan_result_retention_days: int = 30
    
    # 监控配置
    metrics_enabled: bool = True
    metrics_port: int = 8001
    
    @validator("cors_origins", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, tuple)):
            return v
        raise ValueError(v)
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def mongodb_url(self) -> str:
        if self.mongodb_username and self.mongodb_password:
            return f"mongodb://{self.mongodb_username}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局设置实例
settings = Settings()