import asyncio
import ipaddress
import json
import logging
import re
import socket
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import httpx
import nmap
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db, CacheManager
from models.target import Target, TargetType, TargetStatus, TargetCreate, TargetUpdate, TargetDiscoveryRequest
from models.scan import Scan, ScanType, ScanStatus
from utils.security import validate_url, validate_ip

logger = logging.getLogger(__name__)


class TargetService:
    """目标管理服务"""
    
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.http_client = httpx.AsyncClient(timeout=30)
        
    async def create_target(self, target_data: TargetCreate, db: Session) -> Target:
        """创建目标"""
        try:
            # 验证目标数据
            await self._validate_target_data(target_data)
            
            # 创建目标实例
            target = Target(
                name=target_data.name,
                description=target_data.description,
                target_type=target_data.target_type,
                target_url=target_data.target_url,
                target_ip=target_data.target_ip,
                target_port=target_data.target_port,
                target_path=target_data.target_path,
                scan_config=target_data.scan_config or {},
                scan_depth=target_data.scan_depth,
                scan_timeout=target_data.scan_timeout,
                status=TargetStatus.PENDING,
                tags=target_data.tags or [],
                metadata={"created_by": "api"}
            )
            
            db.add(target)
            db.commit()
            db.refresh(target)
            
            # 缓存目标信息
            CacheManager.set(f"target:{target.id}", json.dumps({
                "id": target.id,
                "name": target.name,
                "target_type": target.target_type,
                "status": target.status
            }))
            
            logger.info(f"Target created successfully: {target.id}")
            return target
            
        except Exception as e:
            logger.error(f"Failed to create target: {e}")
            raise
    
    async def update_target(self, target_id: int, target_data: TargetUpdate, db: Session) -> Target:
        """更新目标"""
        try:
            target = db.query(Target).filter(Target.id == target_id).first()
            if not target:
                raise ValueError(f"Target not found: {target_id}")
            
            # 更新字段
            update_data = target_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(target, field, value)
            
            target.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(target)
            
            # 更新缓存
            CacheManager.set(f"target:{target.id}", json.dumps({
                "id": target.id,
                "name": target.name,
                "target_type": target.target_type,
                "status": target.status
            }))
            
            logger.info(f"Target updated successfully: {target.id}")
            return target
            
        except Exception as e:
            logger.error(f"Failed to update target: {e}")
            raise
    
    async def get_target(self, target_id: int, db: Session) -> Target:
        """获取目标"""
        try:
            # 先从缓存获取
            cached_data = CacheManager.get(f"target:{target_id}")
            if cached_data:
                return json.loads(cached_data)
            
            target = db.query(Target).filter(Target.id == target_id).first()
            if not target:
                raise ValueError(f"Target not found: {target_id}")
            
            # 缓存目标信息
            CacheManager.set(f"target:{target.id}", json.dumps({
                "id": target.id,
                "name": target.name,
                "target_type": target.target_type,
                "status": target.status
            }))
            
            return target
            
        except Exception as e:
            logger.error(f"Failed to get target: {e}")
            raise
    
    async def list_targets(self, db: Session, skip: int = 0, limit: int = 100, 
                          target_type: Optional[TargetType] = None, 
                          status: Optional[TargetStatus] = None) -> List[Target]:
        """获取目标列表"""
        try:
            query = db.query(Target)
            
            if target_type:
                query = query.filter(Target.target_type == target_type)
            if status:
                query = query.filter(Target.status == status)
            
            targets = query.offset(skip).limit(limit).all()
            return targets
            
        except Exception as e:
            logger.error(f"Failed to list targets: {e}")
            raise
    
    async def delete_target(self, target_id: int, db: Session) -> bool:
        """删除目标"""
        try:
            target = db.query(Target).filter(Target.id == target_id).first()
            if not target:
                raise ValueError(f"Target not found: {target_id}")
            
            # 删除相关扫描
            db.query(Scan).filter(Scan.target_id == target_id).delete()
            
            # 删除目标
            db.delete(target)
            db.commit()
            
            # 清除缓存
            CacheManager.delete(f"target:{target_id}")
            
            logger.info(f"Target deleted successfully: {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete target: {e}")
            raise
    
    async def discover_targets(self, discovery_request: TargetDiscoveryRequest, db: Session) -> Dict[str, Any]:
        """发现目标"""
        try:
            discovered_targets = []
            errors = []
            
            start_time = time.time()
            
            if discovery_request.target_type == TargetType.NETWORK:
                # 网络发现
                network_targets = await self._discover_network_targets(discovery_request)
                discovered_targets.extend(network_targets)
            elif discovery_request.target_type == TargetType.WEB:
                # Web应用发现
                web_targets = await self._discover_web_targets(discovery_request)
                discovered_targets.extend(web_targets)
            else:
                raise ValueError(f"Unsupported target type for discovery: {discovery_request.target_type}")
            
            # 保存发现的目标
            for target_data in discovered_targets:
                try:
                    target = Target(
                        name=target_data["name"],
                        description=target_data.get("description", ""),
                        target_type=target_data["target_type"],
                        target_url=target_data.get("target_url"),
                        target_ip=target_data.get("target_ip"),
                        target_port=target_data.get("target_port"),
                        target_path=target_data.get("target_path", ""),
                        status=TargetStatus.ACTIVE,
                        tags=target_data.get("tags", []),
                        metadata={"discovered_by": "discovery_service"}
                    )
                    
                    db.add(target)
                    db.commit()
                    db.refresh(target)
                    
                    target_data["id"] = target.id
                    
                except Exception as e:
                    errors.append(f"Failed to save target {target_data.get('name', 'unknown')}: {e}")
            
            scan_time = time.time() - start_time
            
            return {
                "discovered_targets": discovered_targets,
                "scan_time": scan_time,
                "success_count": len(discovered_targets),
                "error_count": len(errors),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to discover targets: {e}")
            raise
    
    async def _validate_target_data(self, target_data: TargetCreate):
        """验证目标数据"""
        if target_data.target_url:
            # 验证URL
            if not validate_url(target_data.target_url):
                raise ValueError(f"Invalid URL: {target_data.target_url}")
            
            # 解析URL获取端口
            parsed = urlparse(target_data.target_url)
            if not target_data.target_port and parsed.port:
                target_data.target_port = parsed.port
        
        if target_data.target_ip:
            # 验证IP地址
            if not validate_ip(target_data.target_ip):
                raise ValueError(f"Invalid IP address: {target_data.target_ip}")
        
        # 验证端口范围
        if target_data.target_port:
            if not (1 <= target_data.target_port <= 65535):
                raise ValueError(f"Invalid port number: {target_data.target_port}")
    
    async def _discover_network_targets(self, discovery_request: TargetDiscoveryRequest) -> List[Dict[str, Any]]:
        """发现网络目标"""
        discovered = []
        
        try:
            if discovery_request.network_range:
                # 使用nmap进行网络扫描
                self.nm.scan(discovery_request.network_range, arguments="-sn")
                
                for host in self.nm.all_hosts():
                    if self.nm[host].state() == "up":
                        target_data = {
                            "name": f"Host-{host}",
                            "target_type": TargetType.NETWORK,
                            "target_ip": host,
                            "target_port": None,
                            "tags": ["discovered", "network"],
                            "metadata": {
                                "discovery_method": "nmap",
                                "state": self.nm[host].state()
                            }
                        }
                        
                        # 获取端口信息
                        if "tcp" in self.nm[host]:
                            for port in self.nm[host]["tcp"]:
                                target_data["target_port"] = port
                                target_data["name"] = f"Service-{host}:{port}"
                                break
                        
                        discovered.append(target_data)
        
        except Exception as e:
            logger.error(f"Network discovery failed: {e}")
        
        return discovered
    
    async def _discover_web_targets(self, discovery_request: TargetDiscoveryRequest) -> List[Dict[str, Any]]:
        """发现Web目标"""
        discovered = []
        
        try:
            if discovery_request.network_range:
                # 假设网络范围是CIDR格式
                network = ipaddress.ip_network(discovery_request.network_range, strict=False)
                
                # 扫描常见的Web端口
                common_ports = [80, 443, 8080, 8443, 3000, 5000, 8000, 9000]
                
                for ip in network.hosts():
                    for port in common_ports:
                        try:
                            # 检查端口是否开放
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(1)
                            result = sock.connect_ex((str(ip), port))
                            sock.close()
                            
                            if result == 0:
                                # 检查是否是Web服务
                                url = f"http://{str(ip)}:{port}"
                                if port == 443:
                                    url = f"https://{str(ip)}:{port}"
                                
                                try:
                                    response = await self.http_client.get(url, timeout=5)
                                    
                                    target_data = {
                                        "name": f"Web-{str(ip)}:{port}",
                                        "target_type": TargetType.WEB,
                                        "target_url": url,
                                        "target_ip": str(ip),
                                        "target_port": port,
                                        "tags": ["discovered", "web"],
                                        "metadata": {
                                            "discovery_method": "network_scan",
                                            "status_code": response.status_code,
                                            "server": response.headers.get("server", ""),
                                            "content_type": response.headers.get("content_type", "")
                                        }
                                    }
                                    
                                    discovered.append(target_data)
                                    
                                except Exception as e:
                                    logger.debug(f"Failed to connect to {url}: {e}")
                                    
                        except Exception as e:
                            logger.debug(f"Port scan failed for {str(ip)}:{port}: {e}")
        
        except Exception as e:
            logger.error(f"Web discovery failed: {e}")
        
        return discovered
    
    async def get_target_statistics(self, db: Session) -> Dict[str, Any]:
        """获取目标统计信息"""
        try:
            total_targets = db.query(Target).count()
            active_targets = db.query(Target).filter(Target.status == TargetStatus.ACTIVE).count()
            inactive_targets = db.query(Target).filter(Target.status == TargetStatus.INACTIVE).count()
            pending_targets = db.query(Target).filter(Target.status == TargetStatus.PENDING).count()
            
            # 按类型统计
            type_stats = {}
            for target_type in TargetType:
                count = db.query(Target).filter(Target.target_type == target_type).count()
                type_stats[target_type.value] = count
            
            # 按状态统计
            status_stats = {}
            for status in TargetStatus:
                count = db.query(Target).filter(Target.status == status).count()
                status_stats[status.value] = count
            
            return {
                "total_targets": total_targets,
                "active_targets": active_targets,
                "inactive_targets": inactive_targets,
                "pending_targets": pending_targets,
                "type_statistics": type_stats,
                "status_statistics": status_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get target statistics: {e}")
            raise