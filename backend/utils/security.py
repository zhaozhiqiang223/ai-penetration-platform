import re
import hashlib
import secrets
import string
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """验证URL格式"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def validate_ip(ip: str) -> bool:
    """验证IP地址格式"""
    try:
        # 检查IPv4
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        # 检查IPv6
        elif re.match(r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$', ip):
            return True
        return False
    except ValueError:
        return False


def validate_port(port: int) -> bool:
    """验证端口号"""
    return 1 <= port <= 65535


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    # 支持国际号码格式
    pattern = r'^\+?[\d\s\-\(\)]+$'
    return re.match(pattern, phone) is not None and len(phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 7


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """清理输入字符串，防止XSS和注入攻击"""
    if not input_str:
        return ""
    
    # 限制长度
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # 移除潜在的恶意字符
    input_str = re.sub(r'<script[^>]*?>.*?</script>', '', input_str, flags=re.IGNORECASE)
    input_str = re.sub(r'javascript:', '', input_str, flags=re.IGNORECASE)
    input_str = re.sub(r'on\w+\s*=', '', input_str, flags=re.IGNORECASE)
    
    # HTML实体编码
    input_str = input_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
    
    return input_str


def check_password_strength(password: str) -> Dict[str, Any]:
    """检查密码强度"""
    result = {
        "is_strong": False,
        "score": 0,
        "checks": {
            "length": len(password) >= 8,
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password),
            "number": any(c.isdigit() for c in password),
            "special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?`~" for c in password),
            "no_repeating": len(set(password)) >= 6,
            "no_common": not is_common_password(password)
        }
    }
    
    # 计算分数
    score = 0
    if result["checks"]["length"]:
        score += 20
    if result["checks"]["uppercase"]:
        score += 20
    if result["checks"]["lowercase"]:
        score += 20
    if result["checks"]["number"]:
        score += 15
    if result["checks"]["special"]:
        score += 15
    if result["checks"]["no_repeating"]:
        score += 5
    if result["checks"]["no_common"]:
        score += 5
    
    result["score"] = score
    result["is_strong"] = score >= 80
    
    return result


def is_common_password(password: str) -> bool:
    """检查是否是常见密码"""
    common_passwords = [
        "password", "123456", "12345678", "123456789", "12345",
        "qwerty", "abc123", "letmein", "monkey", "password1",
        "admin", "welcome", "login", "user", "root", "guest"
    ]
    return password.lower() in common_passwords


def generate_uuid() -> str:
    """生成UUID"""
    return secrets.token_hex(16)


def calculate_hash(data: str, algorithm: str = "sha256") -> str:
    """计算哈希值"""
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(data.encode('utf-8'))
    return hash_func.hexdigest()


def generate_salt(length: int = 32) -> str:
    """生成随机盐值"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    """密码哈希"""
    if salt is None:
        salt = generate_salt()
    
    # 使用PBKDF2进行密码哈希
    iterations = 100000
    key_length = 32
    
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations,
        key_length
    )
    
    return {
        "hash": dk.hex(),
        "salt": salt,
        "iterations": iterations
    }


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """验证密码"""
    hashed_input = hash_password(password, salt)["hash"]
    return hashed_input == hashed_password


def encrypt_data(data: str, key: str) -> str:
    """简单的数据加密"""
    # 这里使用简单的XOR加密，实际项目中应该使用更强大的加密算法
    encrypted = []
    for i, char in enumerate(data):
        key_char = key[i % len(key)]
        encrypted_char = chr(ord(char) ^ ord(key_char))
        encrypted.append(encrypted_char)
    return ''.join(encrypted)


def decrypt_data(encrypted_data: str, key: str) -> str:
    """简单的数据解密"""
    # XOR解密与加密相同
    return encrypt_data(encrypted_data, key)


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """验证文件扩展名"""
    import os
    _, ext = os.path.splitext(filename)
    return ext.lower() in [e.lower() for e in allowed_extensions]


def sanitize_filename(filename: str) -> str:
    """清理文件名"""
    # 移除或替换不安全的字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename


def validate_sql_query(query: str) -> bool:
    """验证SQL查询，防止SQL注入"""
    # 检查危险的SQL关键字
    dangerous_keywords = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 
        'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE', 'UNION',
        'SELECT', 'FROM', 'WHERE', 'OR', 'AND'
    ]
    
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return False
    
    return True


def validate_json_string(json_str: str) -> bool:
    """验证JSON字符串格式"""
    try:
        import json
        json.loads(json_str)
        return True
    except (ValueError, TypeError):
        return False


def sanitize_html(html: str) -> str:
    """清理HTML内容"""
    import html
    return html.escape(html)


def validate_http_method(method: str) -> bool:
    """验证HTTP方法"""
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE']
    return method.upper() in valid_methods


def validate_http_status_code(status_code: int) -> bool:
    """验证HTTP状态码"""
    return 100 <= status_code <= 599


def validate_content_type(content_type: str) -> bool:
    """验证Content-Type"""
    valid_types = [
        'application/json', 'application/xml', 'text/html', 
        'text/plain', 'multipart/form-data', 'application/x-www-form-urlencoded'
    ]
    return content_type.lower() in [t.lower() for t in valid_types]