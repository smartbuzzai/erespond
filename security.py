"""
Security utilities for Email Automation System
"""

import hashlib
import hmac
import secrets
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)


class SecurityManager:
    """Centralized security management"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or self._generate_secret_key()
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.blocked_ips: set = set()
        self.allowed_ips: set = set()
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, hash_hex = hashed.split(':')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hmac.compare_digest(pwd_hash.hex(), hash_hex)
        except (ValueError, TypeError):
            return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    def generate_jwt_token(self, payload: Dict[str, Any], expires_in_hours: int = 24) -> str:
        """Generate JWT token"""
        payload['exp'] = datetime.utcnow() + timedelta(hours=expires_in_hours)
        payload['iat'] = datetime.utcnow()
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check if request is within rate limit"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        if identifier in self.rate_limits:
            self.rate_limits[identifier] = [
                req_time for req_time in self.rate_limits[identifier]
                if req_time > window_start
            ]
        else:
            self.rate_limits[identifier] = []
        
        # Check if under limit
        if len(self.rate_limits[identifier]) < max_requests:
            self.rate_limits[identifier].append(now)
            return True
        
        return False
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ips
    
    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if IP address is in allowed list"""
        if not self.allowed_ips:
            return True  # No restrictions if no allowed list
        return ip_address in self.allowed_ips
    
    def block_ip(self, ip_address: str):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        logger.warning(f"IP address blocked: {ip_address}")
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip_address)
        logger.info(f"IP address unblocked: {ip_address}")
    
    def add_allowed_ip(self, ip_address: str):
        """Add IP address to allowed list"""
        self.allowed_ips.add(ip_address)
        logger.info(f"IP address added to allowed list: {ip_address}")


class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_email_address(email: str) -> bool:
        """Validate email address format"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            'is_valid': True,
            'score': 0,
            'issues': []
        }
        
        if len(password) < 8:
            result['issues'].append("Password must be at least 8 characters long")
            result['is_valid'] = False
        
        if not re.search(r'[A-Z]', password):
            result['issues'].append("Password must contain at least one uppercase letter")
            result['score'] += 1
        
        if not re.search(r'[a-z]', password):
            result['issues'].append("Password must contain at least one lowercase letter")
            result['score'] += 1
        
        if not re.search(r'\d', password):
            result['issues'].append("Password must contain at least one digit")
            result['score'] += 1
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append("Password must contain at least one special character")
            result['score'] += 1
        
        # Check for common weak patterns
        weak_patterns = [
            r'password',
            r'123456',
            r'qwerty',
            r'admin',
            r'user'
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, password.lower()):
                result['issues'].append("Password contains common weak patterns")
                result['score'] -= 1
                break
        
        if result['score'] >= 3:
            result['is_valid'] = True
        
        return result
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_api_key_format(api_key: str, service: str) -> bool:
        """Validate API key format for different services"""
        if service.lower() == 'openai':
            return api_key.startswith('sk-') and len(api_key) > 20
        elif service.lower() == 'google':
            return len(api_key) > 20 and not api_key.startswith(' ')
        else:
            return len(api_key) > 10
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text.strip()
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, max_size: int = 10 * 1024 * 1024) -> Dict[str, Any]:
        """Validate file upload"""
        result = {
            'is_valid': True,
            'issues': []
        }
        
        # Check file extension
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif']
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            result['issues'].append(f"File type {file_ext} not allowed")
            result['is_valid'] = False
        
        # Check content type
        allowed_content_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/gif'
        ]
        
        if content_type not in allowed_content_types:
            result['issues'].append(f"Content type {content_type} not allowed")
            result['is_valid'] = False
        
        # Check file size (this would need to be implemented with actual file size)
        # result['file_size'] = file_size
        # if file_size > max_size:
        #     result['issues'].append(f"File size {file_size} exceeds maximum {max_size}")
        #     result['is_valid'] = False
        
        return result


class SecurityAuditor:
    """Security audit and monitoring"""
    
    def __init__(self):
        self.security_events: List[Dict[str, Any]] = []
        self.failed_attempts: Dict[str, int] = {}
        self.suspicious_activities: List[Dict[str, Any]] = []
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log a security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details
        }
        
        self.security_events.append(event)
        
        # Log to application logger
        if severity == "CRITICAL":
            logger.critical(f"Security event: {event_type} - {details}")
        elif severity == "WARNING":
            logger.warning(f"Security event: {event_type} - {details}")
        else:
            logger.info(f"Security event: {event_type} - {details}")
        
        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
    
    def record_failed_attempt(self, identifier: str, attempt_type: str):
        """Record a failed authentication attempt"""
        key = f"{identifier}:{attempt_type}"
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1
        
        # Log the attempt
        self.log_security_event(
            "failed_attempt",
            {
                'identifier': identifier,
                'attempt_type': attempt_type,
                'count': self.failed_attempts[key]
            },
            "WARNING"
        )
        
        # Check for suspicious activity
        if self.failed_attempts[key] >= 5:
            self.log_security_event(
                "suspicious_activity",
                {
                    'identifier': identifier,
                    'attempt_type': attempt_type,
                    'failed_count': self.failed_attempts[key]
                },
                "CRITICAL"
            )
    
    def reset_failed_attempts(self, identifier: str, attempt_type: str):
        """Reset failed attempts counter"""
        key = f"{identifier}:{attempt_type}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate security report"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > last_24h
        ]
        
        critical_events = [event for event in recent_events if event['severity'] == 'CRITICAL']
        warning_events = [event for event in recent_events if event['severity'] == 'WARNING']
        
        return {
            'total_events_24h': len(recent_events),
            'critical_events': len(critical_events),
            'warning_events': len(warning_events),
            'failed_attempts': len(self.failed_attempts),
            'suspicious_activities': len(self.suspicious_activities),
            'recent_critical_events': critical_events[-5:],  # Last 5 critical events
            'top_failed_attempts': dict(list(self.failed_attempts.items())[:10])  # Top 10
        }


# Global security instances
security_manager = SecurityManager()
input_validator = InputValidator()
security_auditor = SecurityAuditor()


def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    return security_manager


def get_input_validator() -> InputValidator:
    """Get global input validator instance"""
    return input_validator


def get_security_auditor() -> SecurityAuditor:
    """Get global security auditor instance"""
    return security_auditor


