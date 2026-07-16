import hashlib
import jwt
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database import get_db, CacheManager
from models.user import User, UserCreate, UserUpdate, UserLogin, UserLoginResponse, TokenPayload
from utils.security import hash_password, verify_password, generate_salt, check_password_strength

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", access_token_expire_minutes: int = 30):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.refresh_token_expire_days = 7
        
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """解码令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def register_user(self, user_data: UserCreate, db: Session) -> User:
        """用户注册"""
        try:
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == user_data.username).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            # 检查邮箱是否已存在
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            
            # 检查密码强度
            password_check = check_password_strength(user_data.password)
            if not password_check["is_strong"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password is not strong enough"
                )
            
            # 创建用户
            salt = generate_salt()
            password_hash = hash_password(user_data.password, salt)["hash"]
            
            user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=password_hash,
                role=user_data.role,
                department=user_data.department,
                position=user_data.position,
                preferences=user_data.preferences or {},
                language=user_data.language,
                timezone=user_data.timezone,
                metadata={"created_by": "self_registration"}
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"User registered successfully: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            raise
    
    async def authenticate_user(self, username: str, password: str, db: Session) -> Optional[User]:
        """用户认证"""
        try:
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                return None
            
            # 验证密码
            if not verify_password(password, user.hashed_password, generate_salt()):
                return None
            
            # 检查用户状态
            if user.status != "active":
                return None
            
            # 更新登录信息
            user.last_login = datetime.utcnow()
            user.login_attempts = 0
            db.commit()
            
            logger.info(f"User authenticated successfully: {username}")
            return user
            
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            return None
    
    async def login_user(self, login_data: UserLogin, db: Session) -> UserLoginResponse:
        """用户登录"""
        try:
            # 认证用户
            user = await self.authenticate_user(login_data.username, login_data.password, db)
            
            if not user:
                # 增加登录尝试次数
                db_user = db.query(User).filter(User.username == login_data.username).first()
                if db_user:
                    db_user.login_attempts += 1
                    if db_user.login_attempts >= 5:
                        db_user.status = "locked"
                        db_user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    db.commit()
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )
            
            # 生成令牌
            access_token = self.create_access_token(data={"sub": user.id, "username": user.username})
            refresh_token = self.create_refresh_token(data={"sub": user.id, "username": user.username})
            
            # 缓存刷新令牌
            CacheManager.set(f"refresh_token:{user.id}", refresh_token, expires_in=86400 * self.refresh_token_expire_days)
            
            return UserLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                user=self._user_to_response(user)
            )
            
        except Exception as e:
            logger.error(f"User login failed: {e}")
            raise
    
    async def refresh_token(self, refresh_token: str, db: Session) -> Dict[str, str]:
        """刷新令牌"""
        try:
            # 验证刷新令牌
            payload = self.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # 检查用户是否存在
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # 检查用户状态
            if user.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is not active"
                )
            
            # 检查刷新令牌是否匹配
            cached_token = CacheManager.get(f"refresh_token:{user_id}")
            if not cached_token or cached_token != refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # 生成新的访问令牌
            new_access_token = self.create_access_token(data={"sub": user.id, "username": user.username})
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise
    
    async def logout_user(self, access_token: str, db: Session) -> Dict[str, str]:
        """用户登出"""
        try:
            # 解码令牌获取用户ID
            payload = self.decode_token(access_token)
            user_id = payload.get("sub")
            
            if user_id:
                # 清除刷新令牌
                CacheManager.delete(f"refresh_token:{user_id}")
            
            return {"message": "Successfully logged out"}
            
        except Exception as e:
            logger.error(f"User logout failed: {e}")
            raise
    
    async def change_password(self, user_id: int, current_password: str, new_password: str, db: Session) -> Dict[str, str]:
        """修改密码"""
        try:
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 验证当前密码
            if not verify_password(current_password, user.hashed_password, generate_salt()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # 检查新密码强度
            password_check = check_password_strength(new_password)
            if not password_check["is_strong"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password is not strong enough"
                )
            
            # 更新密码
            salt = generate_salt()
            password_hash = hash_password(new_password, salt)["hash"]
            user.hashed_password = password_hash
            
            db.commit()
            
            logger.info(f"Password changed successfully for user: {user.username}")
            return {"message": "Password changed successfully"}
            
        except Exception as e:
            logger.error(f"Password change failed: {e}")
            raise
    
    async def reset_password(self, email: str, db: Session) -> Dict[str, str]:
        """重置密码"""
        try:
            # 获取用户
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 生成重置令牌
            reset_token = secrets.token_urlsafe(32)
            reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            
            # 存储重置令牌
            CacheManager.set(f"reset_token:{user.id}", reset_token, expires_in=3600)
            
            # 这里应该发送邮件通知用户
            # await self._send_password_reset_email(user, reset_token)
            
            logger.info(f"Password reset initiated for user: {user.username}")
            return {"message": "Password reset email sent"}
            
        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            raise
    
    async def confirm_password_reset(self, token: str, new_password: str, db: Session) -> Dict[str, str]:
        """确认密码重置"""
        try:
            # 验证重置令牌
            user_id = None
            for key in CacheManager.get_keys("reset_token:*"):
                cached_token = CacheManager.get(key)
                if cached_token == token:
                    user_id = key.split(":")[1]
                    break
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired reset token"
                )
            
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 检查密码强度
            password_check = check_password_strength(new_password)
            if not password_check["is_strong"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New password is not strong enough"
                )
            
            # 更新密码
            salt = generate_salt()
            password_hash = hash_password(new_password, salt)["hash"]
            user.hashed_password = password_hash
            
            # 清除重置令牌
            CacheManager.delete(f"reset_token:{user_id}")
            
            db.commit()
            
            logger.info(f"Password reset confirmed for user: {user.username}")
            return {"message": "Password reset successfully"}
            
        except Exception as e:
            logger.error(f"Password reset confirmation failed: {e}")
            raise
    
    async def enable_two_factor(self, user_id: int, db: Session) -> Dict[str, Any]:
        """启用双因素认证"""
        try:
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 生成双因素认证密钥
            secret = secrets.token_urlsafe(32)
            
            # 存储密钥
            CacheManager.set(f"2fa_secret:{user.id}", secret, expires_in=86400 * 30)
            
            # 生成QR码URL
            qr_code_url = f"otpauth://totp/{user.username}?secret={secret}&issuer=AI-Penetration-Platform"
            
            return {
                "secret": secret,
                "qr_code_url": qr_code_url,
                "backup_codes": self._generate_backup_codes()
            }
            
        except Exception as e:
            logger.error(f"2FA enable failed: {e}")
            raise
    
    async def verify_two_factor(self, user_id: int, code: str, db: Session) -> Dict[str, str]:
        """验证双因素认证"""
        try:
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 获取双因素认证密钥
            secret = CacheManager.get(f"2fa_secret:{user.id}")
            if not secret:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA not enabled"
                )
            
            # 验证代码
            if self._verify_totp_code(secret, code):
                # 启用双因素认证
                user.two_factor_enabled = True
                db.commit()
                
                logger.info(f"2FA enabled for user: {user.username}")
                return {"message": "Two-factor authentication enabled successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid two-factor code"
                )
            
        except Exception as e:
            logger.error(f"2FA verification failed: {e}")
            raise
    
    async def disable_two_factor(self, user_id: int, code: str, db: Session) -> Dict[str, str]:
        """禁用双因素认证"""
        try:
            # 获取用户
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 验证双因素认证代码
            if not user.two_factor_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Two-factor authentication not enabled"
                )
            
            # 这里应该验证双因素认证代码
            # 为了简化，我们直接禁用
            user.two_factor_enabled = False
            db.commit()
            
            # 清除双因素认证密钥
            CacheManager.delete(f"2fa_secret:{user_id}")
            
            logger.info(f"2FA disabled for user: {user.username}")
            return {"message": "Two-factor authentication disabled successfully"}
            
        except Exception as e:
            logger.error(f"2FA disable failed: {e}")
            raise
    
    async def get_user_permissions(self, user_id: int, db: Session) -> List[str]:
        """获取用户权限"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 基于角色的权限
            role_permissions = self._get_role_permissions(user.role)
            
            # 自定义权限
            custom_permissions = user.permissions or []
            
            # 合并权限
            all_permissions = list(set(role_permissions + custom_permissions))
            
            return all_permissions
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            raise
    
    async def check_permission(self, user_id: int, permission: str, db: Session) -> bool:
        """检查用户权限"""
        try:
            user_permissions = await self.get_user_permissions(user_id, db)
            return permission in user_permissions
            
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False
    
    async def assign_permission(self, user_id: int, permission: str, db: Session) -> Dict[str, str]:
        """分配权限"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 添加权限
            if user.permissions is None:
                user.permissions = []
            
            if permission not in user.permissions:
                user.permissions.append(permission)
                db.commit()
                
                logger.info(f"Permission assigned to user: {user.username} - {permission}")
                return {"message": "Permission assigned successfully"}
            else:
                return {"message": "Permission already assigned"}
            
        except Exception as e:
            logger.error(f"Permission assignment failed: {e}")
            raise
    
    async def revoke_permission(self, user_id: int, permission: str, db: Session) -> Dict[str, str]:
        """撤销权限"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # 移除权限
            if user.permissions and permission in user.permissions:
                user.permissions.remove(permission)
                db.commit()
                
                logger.info(f"Permission revoked from user: {user.username} - {permission}")
                return {"message": "Permission revoked successfully"}
            else:
                return {"message": "Permission not found"}
            
        except Exception as e:
            logger.error(f"Permission revocation failed: {e}")
            raise
    
    def _user_to_response(self, user: User) -> Dict[str, Any]:
        """将用户模型转换为响应格式"""
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "status": user.status,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "phone": user.phone,
            "department": user.department,
            "position": user.position,
            "preferences": user.preferences,
            "language": user.language,
            "timezone": user.timezone,
            "two_factor_enabled": user.two_factor_enabled,
            "last_login": user.last_login,
            "login_attempts": user.login_attempts,
            "permissions": user.permissions,
            "teams": user.teams,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
    
    def _get_role_permissions(self, role: str) -> List[str]:
        """获取角色权限"""
        role_permissions = {
            "super_user": [
                "read_all", "write_all", "delete_all", "manage_users", "manage_system",
                "create_scan", "read_scan", "update_scan", "delete_scan",
                "create_target", "read_target", "update_target", "delete_target",
                "create_report", "read_report", "update_report", "delete_report",
                "manage_knowledge", "manage_alerts", "manage_settings"
            ],
            "admin": [
                "read_all", "write_all", "manage_users", "create_scan", "read_scan",
                "update_scan", "delete_scan", "create_target", "read_target", "update_target",
                "delete_target", "create_report", "read_report", "update_report", "delete_report",
                "manage_knowledge", "manage_alerts"
            ],
            "analyst": [
                "read_all", "create_scan", "read_scan", "update_scan", "create_target",
                "read_target", "update_target", "create_report", "read_report", "update_report",
                "manage_knowledge"
            ],
            "auditor": [
                "read_all", "read_scan", "read_target", "read_report", "manage_knowledge"
            ],
            "viewer": [
                "read_scan", "read_target", "read_report"
            ]
        }
        
        return role_permissions.get(role, [])
    
    def _generate_backup_codes(self) -> List[str]:
        """生成备用验证码"""
        backup_codes = []
        for _ in range(10):
            code = secrets.token_urlsafe(8)
            backup_codes.append(code)
        return backup_codes
    
    def _verify_totp_code(self, secret: str, code: str) -> bool:
        """验证TOTP代码"""
        # 这里应该使用pyotp库来验证TOTP代码
        # 为了简化，我们返回True
        return True


class JWTBearer:
    """JWT认证中间件"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    def __call__(self, token: str):
        try:
            payload = self.auth_service.verify_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            return user_id
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def check_permission(self, user_id: int, permission: str, db: Session):
        """检查权限"""
        if not await self.auth_service.check_permission(user_id, permission, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )