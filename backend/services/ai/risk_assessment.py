"""
AI风险评估模块
实现智能风险评估算法，为漏洞检测提供风险评估功能
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin

import httpx
import numpy as np
import pandas as pd
import tensorflow as tf
from sqlalchemy.orm import Session
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

from database import get_db, CacheManager, TaskManager
from models.target import Target, TargetType, TargetStatus
from models.scan import Scan, ScanType, ScanStatus, ScanResult, ScanSeverity
from models.knowledge import Vulnerability, VulnerabilityType, VulnerabilitySeverity
from utils.security import validate_url, validate_ip, sanitize_input

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险等级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskCategory(str, Enum):
    """风险类别枚举"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    FILE_UPLOAD = "file_upload"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    INFORMATION_DISCLOSURE = "information_disclosure"
    BUSINESS_LOGIC = "business_logic"
    DENIAL_OF_SERVICE = "denial_of_service"


@dataclass
class RiskFactor:
    """风险因素"""
    category: RiskCategory
    severity: RiskLevel
    confidence: float
    description: str
    evidence: List[str]
    impact_score: float
    exploitability_score: float


@dataclass
class RiskAssessment:
    """风险评估结果"""
    risk_score: float
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    recommendations: List[str]
    affected_components: List[str]
    assessment_timestamp: datetime
    assessor_version: str


class RiskMatrix:
    """风险矩阵"""
    
    def __init__(self):
        self.matrix = self._load_risk_matrix()
    
    def _load_risk_matrix(self) -> Dict[str, Dict[str, float]]:
        """加载风险矩阵"""
        return {
            "sql_injection": {
                "critical": 9.0,
                "high": 8.0,
                "medium": 7.0,
                "low": 6.0,
                "info": 1.0
            },
            "xss": {
                "critical": 8.0,
                "high": 7.0,
                "medium": 6.0,
                "low": 5.0,
                "info": 1.0
            },
            "csrf": {
                "critical": 7.0,
                "high": 6.0,
                "medium": 5.0,
                "low": 4.0,
                "info": 1.0
            },
            "file_upload": {
                "critical": 9.0,
                "high": 8.0,
                "medium": 6.0,
                "low": 3.0,
                "info": 1.0
            },
            "authentication": {
                "critical": 9.0,
                "high": 8.0,
                "medium": 7.0,
                "low": 6.0,
                "info": 1.0
            },
            "authorization": {
                "critical": 8.0,
                "high": 7.0,
                "medium": 6.0,
                "low": 5.0,
                "info": 1.0
            },
            "configuration": {
                "critical": 7.0,
                "high": 6.0,
                "medium": 5.0,
                "low": 4.0,
                "info": 1.0
            },
            "information_disclosure": {
                "critical": 6.0,
                "high": 5.0,
                "medium": 4.0,
                "low": 3.0,
                "info": 1.0
            },
            "business_logic": {
                "critical": 8.0,
                "high": 7.0,
                "medium": 6.0,
                "low": 5.0,
                "info": 1.0
            },
            "denial_of_service": {
                "critical": 9.0,
                "high": 8.0,
                "medium": 7.0,
                "low": 6.0,
                "info": 1.0
            }
        }


