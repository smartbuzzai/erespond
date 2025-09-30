"""
Configuration management for Email Automation System
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field, validator
from pathlib import Path


class Config(BaseSettings):
    """Configuration class for Email Automation System"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field("gpt-4o", description="OpenAI model to use")
    
    # IMAP Configuration (Email Receiving)
    imap_host: str = Field(..., description="IMAP server hostname")
    imap_port: int = Field(993, description="IMAP server port")
    imap_email: str = Field(..., description="IMAP email address")
    imap_password: str = Field(..., description="IMAP password or app password")
    imap_check_interval: int = Field(30, description="Email check interval in seconds")
    imap_use_ssl: bool = Field(True, description="Use SSL for IMAP connection")
    
    # SMTP Configuration (Email Sending)
    smtp_host: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(587, description="SMTP server port")
    smtp_email: str = Field(..., description="SMTP email address")
    smtp_password: str = Field(..., description="SMTP password or app password")
    smtp_use_tls: bool = Field(True, description="Use TLS for SMTP connection")
    
    # Google Chat Configuration
    google_chat_webhook_url: str = Field(..., description="Google Chat webhook URL")
    google_chat_oauth_client_id: Optional[str] = Field(None, description="OAuth client ID")
    google_chat_oauth_client_secret: Optional[str] = Field(None, description="OAuth client secret")
    
    # System Configuration
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[str] = Field("email_automation.log", description="Log file path")
    urgent_timeout_minutes: int = Field(10, description="Timeout for urgent email handling in minutes")
    
    # Email Processing Configuration
    max_email_size: int = Field(10 * 1024 * 1024, description="Maximum email size in bytes (10MB)")
    supported_attachments: list = Field([".pdf", ".doc", ".docx", ".txt", ".jpg", ".png"], description="Supported attachment types")
    auto_reply_subject_prefix: str = Field("Re: ", description="Prefix for auto-reply subjects")
    
    # AI Configuration
    urgency_threshold: int = Field(4, description="Urgency threshold for human escalation (1-5 scale)")
    max_response_length: int = Field(500, description="Maximum AI response length in characters")
    response_tone: str = Field("professional", description="Response tone: professional, friendly, formal")
    
    # Security Configuration
    allowed_senders: Optional[list] = Field(None, description="List of allowed sender domains")
    blocked_senders: Optional[list] = Field(None, description="List of blocked sender domains")
    require_approval_for_external: bool = Field(True, description="Require approval for external domain emails")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @validator('openai_model')
    def validate_openai_model(cls, v):
        valid_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']
        if v not in valid_models:
            raise ValueError(f'openai_model must be one of {valid_models}')
        return v
    
    @validator('urgency_threshold')
    def validate_urgency_threshold(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('urgency_threshold must be between 1 and 5')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_config() -> Config:
    """Load configuration from environment variables and .env file"""
    try:
        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            # Create a template .env file
            create_env_template()
            raise FileNotFoundError(
                "Configuration file .env not found. A template has been created. "
                "Please fill in your configuration and restart the application."
            )
        
        config = Config()
        return config
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        raise


def create_env_template():
    """Create a template .env file with all required configuration options"""
    template = """# Email Automation System Configuration
# Copy this file and fill in your actual values

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# IMAP Configuration (Email Receiving)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=your-email@domain.com
IMAP_PASSWORD=your-app-password-here
IMAP_CHECK_INTERVAL=30
IMAP_USE_SSL=true

# SMTP Configuration (Email Sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@domain.com
SMTP_PASSWORD=your-app-password-here
SMTP_USE_TLS=true

# Google Chat Configuration
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/your-space-id/messages
GOOGLE_CHAT_OAUTH_CLIENT_ID=your-oauth-client-id
GOOGLE_CHAT_OAUTH_CLIENT_SECRET=your-oauth-client-secret

# System Configuration
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
LOG_FILE=email_automation.log
URGENT_TIMEOUT_MINUTES=10

# Email Processing Configuration
MAX_EMAIL_SIZE=10485760
SUPPORTED_ATTACHMENTS=.pdf,.doc,.docx,.txt,.jpg,.png
AUTO_REPLY_SUBJECT_PREFIX=Re: 

# AI Configuration
URGENCY_THRESHOLD=4
MAX_RESPONSE_LENGTH=500
RESPONSE_TONE=professional

# Security Configuration
ALLOWED_SENDERS=
BLOCKED_SENDERS=
REQUIRE_APPROVAL_FOR_EXTERNAL=true
"""
    
    with open(".env", "w") as f:
        f.write(template)
    
    print("Template .env file created. Please fill in your configuration values.")


def validate_config(config: Config) -> bool:
    """Validate configuration settings"""
    errors = []
    
    # Check required fields
    required_fields = [
        'openai_api_key', 'imap_host', 'imap_email', 'imap_password',
        'smtp_host', 'smtp_email', 'smtp_password', 'google_chat_webhook_url'
    ]
    
    for field in required_fields:
        if not getattr(config, field):
            errors.append(f"Required field '{field}' is missing or empty")
    
    # Validate email addresses
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, config.imap_email):
        errors.append("Invalid IMAP email address format")
    
    if not re.match(email_pattern, config.smtp_email):
        errors.append("Invalid SMTP email address format")
    
    # Validate ports
    if not 1 <= config.imap_port <= 65535:
        errors.append("IMAP port must be between 1 and 65535")
    
    if not 1 <= config.smtp_port <= 65535:
        errors.append("SMTP port must be between 1 and 65535")
    
    # Validate OpenAI API key format
    if not config.openai_api_key.startswith('sk-'):
        errors.append("OpenAI API key should start with 'sk-'")
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully!")
        print(f"IMAP Host: {config.imap_host}")
        print(f"SMTP Host: {config.smtp_host}")
        print(f"OpenAI Model: {config.openai_model}")
        print(f"Log Level: {config.log_level}")
        
        if validate_config(config):
            print("Configuration validation passed!")
        else:
            print("Configuration validation failed!")
            
    except Exception as e:
        print(f"Error: {e}")


