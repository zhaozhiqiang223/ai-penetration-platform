import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from services.ai.risk_assessment import (
    RiskLevel, RiskCategory, RiskFactor, RiskAssessment,
    RiskMatrix, RiskScoringModel, RiskAssessmentEngine
)
from models.target import Target, TargetType, TargetStatus
from models.scan import Scan, ScanType, ScanStatus, ScanResult


class TestRiskLevel:
    """测试风险等级枚举"""
    
    def test_risk_level_values(self):
        """测试风险等级值"""
        assert RiskLevel.CRITICAL == "critical"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.LOW == "low"
        assert RiskLevel.INFO == "info"


class TestRiskCategory:
    """测试风险类别枚举"""
    
    def test_risk_category_values(self):
        """测试风险类别值"""
        assert RiskCategory.SQL_INJECTION == "sql_injection"
        assert RiskCategory.XSS == "xss"
        assert RiskCategory.CSRF == "csrf"
        assert RiskCategory.FILE_UPLOAD == "file_upload"
        assert RiskCategory.AUTHENTICATION == "authentication"
        assert RiskCategory.AUTHORIZATION == "authorization"
        assert RiskCategory.CONFIGURATION == "configuration"
        assert RiskCategory.INFORMATION_DISCLOSURE == "information_disclosure"
        assert RiskCategory.BUSINESS_LOGIC == "business_logic"
        assert RiskCategory.DENIAL_OF_SERVICE == "denial_of_service"


class TestRiskFactor:
    """测试风险因素"""
    
    def test_risk_factor_creation(self):
        """测试风险因素创建"""
        risk_factor = RiskFactor(
            category=RiskCategory.SQL_INJECTION,
            severity=RiskLevel.CRITICAL,
            confidence=0.9,
            description="SQL注入漏洞",
            evidence=["test evidence"],
            impact_score=8.0,
            exploitability_score=7.0
        )
        
        assert risk_factor.category == RiskCategory.SQL_INJECTION
        assert risk_factor.severity == RiskLevel.CRITICAL
        assert risk_factor.confidence == 0.9
        assert risk_factor.description == "SQL注入漏洞"
        assert risk_factor.evidence == ["test evidence"]
        assert risk_factor.impact_score == 8.0
        assert risk_factor.exploitability_score == 7.0


class TestRiskAssessment:
    """测试风险评估"""
    
    def test_risk_assessment_creation(self):
        """测试风险评估创建"""
        risk_factors = [
            RiskFactor(
                category=RiskCategory.SQL_INJECTION,
                severity=RiskLevel.CRITICAL,
                confidence=0.9,
                description="SQL注入漏洞",
                evidence=["test evidence"],
                impact_score=8.0,
                exploitability_score=7.0
            )
        ]
        
        assessment = RiskAssessment(
            risk_score=85.0,
            risk_level=RiskLevel.CRITICAL,
            risk_factors=risk_factors,
            recommendations=["立即修复SQL注入漏洞"],
            affected_components=["login page"],
            assessment_timestamp=datetime.utcnow(),
            assessor_version="1.0.0"
        )
        
        assert assessment.risk_score == 85.0
        assert assessment.risk_level == RiskLevel.CRITICAL
        assert len(assessment.risk_factors) == 1
        assert assessment.affected_components == ["login page"]
        assert assessment.assessor_version == "1.0.0"


class TestRiskMatrix:
    """测试风险矩阵"""
    
    def test_risk_matrix_initialization(self):
        """测试风险矩阵初始化"""
        risk_matrix = RiskMatrix()
        assert len(risk_matrix.matrix) > 0
        
        # 测试SQL注入风险值
        sql_injection_scores = risk_matrix.matrix.get("sql_injection", {})
        assert "critical" in sql_injection_scores
        assert sql_injection_scores["critical"] == 9.0
        
        # 测试XSS风险值
        xss_scores = risk_matrix.matrix.get("xss", {})
        assert "high" in xss_scores
        assert xss_scores["high"] == 7.0


