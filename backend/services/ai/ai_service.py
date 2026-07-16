import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
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
from models.scan import Scan, ScanType, ScanStatus, ScanResult, ScanSeverity, ScanResultCreate
from models.knowledge import Vulnerability, VulnerabilityType, VulnerabilitySeverity
from utils.security import validate_url, validate_ip, sanitize_input
from .risk_assessment import RiskAssessmentEngine, RiskAssessment

logger = logging.getLogger(__name__)


class AIScanner:
    """AI扫描器核心类"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.vulnerability_detector = None
        self.classifier = None
        self.risk_assessment_engine = RiskAssessmentEngine()
        self.http_client = httpx.AsyncClient(timeout=30)
        
        # 初始化AI模型
        self._initialize_models()
        
    def _initialize_models(self):
        """初始化AI模型"""
        try:
            # 加载预训练模型
            logger.info("Initializing AI models...")
            
            # 文本分类模型（用于漏洞检测）
            self.classifier = pipeline(
                "text-classification",
                model="distilbert-base-uncased",
                device=0 if torch.cuda.is_available() else -1
            )
            
            # 漏洞检测模型
            self.vulnerability_detector = VulnerabilityDetector()
            
            # 加载自定义模型（如果存在）
            self._load_custom_models()
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            # 使用备用方案
            self._initialize_fallback_models()
    
    def _load_custom_models(self):
        """加载自定义训练的模型"""
        try:
            # 这里可以加载自定义训练的漏洞检测模型
            # model_path = "./models/vulnerability_detector.h5"
            # if os.path.exists(model_path):
            #     self.model = tf.keras.models.load_model(model_path)
            pass
        except Exception as e:
            logger.error(f"Failed to load custom models: {e}")
    
    def _initialize_fallback_models(self):
        """初始化备用模型"""
        logger.info("Initializing fallback models...")
        
        # 使用规则基础的检测器
        self.vulnerability_detector = RuleBasedDetector()
        
        # 使用简单的文本分类
        self.classifier = SimpleClassifier()
    
    async def scan_target(self, scan_id: int, target: Target, db: Session) -> List[ScanResult]:
        """扫描目标"""
        try:
            logger.info(f"Starting AI scan for target {target.id}: {target.name}")
            
            # 根据目标类型选择扫描策略
            if target.target_type == TargetType.WEB:
                results = await self._scan_web_target(scan_id, target, db)
            elif target.target_type == TargetType.NETWORK:
                results = await self._scan_network_target(scan_id, target, db)
            elif target.target_type == TargetType.SYSTEM:
                results = await self._scan_system_target(scan_id, target, db)
            else:
                raise ValueError(f"Unsupported target type: {target.target_type}")
            
            # 更新扫描进度
            await self._update_scan_progress(scan_id, len(results), db)
            
            logger.info(f"AI scan completed for target {target.id}: {len(results)} findings")
            
            # 执行风险评估
            await self._perform_risk_assessment(scan_id, target, results, db)
            
            return results
            
        except Exception as e:
            logger.error(f"AI scan failed for target {target.id}: {e}")
            raise
    
    async def _scan_web_target(self, scan_id: int, target: Target, db: Session) -> List[ScanResult]:
        """扫描Web目标"""
        results = []
        
        try:
            # 1. 信息收集
            info_results = await self._web_information_gathering(target, db)
            results.extend(info_results)
            
            # 2. 漏洞扫描
            vulnerability_results = await self._web_vulnerability_scan(target, db)
            results.extend(vulnerability_results)
            
            # 3. 安全配置检查
            config_results = await self._web_security_config_scan(target, db)
            results.extend(config_results)
            
            # 4. 业务逻辑测试
            business_results = await self._web_business_logic_scan(target, db)
            results.extend(business_results)
            
        except Exception as e:
            logger.error(f"Web scan failed: {e}")
            # 添加错误报告
            error_result = ScanResult(
                scan_id=scan_id,
                finding_type="scan_error",
                title="Web Scan Error",
                description=f"Failed to scan web target: {str(e)}",
                severity=ScanSeverity.HIGH,
                confidence=90,
                location=target.target_url,
                metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
            results.append(error_result)
        
        return results
    
    async def _scan_network_target(self, scan_id: int, target: Target, db: Session) -> List[ScanResult]:
        """扫描网络目标"""
        results = []
        
        try:
            # 1. 端口扫描
            port_results = await self._network_port_scan(target, db)
            results.extend(port_results)
            
            # 2. 服务识别
            service_results = await self._network_service_identification(target, db)
            results.extend(service_results)
            
            # 3. 漏洞扫描
            vulnerability_results = await self._network_vulnerability_scan(target, db)
            results.extend(vulnerability_results)
            
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            # 添加错误报告
            error_result = ScanResult(
                scan_id=scan_id,
                finding_type="scan_error",
                title="Network Scan Error",
                description=f"Failed to scan network target: {str(e)}",
                severity=ScanSeverity.HIGH,
                confidence=90,
                location=target.target_ip,
                metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
            results.append(error_result)
        
        return results
    
    async def _scan_system_target(self, scan_id: int, target: Target, db: Session) -> List[ScanResult]:
        """扫描系统目标"""
        results = []
        
        try:
            # 1. 系统信息收集
            info_results = await self._system_information_gathering(target, db)
            results.extend(info_results)
            
            # 2. 配置检查
            config_results = await self._system_config_check(target, db)
            results.extend(config_results)
            
            # 3. 权限检查
            permission_results = await self._system_permission_check(target, db)
            results.extend(permission_results)
            
        except Exception as e:
            logger.error(f"System scan failed: {e}")
            # 添加错误报告
            error_result = ScanResult(
                scan_id=scan_id,
                finding_type="scan_error",
                title="System Scan Error",
                description=f"Failed to scan system target: {str(e)}",
                severity=ScanSeverity.HIGH,
                confidence=90,
                location=target.target_ip,
                metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
            results.append(error_result)
        
        return results
    
    async def _web_information_gathering(self, target: Target, db: Session) -> List[ScanResult]:
        """Web信息收集"""
        results = []
        
        try:
            # 获取主页信息
            response = await self.http_client.get(target.target_url, timeout=10)
            
            # 分析响应
            analysis = await self._analyze_web_response(response, target)
            
            # 检测技术栈
            tech_stack_results = await self._detect_technology_stack(response, target)
            results.extend(tech_stack_results)
            
            # 检查目录列表
            dir_results = await self._check_directory_listing(response, target)
            results.extend(dir_results)
            
            # 检查敏感信息泄露
            info_leak_results = await self._check_information_leakage(response, target)
            results.extend(info_leak_results)
            
        except Exception as e:
            logger.error(f"Web information gathering failed: {e}")
        
        return results
    
    async def _analyze_web_response(self, response, target: Target) -> Dict[str, Any]:
        """分析Web响应"""
        analysis = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": response.headers.get("content-type", ""),
            "server": response.headers.get("server", ""),
            "content_length": len(response.content),
            "response_time": response.elapsed.total_seconds()
        }
        
        # 使用AI分析响应内容
        try:
            content_text = response.text[:1000]  # 限制长度避免内存问题
            ai_analysis = await self._ai_analyze_content(content_text)
            analysis.update(ai_analysis)
        except Exception as e:
            logger.error(f"AI content analysis failed: {e}")
        
        return analysis
    
    async def _ai_analyze_content(self, content: str) -> Dict[str, Any]:
        """AI分析内容"""
        try:
            # 使用文本分类器分析内容
            classification = self.classifier(content)
            
            # 提取关键信息
            analysis = {
                "ai_classification": classification,
                "suspicious_keywords": self._detect_suspicious_keywords(content),
                "security_indicators": self._detect_security_indicators(content)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI content analysis failed: {e}")
            return {}
    
    def _detect_suspicious_keywords(self, content: str) -> List[str]:
        """检测可疑关键词"""
        suspicious_patterns = [
            r'password\s*=\s*[\'"][^\'"]*[\'"]',
            r'api_key\s*=\s*[\'"][^\'"]*[\'"]',
            r'secret\s*=\s*[\'"][^\'"]*[\'"]',
            r'token\s*=\s*[\'"][^\'"]*[\'"]',
            r'private_key\s*=\s*[\'"][^\'"]*[\'"]',
            r'connection\s*string\s*=\s*[\'"][^\'"]*[\'"]',
            r'database\s*password\s*=\s*[\'"][^\'"]*[\'"]',
            r'admin\s*password\s*=\s*[\'"][^\'"]*[\'"]'
        ]
        
        found_keywords = []
        for pattern in suspicious_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_keywords.extend(matches)
        
        return found_keywords
    
    def _detect_security_indicators(self, content: str) -> List[str]:
        """检测安全指标"""
        indicators = []
        
        # 检查错误信息
        if "error" in content.lower() and "traceback" in content.lower():
            indicators.append("Error traceback detected")
        
        # 检查调试信息
        if "debug" in content.lower() or "development" in content.lower():
            indicators.append("Debug mode detected")
        
        # 检查版本信息
        version_patterns = [
            r'version\s*[:=]\s*[\d.]+',
            r'powered\s*by\s*[\w\s]+[\d.]+',
            r'apache/[\d.]+',
            r'nginx/[\d.]+',
            r'microsoft-iis/[\d.]+'
        ]
        
        for pattern in version_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                indicators.extend(matches)
        
        return indicators
    
    async def _detect_technology_stack(self, response, target: Target) -> List[ScanResult]:
        """检测技术栈"""
        results = []
        
        try:
            headers = response.headers
            content = response.text
            
            # 检测服务器信息
            server = headers.get("server", "").lower()
            if "apache" in server:
                results.append(self._create_result(
                    "technology_detection",
                    "Apache Server Detected",
                    f"Apache web server detected: {server}",
                    ScanSeverity.INFO,
                    target.target_url,
                    metadata={"server": server}
                ))
            
            # 检测框架
            frameworks = []
            if "django" in content.lower():
                frameworks.append("Django")
            if "flask" in content.lower():
                frameworks.append("Flask")
            if "spring" in content.lower():
                frameworks.append("Spring")
            if "asp.net" in content.lower():
                frameworks.append("ASP.NET")
            
            for framework in frameworks:
                results.append(self._create_result(
                    "technology_detection",
                    f"{framework} Framework Detected",
                    f"{framework} framework detected in the application",
                    ScanSeverity.INFO,
                    target.target_url,
                    metadata={"framework": framework}
                ))
            
            # 检测数据库
            databases = []
            if "mysql" in content.lower():
                databases.append("MySQL")
            if "postgresql" in content.lower():
                databases.append("PostgreSQL")
            if "mongodb" in content.lower():
                databases.append("MongoDB")
            if "redis" in content.lower():
                databases.append("Redis")
            
            for db in databases:
                results.append(self._create_result(
                    "technology_detection",
                    f"{db} Database Detected",
                    f"{db} database detected in the application",
                    ScanSeverity.INFO,
                    target.target_url,
                    metadata={"database": db}
                ))
            
        except Exception as e:
            logger.error(f"Technology stack detection failed: {e}")
        
        return results
    
    async def _check_directory_listing(self, response, target: Target) -> List[ScanResult]:
        """检查目录列表"""
        results = []
        
        try:
            # 检查是否是目录列表
            if "Index of" in response.text or "Directory Listing" in response.text:
                results.append(self._create_result(
                    "directory_listing",
                    "Directory Listing Enabled",
                    "Directory listing is enabled, which may expose sensitive information",
                    ScanSeverity.MEDIUM,
                    target.target_url,
                    recommendation="Disable directory listing in web server configuration",
                    affected_components=["Web Server"]
                ))
            
        except Exception as e:
            logger.error(f"Directory listing check failed: {e}")
        
        return results
    
    async def _check_information_leakage(self, response, target: Target) -> List[ScanResult]:
        """检查信息泄露"""
        results = []
        
        try:
            content = response.text
            
            # 检查敏感信息
            sensitive_patterns = [
                r'password\s*[=:]\s*[\'"][^\'"]*[\'"]',
                r'api_key\s*[=:]\s*[\'"][^\'"]*[\'"]',
                r'secret\s*[=:]\s*[\'"][^\'"]*[\'"]',
                r'token\s*[=:]\s*[\'"][^\'"]*[\'"]',
                r'private_key\s*[=:]\s*[\'"][^\'"]*[\'"]',
                r'connection\s*string\s*[=:]\s*[\'"][^\'"]*[\'"]',
                r'database\s*password\s*[=:]\s*[\'"][^\'"]*[\'"]'
            ]
            
            for pattern in sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    results.append(self._create_result(
                        "information_leakage",
                        "Sensitive Information Detected",
                        f"Sensitive information found: {', '.join(matches[:3])}",
                        ScanSeverity.CRITICAL,
                        target.target_url,
                        recommendation="Remove sensitive information from source code",
                        proof_of_concept="\n".join(matches[:3]),
                        affected_components=["Application Code"]
                    ))
            
            # 检查注释中的信息
            comment_patterns = [
                r'<!--.*?-->',
                r'/\*.*?\*/',
                r'//.*?$',
                r'#.*?$'
            ]
            
            for pattern in comment_patterns:
                comments = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                for comment in comments:
                    if any(keyword in comment.lower() for keyword in ["password", "key", "secret", "token"]):
                        results.append(self._create_result(
                            "information_leakage",
                            "Comment Information Leakage",
                            "Sensitive information found in comments",
                            ScanSeverity.MEDIUM,
                            target.target_url,
                            recommendation="Remove sensitive information from comments",
                            proof_of_concept=comment,
                            affected_components=["Source Code"]
                        ))
                        break
            
        except Exception as e:
            logger.error(f"Information leakage check failed: {e}")
        
        return results
    
    def _create_result(self, finding_type: str, title: str, description: str, 
                      severity: ScanSeverity, location: str, **kwargs) -> ScanResult:
        """创建扫描结果"""
        return ScanResult(
            scan_id=kwargs.get("scan_id", 0),
            finding_type=finding_type,
            title=title,
            description=description,
            severity=severity,
            confidence=kwargs.get("confidence", 85),
            location=location,
            recommendation=kwargs.get("recommendation"),
            proof_of_concept=kwargs.get("proof_of_concept"),
            affected_components=kwargs.get("affected_components", []),
            metadata=kwargs.get("metadata", {})
        )
    
    async def _web_vulnerability_scan(self, target: Target, db: Session) -> List[ScanResult]:
        """Web漏洞扫描"""
        results = []
        
        try:
            # SQL注入检测
            sql_injection_results = await self._detect_sql_injection(target, db)
            results.extend(sql_injection_results)
            
            # XSS检测
            xss_results = await self._detect_xss(target, db)
            results.extend(xss_results)
            
            # CSRF检测
            csrf_results = await self._detect_csrf(target, db)
            results.extend(csrf_results)
            
            # 文件上传漏洞检测
            upload_results = await self._detect_file_upload_vulnerabilities(target, db)
            results.extend(upload_results)
            
            # 认证绕过检测
            auth_results = await self._detect_authentication_bypass(target, db)
            results.extend(auth_results)
            
        except Exception as e:
            logger.error(f"Web vulnerability scan failed: {e}")
        
        return results
    
    async def _detect_sql_injection(self, target: Target, db: Session) -> List[ScanResult]:
        """检测SQL注入"""
        results = []
        
        try:
            # 常见的SQL注入测试 payload
            sql_payloads = [
                "' OR '1'='1",
                "' OR 1=1--",
                "' OR 1=1#",
                "' UNION SELECT NULL--",
                "' AND 1=1--",
                "' DROP TABLE users--"
            ]
            
            # 测试常见参数
            test_params = ["id", "user", "username", "email", "search", "query"]
            
            for param in test_params:
                for payload in sql_payloads:
                    test_url = f"{target.target_url}?{param}={payload}"
                    
                    try:
                        response = await self.http_client.get(test_url, timeout=10)
                        
                        # 检查响应中是否有SQL错误
                        sql_errors = [
                            "sql syntax error",
                            "mysql_fetch_array",
                            "mysql_num_rows",
                            "you have an error in your sql syntax",
                            "unclosed quotation mark",
                            "sql server",
                            "postgresql query failed",
                            "ora-00933",
                            "sqlite3.operationalerror"
                        ]
                        
                        for error in sql_errors:
                            if error.lower() in response.text.lower():
                                results.append(self._create_result(
                                    "sql_injection",
                                    "SQL Injection Detected",
                                    f"SQL injection vulnerability detected in parameter '{param}'",
                                    ScanSeverity.CRITICAL,
                                    target.target_url,
                                    location=test_url,
                                    parameter=param,
                                    recommendation="Use parameterized queries and input validation",
                                    proof_of_concept=f"Payload: {payload}\nResponse: {response.text[:200]}",
                                    affected_components=["Database", "Application"]
                                ))
                                break
                    
                    except Exception as e:
                        logger.debug(f"SQL injection test failed for {test_url}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"SQL injection detection failed: {e}")
        
        return results
    
    async def _detect_xss(self, target: Target, db: Session) -> List[ScanResult]:
        """检测XSS"""
        results = []
        
        try:
            # XSS payload
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "<iframe src=javascript:alert('XSS')>",
                "<body onload=alert('XSS')>",
                "<input onfocus=alert('XSS') autofocus>"
            ]
            
            # 测试参数
            test_params = ["search", "query", "id", "user", "name", "email"]
            
            for param in test_params:
                for payload in xss_payloads:
                    test_url = f"{target.target_url}?{param}={payload}"
                    
                    try:
                        response = await self.http_client.get(test_url, timeout=10)
                        
                        # 检查响应中是否包含payload
                        if payload.lower() in response.text.lower():
                            results.append(self._create_result(
                                "xss",
                                "XSS Vulnerability Detected",
                                f"Cross-site scripting vulnerability detected in parameter '{param}'",
                                ScanSeverity.HIGH,
                                target.target_url,
                                location=test_url,
                                parameter=param,
                                recommendation="Implement input validation and output encoding",
                                proof_of_concept=f"Payload: {payload}\nResponse: {response.text[:200]}",
                                affected_components=["Web Application"]
                            ))
                            break
                    
                    except Exception as e:
                        logger.debug(f"XSS test failed for {test_url}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"XSS detection failed: {e}")
        
        return results
    
    async def _detect_csrf(self, target: Target, db: Session) -> List[ScanResult]:
        """检测CSRF"""
        results = []
        
        try:
            # 检查是否有CSRF保护
            response = await self.http_client.get(target.target_url, timeout=10)
            
            # 检查CSRF token
            csrf_patterns = [
                r'name="csrf_token"[^>]*value="[^"]*"',
                r'name="csrfmiddlewaretoken"[^>]*value="[^"]*"',
                r'name="_token"[^>]*value="[^"]*"',
                r'csrf-token[^>]*content="[^"]*"',
                r'X-CSRF-Token[^>]*[^"]*"'
            ]
            
            csrf_found = False
            for pattern in csrf_patterns:
                if re.search(pattern, response.text, re.IGNORECASE):
                    csrf_found = True
                    break
            
            if not csrf_found:
                results.append(self._create_result(
                    "csrf",
                    "CSRF Protection Missing",
                    "Cross-Site Request Forgery protection is not implemented",
                    ScanSeverity.MEDIUM,
                    target.target_url,
                    recommendation="Implement CSRF tokens and same-site cookie attributes",
                    affected_components=["Web Application"]
                ))
        
        except Exception as e:
            logger.error(f"CSRF detection failed: {e}")
        
        return results
    
    async def _detect_file_upload_vulnerabilities(self, target: Target, db: Session) -> List[ScanResult]:
        """检测文件上传漏洞"""
        results = []
        
        try:
            # 查找文件上传表单
            upload_forms = await self._find_upload_forms(target, db)
            
            for form_url in upload_forms:
                # 测试文件上传
                upload_results = await self._test_file_upload(target, form_url, db)
                results.extend(upload_results)
        
        except Exception as e:
            logger.error(f"File upload vulnerability detection failed: {e}")
        
        return results
    
    async def _find_upload_forms(self, target: Target, db: Session) -> List[str]:
        """查找文件上传表单"""
        forms = []
        
        try:
            response = await self.http_client.get(target.target_url, timeout=10)
            
            # 查找文件上传表单
            form_pattern = r'<form[^>]*action="([^"]*)"[^>]*method="post"[^>]*>.*?</form>'
            forms_found = re.findall(form_pattern, response.text, re.IGNORECASE | re.DOTALL)
            
            for form_action in forms_found:
                if form_action.startswith('/'):
                    form_url = urljoin(target.target_url, form_action)
                else:
                    form_url = form_action
                
                # 检查是否有文件上传字段
                if 'type="file"' in response.text:
                    forms.append(form_url)
        
        except Exception as e:
            logger.error(f"Failed to find upload forms: {e}")
        
        return forms
    
    async def _test_file_upload(self, target: Target, form_url: str, db: Session) -> List[ScanResult]:
        """测试文件上传"""
        results = []
        
        try:
            # 创建测试文件
            test_files = [
                ("test.php", "<?php phpinfo(); ?>", "application/x-php"),
                ("test.jsp", "<%@ page import=\"java.util.*\" %><%= request.getParameter(\"cmd\") %>", "application/x-jsp"),
                ("test.aspx", "<%@ Page Language=\"C#\" %><%= Request[\"cmd\"] %>", "application/x-aspx"),
                ("test.html", "<script>alert('XSS')</script>", "text/html")
            ]
            
            for filename, content, content_type in test_files:
                files = {"file": (filename, content, content_type)}
                
                try:
                    response = await self.http_client.post(form_url, files=files, timeout=10)
                    
                    # 检查文件是否被上传
                    if filename in response.text or "test.php" in response.text:
                        results.append(self._create_result(
                            "file_upload",
                            "Arbitrary File Upload Detected",
                            f"Arbitrary file upload vulnerability detected in form: {form_url}",
                            ScanSeverity.CRITICAL,
                            target.target_url,
                            location=form_url,
                            recommendation="Implement file type validation and secure file storage",
                            proof_of_concept=f"Uploaded file: {filename}\nResponse: {response.text[:200]}",
                            affected_components=["File Upload System"]
                        ))
                        break
                
                except Exception as e:
                    logger.debug(f"File upload test failed for {filename}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"File upload test failed: {e}")
        
        return results
    
    async def _detect_authentication_bypass(self, target: Target, db: Session) -> List[ScanResult]:
        """检测认证绕过"""
        results = []
        
        try:
            # 测试常见的认证绕过
            bypass_payloads = [
                "' OR '1'='1' --",
                "' OR 1=1 --",
                "' OR 'a'='a' --",
                "' OR 'admin'='admin' --",
                "' OR 'user'='user' --",
                "' OR 'password'='password' --"
            ]
            
            # 测试登录页面
            login_urls = [
                f"{target.target_url}/login",
                f"{target.target_url}/signin",
                f"{target.target_url}/auth",
                f"{target.target_url}/admin",
                f"{target.target_url}/wp-admin"
            ]
            
            for login_url in login_urls:
                try:
                    response = await self.http_client.get(login_url, timeout=10)
                    
                    # 检查是否是登录页面
                    if "login" in response.text.lower() or "signin" in response.text.lower():
                        # 测试认证绕过
                        for payload in bypass_payloads:
                            test_data = {
                                "username": payload,
                                "password": payload
                            }
                            
                            try:
                                bypass_response = await self.http_client.post(login_url, data=test_data, timeout=10)
                                
                                # 检查是否绕过成功
                                if "dashboard" in bypass_response.text.lower() or "admin" in bypass_response.text.lower():
                                    results.append(self._create_result(
                                        "authentication_bypass",
                                        "Authentication Bypass Detected",
                                        f"Authentication bypass vulnerability detected in login form",
                                        ScanSeverity.CRITICAL,
                                        target.target_url,
                                        location=login_url,
                                        recommendation="Implement proper input validation and authentication checks",
                                        proof_of_concept=f"Payload: {payload}\nResponse: {bypass_response.text[:200]}",
                                        affected_components=["Authentication System"]
                                    ))
                                    break
                            
                            except Exception as e:
                                logger.debug(f"Authentication bypass test failed: {e}")
                                continue
                
                except Exception as e:
                    logger.debug(f"Login page test failed: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Authentication bypass detection failed: {e}")
        
        return results
    
    async def _update_scan_progress(self, scan_id: int, findings_count: int, db: Session):
        """更新扫描进度"""
        try:
            from models.scan import ScanProgressUpdate
            
            # 这里应该实现进度更新逻辑
            # TaskManager.update_task_status(f"scan_{scan_id}", "completed")
            
            logger.info(f"Scan progress updated: scan_id={scan_id}, findings={findings_count}")
            
        except Exception as e:
            logger.error(f"Failed to update scan progress: {e}")


class VulnerabilityDetector:
    """漏洞检测器"""
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
    
    def _load_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """加载漏洞模式"""
        return {
            "sql_injection": [
                r"union\s+select",
                r"or\s+1\s*=\s*1",
                r"drop\s+table",
                r"insert\s+into",
                r"update\s+set",
                r"delete\s+from",
                r"exec\s*\(",
                r"execute\s*\(",
                r"xp_cmdshell",
                r"load_file\s*\(",
                r"into\s+outfile",
                r"into\s+dumpfile"
            ],
            "xss": [
                r"<script[^>]*>.*?</script>",
                r"onload\s*=",
                r"onerror\s*=",
                r"onclick\s*=",
                r"onmouseover\s*=",
                r"javascript:",
                r"vbscript:",
                r"data:text/html",
                r"<iframe[^>]*>",
                r"<img[^>]*onerror[^>]*>",
                r"<svg[^>]*onload[^>]*>"
            ],
            "csrf": [
                r"csrf_token",
                r"csrfmiddlewaretoken",
                r"_token",
                r"x-csrf-token",
                r"anti-csrf"
            ],
            "file_upload": [
                r"\.php",
                r"\.jsp",
                r"\.asp",
                r"\.aspx",
                r"\.exe",
                r"\.bat",
                r"\.sh",
                r"\.py",
                r"\.rb",
                r"\.pl"
            ]
        }
    
    def detect_vulnerabilities(self, content: str, content_type: str = "text") -> List[Dict[str, Any]]:
        """检测漏洞"""
        findings = []
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    findings.append({
                        "type": vuln_type,
                        "pattern": pattern,
                        "matches": matches,
                        "confidence": len(matches) * 10
                    })
        
        return findings


class RuleBasedDetector:
    """基于规则的检测器"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """加载检测规则"""
        return [
            {
                "name": "SQL Injection Detection",
                "pattern": r"(union\s+select|or\s+1\s*=\s*1|drop\s+table)",
                "severity": "critical",
                "confidence": 90
            },
            {
                "name": "XSS Detection",
                "pattern": r"(<script[^>]*>.*?</script>|onload\s*=|javascript:)",
                "severity": "high",
                "confidence": 85
            },
            {
                "name": "Path Traversal Detection",
                "pattern": r"(\.\.\/|\.\.\\\)",
                "severity": "high",
                "confidence": 80
            },
            {
                "name": "Command Injection Detection",
                "pattern": r"(;|\||`|\$\(|\${)",
                "severity": "critical",
                "confidence": 90
            }
        ]
    
    def detect(self, content: str) -> List[Dict[str, Any]]:
        """基于规则检测"""
        findings = []
        
        for rule in self.rules:
            matches = re.findall(rule["pattern"], content, re.IGNORECASE)
            if matches:
                findings.append({
                    "rule_name": rule["name"],
                    "pattern": rule["pattern"],
                    "matches": matches,
                    "severity": rule["severity"],
                    "confidence": rule["confidence"]
                })
        
        return findings


class SimpleClassifier:
    """简单的文本分类器"""
    
    def __init__(self):
        self.classification_rules = {
            "security": [
                r"error", "exception", "warning", "critical", "fatal",
                "vulnerability", "exploit", "attack", "breach", "compromise"
            ],
            "normal": [
                "welcome", "hello", "success", "ok", "done", "complete"
            ]
        }
    
    def __call__(self, text: str) -> Dict[str, Any]:
        """分类文本"""
        scores = {}
        
        for category, keywords in self.classification_rules.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text.lower())
            scores[category] = score
        
        # 返回最高分的分类
        if scores:
            predicted_category = max(scores, key=scores.get)
            confidence = scores[predicted_category] / len(text.split()) * 100
            
            return {
                "label": predicted_category,
                "score": confidence,
                "confidence": confidence
            }
        
        return {
            "label": "unknown",
            "score": 0,
            "confidence": 0
        }