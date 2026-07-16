import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import concurrent.futures
import threading
from queue import PriorityQueue

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db, CacheManager, TaskManager
from models.target import Target, TargetType, TargetStatus
from models.scan import Scan, ScanType, ScanStatus, ScanResult, ScanProgressUpdate
from models.user import User
from services.ai.ai_service import AIScanner
from services.ai.risk_assessment import RiskAssessmentEngine
from utils.security import validate_url, validate_ip

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.task_queue = asyncio.PriorityQueue()
        self.running = True
        self.scheduled_tasks = {}
        
    def schedule_task(self, task_data: Dict[str, Any], priority: TaskPriority):
        """调度任务"""
        try:
            # 创建任务项
            task_item = {
                'priority': self._priority_to_weight(priority),
                'task_data': task_data,
                'scheduled_at': datetime.utcnow(),
                'status': TaskStatus.PENDING
            }
            
            # 入队
            self.task_queue.put_nowait((task_item['priority'], task_item))
            
            # 记录调度
            task_id = task_data['task_id']
            self.scheduled_tasks[task_id] = task_item
            
            logger.info(f"Task scheduled: {task_id} with priority {priority}")
            
        except Exception as e:
            logger.error(f"Failed to schedule task: {e}")
            raise
    
    def _priority_to_weight(self, priority: TaskPriority) -> int:
        """将优先级转换为权重"""
        weight_mapping = {
            TaskPriority.CRITICAL: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.MEDIUM: 3,
            TaskPriority.LOW: 4
        }
        return weight_mapping.get(priority, 4)
    
    async def get_next_task(self) -> Optional[Dict[str, Any]]:
        """获取下一个任务"""
        try:
            if self.task_queue.empty():
                return None
            
            # 获取最高优先级任务
            priority, task_item = await self.task_queue.get()
            return task_item['task_data']
            
        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            if task_id in self.scheduled_tasks:
                task_item = self.scheduled_tasks[task_id]
                task_item['status'] = TaskStatus.CANCELLED
                logger.info(f"Task cancelled: {task_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            pending_count = self.task_queue.qsize()
            scheduled_count = len(self.scheduled_tasks)
            
            # 统计各优先级任务数量
            priority_counts = {
                TaskPriority.CRITICAL: 0,
                TaskPriority.HIGH: 0,
                TaskPriority.MEDIUM: 0,
                TaskPriority.LOW: 0
            }
            
            for task_id, task_item in self.scheduled_tasks.items():
                if task_item['status'] == TaskStatus.PENDING:
                    priority_counts[task_item['priority']] += 1
            
            return {
                'pending_tasks': pending_count,
                'scheduled_tasks': scheduled_count,
                'priority_distribution': priority_counts,
                'scheduler_status': 'running' if self.running else 'stopped'
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {
                'pending_tasks': 0,
                'scheduled_tasks': 0,
                'priority_distribution': {},
                'scheduler_status': 'error'
            }


class EngineService:
    """扫描执行引擎服务"""
    
    def __init__(self):
        self.ai_scanner = AIScanner()
        self.risk_assessment = RiskAssessmentEngine()
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks = {}
        self.completed_tasks = {}
        self.max_concurrent_tasks = 10
        self.task_timeout = 3600  # 1小时
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        
        # 任务调度器
        self.scheduler = TaskScheduler()
        self.scheduler_task = asyncio.create_task(self._schedule_tasks())
        
        # 启动任务处理器
        self.processor_task = asyncio.create_task(self._process_tasks())
        
        # 启动监控任务
        self.monitor_task = asyncio.create_task(self._monitor_tasks())
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'average_execution_time': 0,
            'throughput': 0
        }
        
    async def start_scan(self, scan_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """启动扫描任务"""
        try:
            # 获取扫描信息
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
            
            # 检查扫描状态
            if scan.status != ScanStatus.PENDING:
                raise ValueError(f"Scan is not in pending state: {scan.status}")
            
            # 获取目标信息
            target = db.query(Target).filter(Target.id == scan.target_id).first()
            if not target:
                raise ValueError(f"Target not found: {scan.target_id}")
            
            # 创建任务
            task_id = str(uuid.uuid4())
            task_data = {
                "task_id": task_id,
                "scan_id": scan_id,
                "user_id": user_id,
                "target_id": target.id,
                "target_type": target.target_type,
                "target_url": target.target_url,
                "target_ip": target.target_ip,
                "scan_type": scan.scan_type,
                "scan_config": scan.scan_config or {},
                "priority": self._get_task_priority(scan),
                "created_at": datetime.utcnow().isoformat(),
                "status": TaskStatus.PENDING
            }
            
            # 入队任务
            await self.task_queue.put(task_data)
            
            # 更新扫描状态
            scan.status = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            scan.worker_id = task_id
            db.commit()
            
            # 缓存任务信息
            CacheManager.set(f"task:{task_id}", json.dumps(task_data))
            
            logger.info(f"Scan task started: {task_id} for scan {scan_id}")
            
            return {
                "task_id": task_id,
                "scan_id": scan_id,
                "status": TaskStatus.PENDING,
                "message": "Task queued successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start scan: {e}")
            raise
    
    async def cancel_scan(self, scan_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """取消扫描任务"""
        try:
            # 获取扫描信息
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
            
            # 检查权限
            if scan.user_id != user_id:
                raise ValueError("Permission denied")
            
            # 获取任务ID
            task_id = scan.worker_id
            if not task_id:
                raise ValueError("No running task found")
            
            # 取消任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.cancel()
                del self.running_tasks[task_id]
            
            # 更新扫描状态
            scan.status = ScanStatus.CANCELLED
            scan.completed_at = datetime.utcnow()
            db.commit()
            
            # 更新任务状态
            CacheManager.set(f"task:{task_id}", json.dumps({
                "task_id": task_id,
                "scan_id": scan_id,
                "status": TaskStatus.CANCELLED,
                "cancelled_at": datetime.utcnow().isoformat()
            }))
            
            logger.info(f"Scan task cancelled: {task_id} for scan {scan_id}")
            
            return {
                "task_id": task_id,
                "scan_id": scan_id,
                "status": TaskStatus.CANCELLED,
                "message": "Task cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel scan: {e}")
            raise
    
    async def get_scan_status(self, scan_id: int, db: Session) -> Dict[str, Any]:
        """获取扫描状态"""
        try:
            # 获取扫描信息
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
            
            # 获取任务信息
            task_id = scan.worker_id
            task_data = None
            
            if task_id:
                task_data_str = CacheManager.get(f"task:{task_id}")
                if task_data_str:
                    task_data = json.loads(task_data_str)
            
            return {
                "scan_id": scan_id,
                "scan_name": scan.name,
                "scan_type": scan.scan_type,
                "target_id": scan.target_id,
                "status": scan.status,
                "progress": scan.progress,
                "started_at": scan.started_at,
                "completed_at": scan.completed_at,
                "task_id": task_id,
                "task_data": task_data,
                "total_findings": scan.total_findings,
                "critical_findings": scan.critical_findings,
                "high_findings": scan.high_findings,
                "medium_findings": scan.medium_findings,
                "low_findings": scan.low_findings,
                "info_findings": scan.info_findings
            }
            
        except Exception as e:
            logger.error(f"Failed to get scan status: {e}")
            raise
    
    async def list_running_scans(self, db: Session) -> List[Dict[str, Any]]:
        """列出正在运行的扫描"""
        try:
            running_scans = []
            
            for task_id, task in self.running_tasks.items():
                try:
                    task_data_str = CacheManager.get(f"task:{task_id}")
                    if task_data_str:
                        task_data = json.loads(task_data_str)
                        running_scans.append(task_data)
                except Exception as e:
                    logger.error(f"Failed to get task data for {task_id}: {e}")
            
            return running_scans
            
        except Exception as e:
            logger.error(f"Failed to list running scans: {e}")
            return []
    
    async def get_queue_status(self, db: Session) -> Dict[str, Any]:
        """获取队列状态"""
        try:
            pending_count = self.task_queue.qsize()
            running_count = len(self.running_tasks)
            
            return {
                "pending_tasks": pending_count,
                "running_tasks": running_count,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "queue_size": pending_count + running_count,
                "engine_status": "running" if self.processor_task else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            raise
    
    async def _schedule_tasks(self):
        """任务调度器"""
        try:
            logger.info("Task scheduler started")
            
            while self.scheduler.running:
                try:
                    # 获取下一个任务
                    task_data = await self.scheduler.get_next_task()
                    if not task_data:
                        await asyncio.sleep(1)
                        continue
                    
                    task_id = task_data["task_id"]
                    
                    # 检查并发限制
                    if len(self.running_tasks) >= self.max_concurrent_tasks:
                        # 等待后再尝试
                        await asyncio.sleep(1)
                        self.scheduler.schedule_task(task_data, task_data["priority"])
                        continue
                    
                    # 创建任务
                    task = asyncio.create_task(self._execute_task(task_data))
                    self.running_tasks[task_id] = task
                    
                    # 设置任务超时
                    task.set_name(f"task_{task_id}")
                    
                    # 等待任务完成
                    await task
                    
                    # 清理任务
                    del self.running_tasks[task_id]
                    self.completed_tasks[task_id] = task_data
                    
                except asyncio.CancelledError:
                    logger.info("Task scheduler cancelled")
                    break
                except Exception as e:
                    logger.error(f"Task scheduling error: {e}")
                    # 重新调度失败的任务
                    if "task_data" in locals():
                        self.scheduler.schedule_task(task_data, task_data["priority"])
                
        except Exception as e:
            logger.error(f"Task scheduler failed: {e}")
    
    async def _monitor_tasks(self):
        """任务监控"""
        try:
            logger.info("Task monitor started")
            
            while True:
                try:
                    # 监控运行中的任务
                    for task_id, task in list(self.running_tasks.items()):
                        try:
                            # 检查任务是否超时
                            if task.done():
                                continue
                            
                            # 检查任务是否超时
                            task_start = task.get_name().replace("task_", "")
                            if task_start in self.completed_tasks:
                                continue
                            
                            # 获取任务开始时间
                            task_data_str = CacheManager.get(f"task:{task_id}")
                            if task_data_str:
                                task_data = json.loads(task_data_str)
                                started_at = datetime.fromisoformat(task_data.get("started_at", datetime.utcnow().isoformat()))
                                
                                # 检查超时
                                if (datetime.utcnow() - started_at).total_seconds() > self.task_timeout:
                                    task.cancel()
                                    logger.warning(f"Task timeout: {task_id}")
                                    
                        except Exception as e:
                            logger.error(f"Task monitoring error for {task_id}: {e}")
                    
                    # 更新统计信息
                    self._update_statistics()
                    
                    # 等待下一次检查
                    await asyncio.sleep(30)
                    
                except asyncio.CancelledError:
                    logger.info("Task monitor cancelled")
                    break
                except Exception as e:
                    logger.error(f"Task monitoring error: {e}")
                    await asyncio.sleep(30)
                
        except Exception as e:
            logger.error(f"Task monitor failed: {e}")
    
    def _update_statistics(self):
        """更新统计信息"""
        try:
            # 计算任务统计
            self.stats['total_tasks'] = len(self.completed_tasks) + len(self.running_tasks)
            self.stats['completed_tasks'] = len(self.completed_tasks)
            
            # 计算平均执行时间
            if self.completed_tasks:
                execution_times = []
                for task_id in self.completed_tasks:
                    task_data_str = CacheManager.get(f"task:{task_id}")
                    if task_data_str:
                        task_data = json.loads(task_data_str)
                        started_at = datetime.fromisoformat(task_data.get("started_at", datetime.utcnow().isoformat()))
                        completed_at = datetime.fromisoformat(task_data.get("completed_at", datetime.utcnow().isoformat()))
                        execution_time = (completed_at - started_at).total_seconds()
                        execution_times.append(execution_time)
                
                if execution_times:
                    self.stats['average_execution_time'] = sum(execution_times) / len(execution_times)
            
            # 计算吞吐量（每小时任务数）
            if self.stats['average_execution_time'] > 0:
                self.stats['throughput'] = 3600 / self.stats['average_execution_time']
                
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
    
    async def _process_tasks(self):
        """处理任务队列（保持向后兼容）"""
        try:
            logger.info("Task processor started")
            
            while True:
                try:
                    # 获取任务
                    task_data = await self.task_queue.get()
                    task_id = task_data["task_id"]
                    
                    # 检查并发限制
                    if len(self.running_tasks) >= self.max_concurrent_tasks:
                        # 等待后再尝试
                        await asyncio.sleep(1)
                        await self.task_queue.put(task_data)
                        continue
                    
                    # 创建任务
                    task = asyncio.create_task(self._execute_task(task_data))
                    self.running_tasks[task_id] = task
                    
                    # 设置任务超时
                    task.set_name(f"task_{task_id}")
                    
                    # 等待任务完成
                    await task
                    
                    # 清理任务
                    del self.running_tasks[task_id]
                    
                except asyncio.CancelledError:
                    logger.info("Task processor cancelled")
                    break
                except Exception as e:
                    logger.error(f"Task processing error: {e}")
                    # 重新入队失败的任务
                    if "task_data" in locals():
                        await self.task_queue.put(task_data)
                
        except Exception as e:
            logger.error(f"Task processor failed: {e}")
    
    async def _execute_task(self, task_data: Dict[str, Any]):
        """执行单个任务"""
        try:
            task_id = task_data["task_id"]
            scan_id = task_data["scan_id"]
            target_id = task_data["target_id"]
            
            logger.info(f"Executing task: {task_id}")
            
            # 更新任务状态
            task_data["status"] = TaskStatus.RUNNING
            task_data["started_at"] = datetime.utcnow().isoformat()
            CacheManager.set(f"task:{task_id}", json.dumps(task_data))
            
            # 获取数据库会话
            db = next(get_db())
            
            try:
                # 执行扫描
                results = await self.ai_scanner.scan_target(scan_id, task_data, db)
                
                # 保存结果
                await self._save_scan_results(scan_id, results, db)
                
                # 执行风险评估
                target = db.query(Target).filter(Target.id == target_id).first()
                if target:
                    risk_assessment = await self.risk_assessment.assess_risk(scan_id, target, results, db)
                    logger.info(f"Risk assessment completed for scan {scan_id}")
                
                # 更新扫描状态
                scan = db.query(Scan).filter(Scan.id == scan_id).first()
                if scan:
                    scan.status = ScanStatus.COMPLETED
                    scan.completed_at = datetime.utcnow()
                    scan.progress = 100
                    scan.actual_duration = int((datetime.utcnow() - scan.started_at).total_seconds())
                    
                    # 统计结果
                    scan.total_findings = len(results)
                    scan.critical_findings = len([r for r in results if r.severity == "critical"])
                    scan.high_findings = len([r for r in results if r.severity == "high"])
                    scan.medium_findings = len([r for r in results if r.severity == "medium"])
                    scan.low_findings = len([r for r in results if r.severity == "low"])
                    scan.info_findings = len([r for r in results if r.severity == "info"])
                    
                    # 更新任务状态
                    task_data["status"] = TaskStatus.COMPLETED
                    task_data["completed_at"] = datetime.utcnow().isoformat()
                    CacheManager.set(f"task:{task_id}", json.dumps(task_data))
                    
                    db.commit()
                    logger.info(f"Task completed: {task_id}")
                
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                
                # 更新任务状态为失败
                task_data["status"] = TaskStatus.FAILED
                task_data["error"] = str(e)
                task_data["completed_at"] = datetime.utcnow().isoformat()
                CacheManager.set(f"task:{task_id}", json.dumps(task_data))
                
                # 更新扫描状态
                scan = db.query(Scan).filter(Scan.id == scan_id).first()
                if scan:
                    scan.status = ScanStatus.FAILED
                    scan.completed_at = datetime.utcnow()
                    db.commit()
                
                # 更新统计
                self.stats['failed_tasks'] += 1
                
                raise
                
        except asyncio.CancelledError:
            logger.info(f"Task cancelled: {task_id}")
            
            # 更新任务状态为取消
            task_data["status"] = TaskStatus.CANCELLED
            task_data["cancelled_at"] = datetime.utcnow().isoformat()
            CacheManager.set(f"task:{task_id}", json.dumps(task_data))
            
            # 更新扫描状态
            db = next(get_db())
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = ScanStatus.CANCELLED
                scan.completed_at = datetime.utcnow()
                db.commit()
            
            # 更新统计
            self.stats['cancelled_tasks'] += 1
            
            raise
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            raise
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        try:
            # 获取队列状态
            queue_status = await self.get_queue_status()
            
            # 获取调度器状态
            scheduler_status = self.scheduler.get_queue_status()
            
            # 获取运行中任务
            running_tasks = await self.list_running_scans()
            
            # 获取统计信息
            stats = self.stats.copy()
            
            return {
                'engine_status': 'running',
                'queue_status': queue_status,
                'scheduler_status': scheduler_status,
                'running_tasks': running_tasks,
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get engine status: {e}")
            return {
                'engine_status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务历史"""
        try:
            # 获取已完成任务
            completed_tasks = list(self.completed_tasks.values())[-limit:]
            
            # 获取运行中任务
            running_tasks = list(self.running_tasks.values())
            
            # 合并并排序
            all_tasks = completed_tasks + running_tasks
            all_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # 限制返回数量
            return all_tasks[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get task history: {e}")
            return []
    
    async def cancel_task_by_id(self, task_id: str) -> bool:
        """根据任务ID取消任务"""
        try:
            # 取消运行中的任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.cancel()
                del self.running_tasks[task_id]
                
                # 更新任务状态
                task_data_str = CacheManager.get(f"task:{task_id}")
                if task_data_str:
                    task_data = json.loads(task_data_str)
                    task_data["status"] = TaskStatus.CANCELLED
                    task_data["cancelled_at"] = datetime.utcnow().isoformat()
                    CacheManager.set(f"task:{task_id}", json.dumps(task_data))
                
                logger.info(f"Task cancelled by ID: {task_id}")
                return True
            
            # 取消调度中的任务
            return self.scheduler.cancel_task(task_id)
            
        except Exception as e:
            logger.error(f"Failed to cancel task by ID: {e}")
            return False r.severity == "info"])
                    
                    db.commit()
                
                # 更新任务状态
                task_data["status"] = TaskStatus.COMPLETED
                task_data["completed_at"] = datetime.utcnow().isoformat()
                task_data["results_count"] = len(results)
                CacheManager.set(f"task:{task_id}", json.dumps(task_data))
                
                logger.info(f"Task completed: {task_id} with {len(results)} results")
                
            except Exception as e:
                logger.error(f"Task execution failed: {task_id} - {e}")
                
                # 更新任务状态
                task_data["status"] = TaskStatus.FAILED
                task_data["failed_at"] = datetime.utcnow().isoformat()
                task_data["error"] = str(e)
                CacheManager.set(f"task:{task_id}", json.dumps(task_data))
                
                # 更新扫描状态
                scan = db.query(Scan).filter(Scan.id == scan_id).first()
                if scan:
                    scan.status = ScanStatus.FAILED
                    scan.completed_at = datetime.utcnow()
                    db.commit()
                
                raise
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            raise
    
    async def _save_scan_results(self, scan_id: int, results: List[Dict[str, Any]], db: Session):
        """保存扫描结果"""
        try:
            for result_data in results:
                # 创建扫描结果
                scan_result = ScanResult(
                    scan_id=scan_id,
                    finding_type=result_data.get("finding_type", "unknown"),
                    title=result_data.get("title", "Unknown Finding"),
                    description=result_data.get("description", ""),
                    severity=result_data.get("severity", "medium"),
                    confidence=result_data.get("confidence", 85),
                    location=result_data.get("location", ""),
                    parameter=result_data.get("parameter", ""),
                    method=result_data.get("method", ""),
                    headers=result_data.get("headers", {}),
                    cookies=result_data.get("cookies", {}),
                    vulnerability_type=result_data.get("vulnerability_type", ""),
                    cve_id=result_data.get("cve_id", ""),
                    cwe_id=result_data.get("cwe_id", ""),
                    owasp_top_10=result_data.get("owasp_top_10", ""),
                    recommendation=result_data.get("recommendation", ""),
                    affected_components=result_data.get("affected_components", []),
                    proof_of_concept=result_data.get("proof_of_concept", ""),
                    references=result_data.get("references", []),
                    metadata=result_data.get("metadata", {}),
                    tags=result_data.get("tags", [])
                )
                
                db.add(scan_result)
            
            db.commit()
            logger.info(f"Saved {len(results)} scan results for scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to save scan results: {e}")
            raise
    
    def _get_task_priority(self, scan: Scan) -> TaskPriority:
        """获取任务优先级"""
        # 根据扫描类型和目标类型确定优先级
        if scan.scan_type == ScanType.PENETRATION:
            return TaskPriority.CRITICAL
        elif scan.scan_type == ScanType.VULNERABILITY:
            return TaskPriority.HIGH
        elif scan.scan_type == ScanType.ASSESSMENT:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    async def pause_scan(self, scan_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """暂停扫描任务"""
        try:
            # 获取扫描信息
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
            
            # 检查权限
            if scan.user_id != user_id:
                raise ValueError("Permission denied")
            
            # 获取任务ID
            task_id = scan.worker_id
            if not task_id:
                raise ValueError("No running task found")
            
            # 暂停任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.cancel()
                del self.running_tasks[task_id]
            
            # 更新扫描状态
            scan.status = ScanStatus.PAUSED
            db.commit()
            
            # 更新任务状态
            task_data_str = CacheManager.get(f"task:{task_id}")
            if task_data_str:
                task_data = json.loads(task_data_str)
                task_data["status"] = TaskStatus.PAUSED
                task_data["paused_at"] = datetime.utcnow().isoformat()
                CacheManager.set(f"task:{task_id}", json.dumps(task_data))
            
            logger.info(f"Scan task paused: {task_id} for scan {scan_id}")
            
            return {
                "task_id": task_id,
                "scan_id": scan_id,
                "status": TaskStatus.PAUSED,
                "message": "Task paused successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to pause scan: {e}")
            raise
    
    async def resume_scan(self, scan_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """恢复扫描任务"""
        try:
            # 获取扫描信息
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
            
            # 检查权限
            if scan.user_id != user_id:
                raise ValueError("Permission denied")
            
            # 检查扫描状态
            if scan.status != ScanStatus.PAUSED:
                raise ValueError(f"Scan is not in paused state: {scan.status}")
            
            # 创建任务
            task_id = str(uuid.uuid4())
            task_data = {
                "task_id": task_id,
                "scan_id": scan_id,
                "user_id": user_id,
                "target_id": scan.target_id,
                "target_type": scan.target.target_type if scan.target else None,
                "target_url": scan.target.target_url if scan.target else None,
                "target_ip": scan.target.target_ip if scan.target else None,
                "scan_type": scan.scan_type,
                "scan_config": scan.scan_config or {},
                "priority": self._get_task_priority(scan),
                "created_at": datetime.utcnow().isoformat(),
                "status": TaskStatus.PENDING,
                "resumed_from": scan_id
            }
            
            # 入队任务
            await self.task_queue.put(task_data)
            
            # 更新扫描状态
            scan.status = ScanStatus.RUNNING
            scan.worker_id = task_id
            db.commit()
            
            # 缓存任务信息
            CacheManager.set(f"task:{task_id}", json.dumps(task_data))
            
            logger.info(f"Scan task resumed: {task_id} for scan {scan_id}")
            
            return {
                "task_id": task_id,
                "scan_id": scan_id,
                "status": TaskStatus.PENDING,
                "message": "Task resumed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to resume scan: {e}")
            raise
    
    async def get_task_statistics(self, db: Session) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            # 获取队列状态
            queue_status = await self.get_queue_status(db)
            
            # 获取运行中的扫描
            running_scans = await self.list_running_scans(db)
            
            # 统计任务状态
            task_status_counts = {
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "paused": 0
            }
            
            for task in running_scans:
                status = task.get("status", "unknown")
                if status in task_status_counts:
                    task_status_counts[status] += 1
            
            # 从缓存获取已完成任务
            task_keys = CacheManager.get_keys("task:*")
            for key in task_keys:
                task_data_str = CacheManager.get(key)
                if task_data_str:
                    task_data = json.loads(task_data_str)
                    status = task_data.get("status", "unknown")
                    if status in task_status_counts:
                        task_status_counts[status] += 1
            
            return {
                "queue_status": queue_status,
                "task_statistics": task_status_counts,
                "running_scans": len(running_scans),
                "total_tasks": sum(task_status_counts.values()),
                "engine_status": "running" if self.processor_task else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to get task statistics: {e}")
            raise
    
    async def cleanup_old_tasks(self, days: int = 7, db: Session = None):
        """清理旧任务"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 清理缓存中的旧任务
            task_keys = CacheManager.get_keys("task:*")
            for key in task_keys:
                task_data_str = CacheManager.get(key)
                if task_data_str:
                    task_data = json.loads(task_data_str)
                    created_at = task_data.get("created_at")
                    if created_at:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if created_date < cutoff_date:
                            CacheManager.delete(key)
                            logger.info(f"Cleaned up old task: {key}")
            
            # 清理数据库中的旧扫描结果
            if db:
                from models.scan import ScanResult
                old_results = db.query(ScanResult).filter(
                    ScanResult.created_at < cutoff_date
                ).all()
                
                for result in old_results:
                    db.delete(result)
                
                db.commit()
                logger.info(f"Cleaned up {len(old_results)} old scan results")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")
            raise
    
    async def shutdown(self):
        """关闭引擎"""
        try:
            logger.info("Shutting down engine...")
            
            # 取消所有运行中的任务
            for task_id, task in self.running_tasks.items():
                task.cancel()
            
            # 等待任务完成
            if self.running_tasks:
                await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
            
            # 停止任务处理器
            if self.processor_task:
                self.processor_task.cancel()
                try:
                    await self.processor_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            logger.info("Engine shutdown completed")
            
        except Exception as e:
            logger.error(f"Engine shutdown failed: {e}")
            raise