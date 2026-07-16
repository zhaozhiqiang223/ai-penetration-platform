import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from services.engine.engine_service import (
    EngineService, TaskPriority, TaskStatus, TaskScheduler
)
from models.target import Target, TargetType, TargetStatus
from models.scan import Scan, ScanType, ScanStatus, ScanResult


class TestTaskPriority:
    """测试任务优先级"""
    
    def test_task_priority_values(self):
        """测试任务优先级值"""
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.CRITICAL == "critical"


class TestTaskStatus:
    """测试任务状态"""
    
    def test_task_status_values(self):
        """测试任务状态值"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
        assert TaskStatus.PAUSED == "paused"


class TestTaskScheduler:
    """测试任务调度器"""
    
    def test_task_scheduler_initialization(self):
        """测试任务调度器初始化"""
        scheduler = TaskScheduler()
        assert scheduler.task_queue is not None
        assert scheduler.running is True
        assert scheduler.scheduled_tasks == {}
    
    def test_priority_to_weight(self):
        """测试优先级到权重的转换"""
        scheduler = TaskScheduler()
        
        # 测试不同优先级的权重
        critical_weight = scheduler._priority_to_weight(TaskPriority.CRITICAL)
        high_weight = scheduler._priority_to_weight(TaskPriority.HIGH)
        medium_weight = scheduler._priority_to_weight(TaskPriority.MEDIUM)
        low_weight = scheduler._priority_to_weight(TaskPriority.LOW)
        
        assert critical_weight < high_weight < medium_weight < low_weight
    
    @patch('services.engine.engine_task_scheduler.asyncio.PriorityQueue')
    def test_schedule_task(self, mock_priority_queue):
        """测试任务调度"""
        # 设置mock
        mock_queue = AsyncMock()
        mock_priority_queue.return_value = mock_queue
        
        scheduler = TaskScheduler()
        
        # 创建测试任务
        task_data = {
            "task_id": "test-task-123",
            "scan_id": 1,
            "priority": TaskPriority.HIGH
        }
        
        # 调度任务
        scheduler.schedule_task(task_data, TaskPriority.HIGH)
        
        # 验证任务已调度
        assert "test-task-123" in scheduler.scheduled_tasks
        assert scheduler.scheduled_tasks["test-task-123"]["priority"] == 2  # HIGH的权重
    
    def test_cancel_task(self):
        """测试取消任务"""
        scheduler = TaskScheduler()
        
        # 添加任务
        task_data = {
            "task_id": "test-task-123",
            "scan_id": 1,
            "priority": TaskPriority.HIGH
        }
        scheduler.scheduled_tasks["test-task-123"] = task_data
        
        # 取消任务
        result = scheduler.cancel_task("test-task-123")
        
        # 验证结果
        assert result is True
        assert scheduler.scheduled_tasks["test-task-123"]["status"] == TaskStatus.CANCELLED
        
        # 测试取消不存在的任务
        result = scheduler.cancel_task("non-existent-task")
        assert result is False
    
    def test_get_queue_status(self):
        """测试获取队列状态"""
        scheduler = TaskScheduler()
        
        # 添加任务
        task_data = {
            "task_id": "test-task-123",
            "scan_id": 1,
            "priority": TaskPriority.HIGH
        }
        scheduler.scheduled_tasks["test-task-123"] = task_data
        
        # 获取队列状态
        status = scheduler.get_queue_status()
        
        # 验证状态
        assert "pending_tasks" in status
        assert "scheduled_tasks" in status
        assert "priority_distribution" in status
        assert "scheduler_status" in status
        assert status["scheduled_tasks"] == 1


class TestEngineService:
    """测试引擎服务"""
    
    def test_engine_service_initialization(self):
        """测试引擎服务初始化"""
        with patch('services.engine.engine_service.AIScanner'), \
             patch('services.engine.engine_service.RiskAssessmentEngine'), \
             patch('services.engine.engine_service.TaskScheduler'):
            
            engine = EngineService()
            assert engine is not None
            assert engine.ai_scanner is not None
            assert engine.risk_assessment is not None
            assert engine.scheduler is not None
            assert engine.max_concurrent_tasks == 10
            assert engine.task_timeout == 3600
    
    @patch('services.engine.engine_service.get_db')
    async def test_start_scan(self, mock_get_db):
        """测试启动扫描"""
        # 设置mock
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 创建模拟扫描和目标
        mock_scan = Mock()
        mock_scan.id = 1
        mock_scan.status = ScanStatus.PENDING
        mock_scan.target_id = 1
        mock_scan.scan_type = ScanType.WEB
        mock_scan.scan_config = {}
        
        mock_target = Mock()
        mock_target.id = 1
        mock_target.target_type = TargetType.WEB
        mock_target.target_url = "https://example.com"
        mock_target.target_ip = "192.168.1.1"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_scan, mock_target]
        
        # 创建引擎服务
        with patch('services.engine.engine_service.AIScanner'), \
             patch('services.engine.engine_service.RiskAssessmentEngine'), \
             patch('services.engine.engine_service.TaskScheduler'), \
             patch('services.engine.engine_service.CacheManager') as mock_cache:
            
            engine = EngineService()
            
            # 启动扫描
            result = await engine.start_scan(1, 1, mock_db)
            
            # 验证结果
            assert "task_id" in result
            assert "scan_id" in result
            assert result["status"] == TaskStatus.PENDING
            
            # 验证数据库更新
            assert mock_scan.status == ScanStatus.RUNNING
            assert mock_scan.started_at is not None
            assert mock_scan.worker_id is not None
    
    @patch('services.engine.engine_service.get_db')
    async def test_cancel_scan(self, mock_get_db):
        """测试取消扫描"""
        # 设置mock
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 创建模拟扫描
        mock_scan = Mock()
        mock_scan.id = 1
        mock_scan.status = ScanStatus.RUNNING
        mock_scan.user_id = 1
        mock_scan.worker_id = "test-task-123"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_scan
        
        # 创建引擎服务
        with patch('services.engine.engine_service.AIScanner'), \
             patch('services.engine.engine_service.RiskAssessmentEngine'), \
             patch('services.engine.engine_service.TaskScheduler'), \
             patch('services.engine.engine_service.CacheManager') as mock_cache:
            
            engine = EngineService()
            
            # 添加运行中的任务
            engine.running_tasks["test-task-123"] = Mock()
            
            # 取消扫描
            result = await engine.cancel_scan(1, 1, mock_db)
            
            # 验证结果
            assert result["status"] == TaskStatus.CANCELLED
            
            # 验证数据库更新
            assert mock_scan.status == ScanStatus.CANCELLED
            assert mock_scan.completed_at is not None
    
    @patch('services.engine.engine_service.get_db')
    async def test_get_scan_status(self, mock_get_db):
        """测试获取扫描状态"""
        # 设置mock
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        
        # 创建模拟扫描
        mock_scan = Mock()
        mock_scan.id = 1
        mock_scan.name = "测试扫描"
        mock_scan.scan_type = ScanType.WEB
        mock_scan.target_id = 1
        mock_scan.status = ScanStatus.RUNNING
        mock_scan.progress = 50
        mock_scan.started_at = datetime.utcnow()
        mock_scan.completed_at = None
        mock_scan.worker_id = "test-task-123"
        mock_scan.total_findings = 10
        mock_scan.critical_findings = 2
        mock_scan.high_findings = 3
        mock_scan.medium_findings = 4
        mock_scan.low_findings = 1
        mock_scan.info_findings = 0
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_scan
        
        # 创建引擎服务
        with patch('services.engine.engine_service.AIScanner'), \
             patch('services.engine.engine_service.RiskAssessmentEngine'), \
             patch('services.engine.engine_service.TaskScheduler'), \
             patch('services.engine.engine_service.CacheManager') as mock_cache:
            
            engine = EngineService()
            
            # 模拟任务数据
            mock_cache.get.return_value = '{"task_id": "test-task-123", "status": "running"}'
            
            # 获取扫描状态
            result = await engine.get_scan_status(1, mock_db)
            
            # 验证结果
            assert result["scan_id"] == 1
            assert result["scan_name"] == "测试扫描"
            assert result["status"] == ScanStatus.RUNNING
            assert result["progress"] == 50
            assert result["task_id"] == "test-task-123"
    
    @patch('services.engine.engine_service.get_db')
    async def test_list_running_scans(self, mock_get_db):
        """测试列出运行中的扫描"""
        # 创建引擎服务
        with patch('services.engine.engine_service.AIScanner'), \
             patch('services.engine.engine_service.RiskAssessmentEngine'), \
             patch('services.engine.engine_service.TaskScheduler'), \
             patch('services.engine.engine_service.CacheManager') as mock_cache:
            
            engine = EngineService()
            
            # 模拟运行中的任务
            mock_cache.get.return_value = '{"task_id": "test-task-123", "scan_id": 1}'
            engine.running_tasks["test-task-123"] = Mock()
            
            # 列出运行中的扫描
            result = await engine.list_running_scans(mock_db)
            
            # 验证结果
            assert len(result) == 1
            assert result[0]["task_id"] == "test-task-123"
    
    @patch('services.engine.engine_service.get_db')
    async def test_get_queue_status(self, mock_get_db):
        """测试获取队列状态"""
        # 创建引擎服务
        with patch('services.engine.engine_service.AIScanner'), \
             patch('services.engine.engine_service.RiskAssessmentEngine'), \
             patch('services.engine.engine_service.TaskScheduler'):
            
            engine = EngineService()
            
            # 模拟队列状态
            engine.task_queue.qsize = Mock(return_value=5)
            engine.running_tasks = {"task1": Mock(), "task2": Mock()}
            
            # 获取队列状态
            result = await engine.get_queue_status()
            
            # 验证结果
            assert "pending_tasks" in result
            assert "running_tasks" in result
            assert "max_concurrent_tasks" in result
            assert "queue_size" in result
            assert "engine_status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])