class RiskScoringModel:
    """风险评分模型"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        try:
            # 加载预训练模型
            self.model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu', input_shape=(10,)),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            # 编译模型
            self.model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            logger.info("Risk scoring model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize risk scoring model: {e}")
            # 使用备用方案
            self.model = None
    
    def calculate_risk_score(self, vulnerabilities: List[Dict[str, Any]]) -> float:
        """计算风险分数"""
        if not vulnerabilities:
            return 0.0
        
        total_score = 0.0
        risk_matrix = RiskMatrix()
        
        for vuln in vulnerabilities:
            # 获取漏洞类别和严重程度
            vuln_category = vuln.get('type', 'unknown')
            vuln_severity = vuln.get('severity', 'info')
            
            # 从风险矩阵获取基础分数
            base_score = risk_matrix.matrix.get(vuln_category, {}).get(vuln_severity, 1.0)
            
            # 根据漏洞特征调整分数
            adjusted_score = self._adjust_score_by_features(base_score, vuln)
            
            # 根据影响范围调整分数
            impact_multiplier = self._calculate_impact_multiplier(vuln)
            
            total_score += adjusted_score * impact_multiplier
        
        # 归一化到0-100范围
        normalized_score = min(100.0, total_score)
        
        return normalized_score
    
    def _adjust_score_by_features(self, base_score: float, vuln: Dict[str, Any]) -> float:
        """根据漏洞特征调整分数"""
        adjusted_score = base_score
        
        # 根据漏洞数量调整
        if vuln.get('count', 1) > 1:
            adjusted_score *= 1.2
        
        # 根据置信度调整
        confidence = vuln.get('confidence', 1.0)
        adjusted_score *= confidence
        
        # 根据可利用性调整
        exploitability = vuln.get('exploitability', 1.0)
        adjusted_score *= exploitability
        
        return adjusted_score
    
    def _calculate_impact_multiplier(self, vuln: Dict[str, Any]) -> float:
        """计算影响范围乘数"""
        impact_multiplier = 1.0
        
        # 根据影响范围调整
        impact_scope = vuln.get('impact_scope', 'single')
        if impact_scope == 'multiple':
            impact_multiplier = 1.5
        elif impact_scope == 'system':
            impact_multiplier = 2.0
        
        # 根据业务影响调整
        business_impact = vuln.get('business_impact', 'low')
        if business_impact == 'high':
            impact_multiplier *= 1.3
        elif business_impact == 'critical':
            impact_multiplier *= 1.5
        
        return impact_multiplier


class RiskAssessmentEngine:
    """风险评估引擎"""
    
    def __init__(self):
        self.risk_matrix = RiskMatrix()
        self.scoring_model = RiskScoringModel()
        self.classifier = None
        self._initialize_classifier()
    
    def _initialize_classifier(self):
        """初始化分类器"""
        try:
            # 使用预训练的分类器
            self.classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Risk assessment classifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize risk assessment classifier: {e}")
            self.classifier = None
    
    async def assess_risk(self, scan_id: int, target: Target, scan_results: List[Dict[str, Any]], db: Session) -> RiskAssessment:
        """评估风险"""
        try:
            logger.info(f"Starting risk assessment for scan {scan_id}, target {target.id}")
            
            # 分析扫描结果
            risk_factors = self._analyze_scan_results(scan_results)
            
            # 计算风险分数
            risk_score = self.scoring_model.calculate_risk_score(scan_results)
            
            # 确定风险等级
            risk_level = self._determine_risk_level(risk_score)
            
            # 生成建议
            recommendations = self._generate_recommendations(risk_factors)
            
            # 确定受影响组件
            affected_components = self._identify_affected_components(scan_results)
            
            # 创建风险评估结果
            assessment = RiskAssessment(
                risk_score=risk_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                recommendations=recommendations,
                affected_components=affected_components,
                assessment_timestamp=datetime.utcnow(),
                assessor_version="1.0.0"
            )
            
            # 保存风险评估结果
            await self._save_risk_assessment(assessment, scan_id, db)
            
            logger.info(f"Risk assessment completed for scan {scan_id}")
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            raise
    
    def _analyze_scan_results(self, scan_results: List[Dict[str, Any]]) -> List[RiskFactor]:
        """分析扫描结果"""
        risk_factors = []
        
        for result in scan_results:
            # 提取漏洞信息
            vuln_type = result.get('type', 'unknown')
            severity = result.get('severity', 'info')
            confidence = result.get('confidence', 1.0)
            description = result.get('description', '')
            evidence = result.get('evidence', [])
            
            # 确定风险类别
            category = self._determine_risk_category(vuln_type)
            
            # 确定风险等级
            risk_level = self._map_severity_to_risk_level(severity)
            
            # 计算影响分数
            impact_score = self._calculate_impact_score(result)
            
            # 计算可利用性分数
            exploitability_score = self._calculate_exploitability_score(result)
            
            # 创建风险因素
            risk_factor = RiskFactor(
                category=category,
                severity=risk_level,
                confidence=confidence,
                description=description,
                evidence=evidence,
                impact_score=impact_score,
                exploitability_score=exploitability_score
            )
            
            risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _determine_risk_category(self, vuln_type: str) -> RiskCategory:
        """确定风险类别"""
        category_mapping = {
            'sql_injection': RiskCategory.SQL_INJECTION,
            'sqli': RiskCategory.SQL_INJECTION,
            'xss': RiskCategory.XSS,
            'cross_site_scripting': RiskCategory.XSS,
            'csrf': RiskCategory.CSRF,
            'cross_site_request_forgery': RiskCategory.CSRF,
            'file_upload': RiskCategory.FILE_UPLOAD,
            'authentication': RiskCategory.AUTHENTICATION,
            'auth': RiskCategory.AUTHENTICATION,
            'authorization': RiskCategory.AUTHORIZATION,
            'authz': RiskCategory.AUTHORIZATION,
            'configuration': RiskCategory.CONFIGURATION,
            'config': RiskCategory.CONFIGURATION,
            'information_disclosure': RiskCategory.INFORMATION_DISCLOSURE,
            'info_disclosure': RiskCategory.INFORMATION_DISCLOSURE,
            'business_logic': RiskCategory.BUSINESS_LOGIC,
            'business': RiskCategory.BUSINESS_LOGIC,
            'denial_of_service': RiskCategory.DENIAL_OF_SERVICE,
            'dos': RiskCategory.DENIAL_OF_SERVICE
        }
        
        return category_mapping.get(vuln_type.lower(), RiskCategory.INFORMATION_DISCLOSURE)
    
    def _map_severity_to_risk_level(self, severity: str) -> RiskLevel:
        """映射严重程度到风险等级"""
        severity_mapping = {
            'critical': RiskLevel.CRITICAL,
            'high': RiskLevel.HIGH,
            'medium': RiskLevel.MEDIUM,
            'low': RiskLevel.LOW,
            'info': RiskLevel.INFO,
            'informational': RiskLevel.INFO
        }
        
        return severity_mapping.get(severity.lower(), RiskLevel.INFO)
    
    def _calculate_impact_score(self, result: Dict[str, Any]) -> float:
        """计算影响分数"""
        impact_score = 1.0
        
        # 根据漏洞类型调整
        vuln_type = result.get('type', 'unknown')
        if vuln_type in ['sql_injection', 'file_upload', 'authentication']:
            impact_score *= 2.0
        
        # 根据影响范围调整
        impact_scope = result.get('impact_scope', 'single')
        if impact_scope == 'multiple':
            impact_score *= 1.5
        elif impact_scope == 'system':
            impact_score *= 2.0
        
        # 根据业务影响调整
        business_impact = result.get('business_impact', 'low')
        if business_impact == 'high':
            impact_score *= 1.3
        elif business_impact == 'critical':
            impact_score *= 1.5
        
        return min(10.0, impact_score)
    
    def _calculate_exploitability_score(self, result: Dict[str, Any]) -> float:
        """计算可利用性分数"""
        exploitability_score = 1.0
        
        # 根据漏洞类型调整
        vuln_type = result.get('type', 'unknown')
        if vuln_type in ['sql_injection', 'xss', 'csrf']:
            exploitability_score *= 1.5
        
        # 根据利用难度调整
        exploit_difficulty = result.get('exploit_difficulty', 'medium')
        if exploit_difficulty == 'low':
            exploitability_score *= 1.5
        elif exploit_difficulty == 'high':
            exploitability_score *= 0.5
        
        # 根据公开利用代码调整
        has_public_exploit = result.get('has_public_exploit', False)
        if has_public_exploit:
            exploitability_score *= 1.3
        
        return min(10.0, exploitability_score)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """根据风险分数确定风险等级"""
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.MEDIUM
        elif risk_score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFO
    
    def _generate_recommendations(self, risk_factors: List[RiskFactor]) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        for factor in risk_factors:
            if factor.severity == RiskLevel.CRITICAL:
                recommendations.append(f"立即修复 {factor.category.value} 漏洞：{factor.description}")
            elif factor.severity == RiskLevel.HIGH:
                recommendations.append(f"高优先级修复 {factor.category.value} 漏洞：{factor.description}")
            elif factor.severity == RiskLevel.MEDIUM:
                recommendations.append(f"中优先级修复 {factor.category.value} 漏洞：{factor.description}")
            elif factor.severity == RiskLevel.LOW:
                recommendations.append(f"低优先级修复 {factor.category.value} 漏洞：{factor.description}")
            else:
                recommendations.append(f"考虑优化 {factor.category.value} 问题：{factor.description}")
        
        # 添加通用建议
        if len(recommendations) == 0:
            recommendations.append("未发现明显的安全风险，建议定期进行安全检查")
        
        return recommendations
    
    def _identify_affected_components(self, scan_results: List[Dict[str, Any]]) -> List[str]:
        """识别受影响的组件"""
        components = set()
        
        for result in scan_results:
            # 提取组件信息
            endpoint = result.get('endpoint', '')
            component = result.get('component', '')
            service = result.get('service', '')
            
            if endpoint:
                components.add(endpoint)
            if component:
                components.add(component)
            if service:
                components.add(service)
        
        return list(components)
    
    async def _save_risk_assessment(self, assessment: RiskAssessment, scan_id: int, db: Session):
        """保存风险评估结果"""
        try:
            # 创建风险评估记录
            from models.report import RiskAssessment as RiskAssessmentModel
            
            assessment_model = RiskAssessmentModel(
                scan_id=scan_id,
                risk_score=assessment.risk_score,
                risk_level=assessment.risk_level.value,
                risk_factors=[{
                    'category': rf.category.value,
                    'severity': rf.severity.value,
                    'confidence': rf.confidence,
                    'description': rf.description,
                    'evidence': rf.evidence,
                    'impact_score': rf.impact_score,
                    'exploitability_score': rf.exploitability_score
                } for rf in assessment.risk_factors],
                recommendations=assessment.recommendations,
                affected_components=assessment.affected_components,
                assessment_timestamp=assessment.assessment_timestamp,
                assessor_version=assessment.assessor_version
            )
            
            db.add(assessment_model)
            db.commit()
            
            logger.info(f"Risk assessment saved for scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to save risk assessment: {e}")
            raise
    
    def get_risk_trends(self, target_id: int, days: int = 30) -> Dict[str, Any]:
        """获取风险趋势分析"""
        try:
            # 计算日期范围
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 查询历史风险评估
            from models.report import RiskAssessment as RiskAssessmentModel
            
            db = next(get_db())
            assessments = db.query(RiskAssessmentModel).filter(
                RiskAssessmentModel.assessment_timestamp >= start_date,
                RiskAssessmentModel.assessment_timestamp <= end_date
            ).all()
            
            # 分析趋势
            trend_data = []
            for assessment in assessments:
                trend_data.append({
                    'date': assessment.assessment_timestamp.isoformat(),
                    'risk_score': assessment.risk_score,
                    'risk_level': assessment.risk_level,
                    'findings_count': len(assessment.risk_factors)
                })
            
            # 计算统计信息
            if trend_data:
                avg_risk_score = sum(d['risk_score'] for d in trend_data) / len(trend_data)
                max_risk_score = max(d['risk_score'] for d in trend_data)
                min_risk_score = min(d['risk_score'] for d in trend_data)
            else:
                avg_risk_score = 0
                max_risk_score = 0
                min_risk_score = 0
            
            return {
                'target_id': target_id,
                'period_days': days,
                'assessments_count': len(assessments),
                'trend_data': trend_data,
                'statistics': {
                    'average_risk_score': round(avg_risk_score, 2),
                    'max_risk_score': max_risk_score,
                    'min_risk_score': min_risk_score,
                    'risk_score_trend': 'increasing' if avg_risk_score > 50 else 'decreasing'
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get risk trends: {e}")
            return {
                'target_id': target_id,
                'period_days': days,
                'assessments_count': 0,
                'trend_data': [],
                'statistics': {
                    'average_risk_score': 0,
                    'max_risk_score': 0,
                    'min_risk_score': 0,
                    'risk_score_trend': 'stable'
                }
            }l_injection': RiskCategory.SQL_INJECTION,
            'xss': RiskCategory.XSS,
            'csrf': RiskCategory.CSRF,
            'file_upload': RiskCategory.FILE_UPLOAD,
            'authentication': RiskCategory.AUTHENTICATION,
            'authorization': RiskCategory.AUTHORIZATION,
            'configuration': RiskCategory.CONFIGURATION,
            'information_disclosure': RiskCategory.INFORMATION_DISCLOSURE,
            'business_logic': RiskCategory.BUSINESS_LOGIC,
            'denial_of_service': RiskCategory.DENIAL_OF_SERVICE
        }
        
        return category_mapping.get(vuln_type, RiskCategory.INFORMATION_DISCLOSURE)
    
    def _map_severity_to_risk_level(self, severity: str) -> RiskLevel:
        """映射严重程度到风险等级"""
        severity_mapping = {
            'critical': RiskLevel.CRITICAL,
            'high': RiskLevel.HIGH,
            'medium': RiskLevel.MEDIUM,
            'low': RiskLevel.LOW,
            'info': RiskLevel.INFO
        }
        
        return severity_mapping.get(severity, RiskLevel.INFO)
    
    def _calculate_impact_score(self, result: Dict[str, Any]) -> float:
        """计算影响分数"""
        impact_score = 1.0
        
        # 根据影响范围调整
        impact_scope = result.get('impact_scope', 'single')
        if impact_scope == 'multiple':
            impact_score = 2.0
        elif impact_scope == 'system':
            impact_score = 3.0
        
        # 根据业务影响调整
        business_impact = result.get('business_impact', 'low')
        if business_impact == 'high':
            impact_score *= 1.5
        elif business_impact == 'critical':
            impact_score *= 2.0
        
        return impact_score
    
    def _calculate_exploitability_score(self, result: Dict[str, Any]) -> float:
        """计算可利用性分数"""
        exploitability_score = 1.0
        
        # 根据攻击复杂度调整
        attack_complexity = result.get('attack_complexity', 'medium')
        if attack_complexity == 'low':
            exploitability_score = 2.0
        elif attack_complexity == 'high':
            exploitability_score = 0.5
        
        # 根据权限要求调整
        privileges_required = result.get('privileges_required', 'none')
        if privileges_required == 'low':
            exploitability_score *= 1.5
        elif privileges_required == 'high':
            exploitability_score *= 0.7
        
        return exploitability_score
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """确定风险等级"""
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.MEDIUM
        elif risk_score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFO
    
    def _generate_recommendations(self, risk_factors: List[RiskFactor]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        for factor in risk_factors:
            if factor.category == RiskCategory.SQL_INJECTION:
                recommendations.append("实施参数化查询，防止SQL注入攻击")
            elif factor.category == RiskCategory.XSS:
                recommendations.append("实施输入验证和输出编码，防止XSS攻击")
            elif factor.category == RiskCategory.CSRF:
                recommendations.append("实施CSRF令牌，防止跨站请求伪造")
            elif factor.category == RiskCategory.FILE_UPLOAD:
                recommendations.append("实施文件类型验证和病毒扫描")
            elif factor.category == RiskCategory.AUTHENTICATION:
                recommendations.append("实施多因素认证，加强身份验证")
            elif factor.category == RiskCategory.AUTHORIZATION:
                recommendations.append("实施最小权限原则，加强访问控制")
            elif factor.category == RiskCategory.CONFIGURATION:
                recommendations.append("检查和修复安全配置问题")
            elif factor.category == RiskCategory.INFORMATION_DISCLOSURE:
                recommendations.append("实施信息访问控制，防止信息泄露")
            elif factor.category == RiskCategory.BUSINESS_LOGIC:
                recommendations.append("实施业务逻辑验证，防止业务逻辑漏洞")
            elif factor.category == RiskCategory.DENIAL_OF_SERVICE:
                recommendations.append("实施速率限制和资源管理，防止拒绝服务攻击")
        
        # 去重
        return list(set(recommendations))
    
    def _identify_affected_components(self, scan_results: List[Dict[str, Any]]) -> List[str]:
        """确定受影响组件"""
        components = set()
        
        for result in scan_results:
            # 提取受影响的组件
            affected_components = result.get('affected_components', [])
            components.update(affected_components)
        
        return list(components)
    
    async def _save_risk_assessment(self, assessment: RiskAssessment, scan_id: int, db: Session):
        """保存风险评估结果"""
        try:
            # 将风险评估结果保存到数据库
            assessment_data = {
                'scan_id': scan_id,
                'risk_score': assessment.risk_score,
                'risk_level': assessment.risk_level.value,
                'risk_factors': [
                    {
                        'category': factor.category.value,
                        'severity': factor.severity.value,
                        'confidence': factor.confidence,
                        'description': factor.description,
                        'evidence': factor.evidence,
                        'impact_score': factor.impact_score,
                        'exploitability_score': factor.exploitability_score
                    }
                    for factor in assessment.risk_factors
                ],
                'recommendations': assessment.recommendations,
                'affected_components': assessment.affected_components,
                'assessment_timestamp': assessment.assessment_timestamp.isoformat(),
                'assessor_version': assessment.assessor_version
            }
            
            # 保存到缓存
            CacheManager.set(f"risk_assessment:{scan_id}", json.dumps(assessment_data))
            
            # 保存到数据库（如果需要）
            # 这里可以添加数据库保存逻辑
            
            logger.info(f"Risk assessment saved for scan {scan_id}")
            
        except Exception as e:
            logger.error(f"Failed to save risk assessment: {e}")
            raise


# 创建全局风险评估引擎实例
risk_assessment_engine = RiskAssessmentEngine()


def get_risk_assessment_engine() -> RiskAssessmentEngine:
    """获取风险评估引擎实例"""
    return risk_assessment_engine