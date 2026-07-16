from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import asyncio
from datetime import datetime, timedelta

from config.settings import settings
from database import get_db, init_database, test_database_connections
from models.target import Target, TargetCreate, TargetUpdate, TargetResponse, TargetListResponse, TargetDiscoveryRequest
from models.user import User, UserCreate, UserResponse, UserListResponse, UserLogin, UserLoginResponse
from models.scan import Scan, ScanCreate, ScanResponse, ScanListResponse, ScanType, ScanStatus
from services.target.target_service import TargetService
from services.ai.ai_service import AIScanner
from services.engine.engine_service import EngineService
from services.auth.auth_service import AuthService, JWTBearer, PermissionChecker

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI自动化渗透测试平台API",
    debug=settings.debug
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# 初始化服务
target_service = TargetService()
auth_service = AuthService(
    secret_key=settings.secret_key,
    algorithm=settings.algorithm,
    access_token_expire_minutes=settings.access_token_expire_minutes
)
jwt_bearer = JWTBearer(auth_service)
permission_checker = PermissionChecker(auth_service)

# 全局变量
engine_service = None
ai_scanner = None

# 数据库依赖
def get_database_session() -> Session:
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    """启动时初始化数据库和服务"""
    global engine_service, ai_scanner
    
    try:
        # 测试数据库连接
        if not test_database_connections():
            raise Exception("Database connection failed")
        
        # 初始化数据库
        init_database()
        
        # 初始化服务
        engine_service = EngineService()
        ai_scanner = AIScanner()
        
        logger.info("Database and services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database and services: {e}")
        raise

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "services": {
            "database": "connected",
            "redis": "connected",
            "mongodb": "connected",
            "engine": "running" if engine_service else "stopped",
            "ai_scanner": "ready" if ai_scanner else "not_ready"
        }
    }