class TestRiskScoringModel:
    """测试风险评分模型"""
    
    def test_risk_scoring_model_initialization(self):
        """测试风险评分模型初始化"""
        model = RiskScoringModel()
        # 模型可能为None（如果初始化失败）
        assert model is not None
    
    def test_calculate_risk_score_empty(self):
        """测试计算空风险分数"""
        model = RiskScoringModel()
        score = model.calculate_risk_score([])
        assert score == 0.0
    
    def test_calculate_risk_score_with_vulnerabilities(self):
        """测试计算有漏洞的风险分数"""
        model = RiskScoringModel()
        
        vulnerabilities = [
            {
                "type": "sql_injection",
                "severity": "critical",
                "confidence": 0.9,
                "count": 1,
                "exploitability": 1.0,
                "impact_scope": "single",
                "business_impact": "high"
            }
        ]
        
        score = model.calculate_risk_score(vulnerabilities)
        assert score > 0
        assert score <= 100
    
    def test_adjust_score_by_features(self):
        """测试根据特征调整分数"""
        model = RiskScoringModel()
        
        base_score = 8.0
        vuln = {
            "count": 2,
            "confidence": 0.8,
            "exploitability": 1.2
        }
        
        adjusted_score = model._adjust_score_by_features(base_score, vuln)
        assert adjusted_score > base_score  # 应该增加分数
    
    def test_calculate_impact_multiplier(self):
        """测试计算影响乘数"""
        model = RiskScoringModel()
        
        # 测试单个影响范围
        vuln = {"impact_scope": "single", "business_impact": "low"}
        multiplier = model._calculate_impact_multiplier(vuln)
        assert multiplier == 1.0
        
        # 测试多个影响范围
        vuln = {"impact_scope": "multiple", "business_impact": "high"}
        multiplier = model._calculate_impact_multiplier(vuln)
        assert multiplier > 1.0


class TestRiskAssessmentEngine:
    """测试风险评估引擎"""
    
    def test_risk_assessment_engine_initialization(self):
        """测试风险评估引擎初始化"""
        engine = RiskAssessmentEngine()
        assert engine is not None
        assert engine.risk_matrix is not None
        assert engine.scoring_model is not None
    
    def test_determine_risk_category(self):
        """测试确定风险类别"""
        engine = RiskAssessmentEngine()
        
        # 测试SQL注入
        category = engine._determine_risk_category("sql_injection")
        assert category == RiskCategory.SQL_INJECTION
        
        # 测试XSS
        category = engine._determine_risk_category("xss")
        assert category == RiskCategory.XSS
        
        # 测试未知类型
        category = engine._determine_risk_category("unknown")
        assert category == RiskCategory.INFORMATION_DISCLOSURE
    
    def test_map_severity_to_risk_level(self):
        """测试映射严重程度到风险等级"""
        engine = RiskAssessmentEngine()
        
        # 测试严重程度映射
        critical_level = engine._map_severity_to_risk_level("critical")
        assert critical_level == RiskLevel.CRITICAL
        
        high_level = engine._map_severity_to_risk_level("high")
        assert high_level == RiskLevel.HIGH
        
        medium_level = engine._map_severity_to_risk_level("medium")
        assert medium_level == RiskLevel.MEDIUM
        
        low_level = engine._map_severity_to_risk_level("low")
        assert low_level == RiskLevel.LOW
        
        info_level = engine._map_severity_to_risk_level("info")
        assert info_level == RiskLevel.INFO
    
    def test_determine_risk_level(self):
        """测试确定风险等级"""
        engine = RiskAssessmentEngine()
        
        # 测试不同风险分数对应的等级
        critical_level = engine._determine_risk_level(85)
        assert critical_level == RiskLevel.CRITICAL
        
        high_level = engine._determine_risk_level(65)
        assert high_level == RiskLevel.HIGH
        
        medium_level = engine._determine_risk_level(45)
        assert medium_level == RiskLevel.MEDIUM
        
        low_level = engine._determine_risk_level(25)
        assert low_level == RiskLevel.LOW
        
        info_level = engine._determine_risk_level(15)
        assert info_level == RiskLevel.INFO
    
    def test_generate_recommendations(self):
        """测试生成修复建议"""
        engine = RiskAssessmentEngine()
        
        # 测试严重风险因素
        risk_factors = [
            RiskFactor(
                category=RiskCategory.SQL_INJECTION,
                severity=RiskLevel.CRITICAL,
                confidence=0.9,
                description="SQL注入漏洞",
                evidence=["test evidence"],
                impact_score=8.0,
                exploitability_score=7.0
            )
        ]
        
        recommendations = engine._generate_recommendations(risk_factors)
        assert len(recommendations) > 0
        assert "立即修复" in recommendations[0]
        
        # 测试无风险因素
        empty_recommendations = engine._generate_recommendations([])
        assert len(empty_recommendations) == 1
        assert "未发现明显的安全风险" in empty_recommendations[0]
    
    def test_identify_affected_components(self):
        """测试识别受影响组件"""
        engine = RiskAssessmentEngine()
        
        scan_results = [
            {
                "endpoint": "/api/login",
                "component": "authentication",
                "service": "user-service"
            },
            {
                "endpoint": "/api/profile",
                "component": "profile",
                "service": "user-service"
            }
        ]
        
        components = engine._identify_affected_components(scan_results)
        assert len(components) == 3
        assert "/api/login" in components
        assert "authentication" in components
        assert "user-service" in components


if __name__ == "__main__":
    pytest.main([__file__, "-v"])