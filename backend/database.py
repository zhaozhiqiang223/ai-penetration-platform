from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import redis
from pymongo import MongoClient
import logging

from config.settings import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

# Redis连接
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)

# MongoDB连接
mongo_client = MongoClient(
    settings.mongodb_url,
    serverSelectionTimeoutMS=5000,
    socketTimeoutMS=5000,
    connectTimeoutMS=5000,
    retryWrites=True
)

# 获取MongoDB数据库
mongo_db = mongo_client[settings.mongodb_db]

# 测试数据库连接
def test_database_connections():
    """测试所有数据库连接"""
    try:
        # 测试PostgreSQL连接
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            logger.info("PostgreSQL connection successful")
        
        # 测试Redis连接
        redis_client.ping()
        logger.info("Redis connection successful")
        
        # 测试MongoDB连接
        mongo_client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# 数据库会话管理
@contextmanager
def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

# Redis操作函数
def get_redis_client():
    """获取Redis客户端"""
    return redis_client

def get_mongo_client():
    """获取MongoDB客户端"""
    return mongo_client

def get_mongo_db():
    """获取MongoDB数据库"""
    return mongo_db

# 数据库初始化函数
def init_database():
    """初始化数据库"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # 创建Redis索引
        redis_client.set("initialized", "true")
        logger.info("Redis initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

# 数据库清理函数
def cleanup_database():
    """清理数据库"""
    try:
        # 清理PostgreSQL数据
        Base.metadata.drop_all(bind=engine)
        logger.info("PostgreSQL tables dropped")
        
        # 清理Redis数据
        redis_client.flushdb()
        logger.info("Redis data cleared")
        
        # 清理MongoDB数据
        mongo_db.drop_collection("vulnerabilities")
        mongo_db.drop_collection("rules")
        mongo_db.drop_collection("cases")
        logger.info("MongoDB data cleared")
        
        return True
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        return False

# 缓存操作
class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def set(key: str, value: any, expire: int = 3600):
        """设置缓存"""
        try:
            redis_client.setex(key, expire, value)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @staticmethod
    def get(key: str):
        """获取缓存"""
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @staticmethod
    def delete(key: str):
        """删除缓存"""
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    @staticmethod
    def exists(key: str):
        """检查缓存是否存在"""
        try:
            return redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False
    
    @staticmethod
    def get_keys(pattern: str):
        """获取匹配的键"""
        try:
            return redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Cache get_keys error: {e}")
            return []
    
    @staticmethod
    def clear_pattern(pattern: str):
        """清除匹配模式的键"""
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear_pattern error: {e}")
            return False

# 任务队列管理
class TaskManager:
    """任务队列管理器"""
    
    @staticmethod
    def enqueue_task(task_name: str, task_data: dict, queue: str = "default"):
        """入队任务"""
        try:
            task_key = f"task:{queue}:{task_name}"
            task_data["status"] = "pending"
            task_data["created_at"] = str(datetime.utcnow())
            
            # 使用Redis列表作为任务队列
            redis_client.lpush(f"queue:{queue}", json.dumps(task_data))
            
            # 设置任务状态
            CacheManager.set(task_key, json.dumps(task_data))
            
            return True
        except Exception as e:
            logger.error(f"Task enqueue error: {e}")
            return False
    
    @staticmethod
    def dequeue_task(queue: str = "default"):
        """出队任务"""
        try:
            task_data_str = redis_client.rpop(f"queue:{queue}")
            if task_data_str:
                task_data = json.loads(task_data_str)
                task_key = f"task:{queue}:{task_data['name']}"
                
                # 更新任务状态
                task_data["status"] = "processing"
                task_data["started_at"] = str(datetime.utcnow())
                
                CacheManager.set(task_key, json.dumps(task_data))
                
                return task_data
            return None
        except Exception as e:
            logger.error(f"Task dequeue error: {e}")
            return None
    
    @staticmethod
    def get_task_status(task_name: str, queue: str = "default"):
        """获取任务状态"""
        try:
            task_key = f"task:{queue}:{task_name}"
            task_data_str = CacheManager.get(task_key)
            if task_data_str:
                return json.loads(task_data_str)
            return None
        except Exception as e:
            logger.error(f"Task status get error: {e}")
            return None
    
    @staticmethod
    def update_task_status(task_name: str, status: str, queue: str = "default"):
        """更新任务状态"""
        try:
            task_key = f"task:{queue}:{task_name}"
            task_data_str = CacheManager.get(task_key)
            if task_data_str:
                task_data = json.loads(task_data_str)
                task_data["status"] = status
                task_data["updated_at"] = str(datetime.utcnow())
                
                if status == "completed":
                    task_data["completed_at"] = str(datetime.utcnow())
                elif status == "failed":
                    task_data["failed_at"] = str(datetime.utcnow())
                
                CacheManager.set(task_key, json.dumps(task_data))
                return True
            return False
        except Exception as e:
            logger.error(f"Task status update error: {e}")
            return False

# MongoDB操作管理
class MongoDBManager:
    """MongoDB操作管理器"""
    
    @staticmethod
    def insert_one(collection_name: str, document: dict):
        """插入文档"""
        try:
            collection = mongo_db[collection_name]
            result = collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            logger.error(f"MongoDB insert error: {e}")
            return None
    
    @staticmethod
    def find_one(collection_name: str, query: dict):
        """查找一个文档"""
        try:
            collection = mongo_db[collection_name]
            return collection.find_one(query)
        except Exception as e:
            logger.error(f"MongoDB find error: {e}")
            return None
    
    @staticmethod
    def find_many(collection_name: str, query: dict, limit: int = 0):
        """查找多个文档"""
        try:
            collection = mongo_db[collection_name]
            cursor = collection.find(query)
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"MongoDB find many error: {e}")
            return []
    
    @staticmethod
    def update_one(collection_name: str, query: dict, update: dict):
        """更新一个文档"""
        try:
            collection = mongo_db[collection_name]
            result = collection.update_one(query, {"$set": update})
            return result.modified_count
        except Exception as e:
            logger.error(f"MongoDB update error: {e}")
            return 0
    
    @staticmethod
    def delete_one(collection_name: str, query: dict):
        """删除一个文档"""
        try:
            collection = mongo_db[collection_name]
            result = collection.delete_one(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"MongoDB delete error: {e}")
            return 0
    
    @staticmethod
    def count_documents(collection_name: str, query: dict):
        """统计文档数量"""
        try:
            collection = mongo_db[collection_name]
            return collection.count_documents(query)
        except Exception as e:
            logger.error(f"MongoDB count error: {e}")
            return 0

# 导入必要的模块
import json
from datetime import datetime