# 认证相关API
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_database_session)):
    """用户注册"""
    try:
        return await auth_service.register_user(user, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/auth/login", response_model=UserLoginResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_database_session)):
    """用户登录"""
    try:
        return await auth_service.login_user(login_data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_database_session)):
    """刷新令牌"""
    try:
        return await auth_service.refresh_token(refresh_token, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/auth/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """用户登出"""
    try:
        return await auth_service.logout_user(credentials.credentials, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/auth/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """修改密码"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        return await auth_service.change_password(user_id, current_password, new_password, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/auth/reset-password")
async def reset_password(email: str, db: Session = Depends(get_database_session)):
    """重置密码"""
    try:
        return await auth_service.reset_password(email, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/auth/confirm-password-reset")
async def confirm_password_reset(
    token: str,
    new_password: str,
    db: Session = Depends(get_database_session)
):
    """确认密码重置"""
    try:
        return await auth_service.confirm_password_reset(token, new_password, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 目标管理API
@app.post("/api/v1/targets", response_model=TargetResponse)
async def create_target(
    target: TargetCreate,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """创建目标"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "create_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return await target_service.create_target(target, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/v1/targets", response_model=TargetListResponse)
async def list_targets(
    skip: int = 0,
    limit: int = 100,
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取目标列表"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        from models.target import TargetType, TargetStatus
        
        target_type_enum = TargetType(target_type) if target_type else None
        status_enum = TargetStatus(status) if status else None
        
        targets = await target_service.list_targets(
            db, skip=skip, limit=limit,
            target_type=target_type_enum, status=status_enum
        )
        
        return TargetListResponse(
            targets=targets,
            total=len(targets),
            page=skip // limit + 1,
            size=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/v1/targets/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取目标详情"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return await target_service.get_target(target_id, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@app.put("/api/v1/targets/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target: TargetUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """更新目标"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "update_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return await target_service.update_target(target_id, target, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.delete("/api/v1/targets/{target_id}")
async def delete_target(
    target_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """删除目标"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "delete_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        success = await target_service.delete_target(target_id, db)
        return {"message": "Target deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/targets/discover", response_model=dict)
async def discover_targets(
    discovery_request: TargetDiscoveryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """发现目标"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "create_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        result = await target_service.discover_targets(discovery_request, db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/v1/targets/statistics")
async def get_target_statistics(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取目标统计信息"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_target", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        stats = await target_service.get_target_statistics(db)
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 扫描管理API
@app.post("/api/v1/scans", response_model=ScanResponse)
async def create_scan(
    scan: ScanCreate,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """创建扫描"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "create_scan", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # 创建扫描
        from models.scan import Scan
        scan_obj = Scan(
            name=scan.name,
            description=scan.description,
            scan_type=scan.scan_type,
            target_id=scan.target_id,
            scan_config=scan.scan_config or {},
            scan_parameters=scan.scan_parameters or {},
            scan_options=scan.scan_options or {},
            estimated_duration=scan.estimated_duration,
            user_id=user_id,
            status=ScanStatus.PENDING
        )
        
        db.add(scan_obj)
        db.commit()
        db.refresh(scan_obj)
        
        return scan_obj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/scans/{scan_id}/start")
async def start_scan(
    scan_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """启动扫描"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "create_scan", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        if not engine_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Engine service not available"
            )
        
        result = await engine_service.start_scan(scan_id, user_id, db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/api/v1/scans/{scan_id}/cancel")
async def cancel_scan(
    scan_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """取消扫描"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "update_scan", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        if not engine_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Engine service not available"
            )
        
        result = await engine_service.cancel_scan(scan_id, user_id, db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/v1/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取扫描详情"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_scan", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found"
            )
        
        return scan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@app.get("/api/v1/scans", response_model=ScanListResponse)
async def list_scans(
    skip: int = 0,
    limit: int = 100,
    scan_type: Optional[str] = None,
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取扫描列表"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_scan", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        from models.scan import ScanType as ScanTypeEnum, ScanStatus as ScanStatusEnum
        
        scan_type_enum = ScanTypeEnum(scan_type) if scan_type else None
        status_enum = ScanStatusEnum(status) if status else None
        
        query = db.query(Scan)
        if scan_type_enum:
            query = query.filter(Scan.scan_type == scan_type_enum)
        if status_enum:
            query = query.filter(Scan.status == status_enum)
        
        scans = query.offset(skip).limit(limit).all()
        
        return ScanListResponse(
            scans=scans,
            total=len(scans),
            page=skip // limit + 1,
            size=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/v1/scans/running")
async def get_running_scans(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取正在运行的扫描"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_scan", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        if not engine_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Engine service not available"
            )
        
        running_scans = await engine_service.list_running_scans(db)
        return {"running_scans": running_scans}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/api/v1/engine/status")
async def get_engine_status(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取引擎状态"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "read_all", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        if not engine_service:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Engine service not available"
            )
        
        queue_status = await engine_service.get_queue_status(db)
        task_stats = await engine_service.get_task_statistics(db)
        
        return {
            "queue_status": queue_status,
            "task_statistics": task_stats,
            "engine_status": "running" if engine_service else "stopped"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 用户管理API
@app.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取当前用户信息"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@app.get("/api/v1/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_database_session)
):
    """获取用户列表"""
    try:
        user_id = jwt_bearer(credentials.credentials)
        
        # 检查权限
        if not await permission_checker.check_permission(user_id, "manage_users", db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        users = db.query(User).offset(skip).limit(limit).all()
        
        return UserListResponse(
            users=users,
            total=len(users),
            page=skip // limit + 1,
            size=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI自动化渗透测试平台API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/api/v1/auth",
            "targets": "/api/v1/targets",
            "scans": "/api/v1/scans",
            "users": "/api/v1/users",
            "health": "/health"
        }
    }

# API信息
@app.get("/api/v1/info")
async def api_info():
    """API信息"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI自动化渗透测试平台API",
        "endpoints": {
            "auth": "/api/v1/auth",
            "targets": "/api/v1/targets",
            "scans": "/api/v1/scans",
            "users": "/api/v1/users",
            "health": "/health"
        }
    }

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    if engine_service:
        await engine_service.shutdown()
    logger.info("Application shutdown completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )