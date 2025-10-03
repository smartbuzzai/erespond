"""
Data models for Email Automation System
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import email
import json


class UrgencyLevel(int, Enum):
    """Email urgency levels (1-5 scale)"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    URGENT = 5


class ResponseType(str, Enum):
    """Types of email responses"""
    AI_AUTO = "ai_auto"
    AI_APPROVED = "ai_approved"
    HUMAN_RESPONSE = "human_response"
    ESCALATION = "escalation"
    FALLBACK = "fallback"


class EmailMessage(BaseModel):
    """Email message model"""
    message_id: str = Field(..., description="Unique message ID")
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Sender email address")
    recipient: str = Field(..., description="Recipient email address")
    body: str = Field(..., description="Email body content")
    html_body: Optional[str] = Field(None, description="HTML email body")
    received_at: datetime = Field(default_factory=datetime.now, description="When email was received")
    urgency: Optional[UrgencyLevel] = Field(None, description="AI-determined urgency level")
    response_type: Optional[ResponseType] = Field(None, description="Type of response sent")
    response_sent: bool = Field(False, description="Whether a response was sent")
    response_sent_at: Optional[datetime] = Field(None, description="When response was sent")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Email attachments")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('sender', 'recipient')
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email address format')
        return v.lower()
    
    @validator('urgency')
    def validate_urgency(cls, v):
        if v is not None and not isinstance(v, UrgencyLevel):
            if isinstance(v, int) and 1 <= v <= 5:
                return UrgencyLevel(v)
            raise ValueError('Urgency must be between 1 and 5')
        return v


class AIResponse(BaseModel):
    """AI-generated response model"""
    message_id: str = Field(..., description="Original message ID")
    response_text: str = Field(..., description="Generated response text")
    confidence_score: float = Field(..., description="AI confidence score (0-1)")
    reasoning: str = Field(..., description="AI reasoning for the response")
    suggested_urgency: UrgencyLevel = Field(..., description="AI-suggested urgency level")
    requires_human_review: bool = Field(False, description="Whether response needs human approval")
    created_at: datetime = Field(default_factory=datetime.now, description="When response was created")
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v


class ApprovalRequest(BaseModel):
    """Human approval request model"""
    message_id: str = Field(..., description="Original message ID")
    ai_response: AIResponse = Field(..., description="AI-generated response")
    original_email: EmailMessage = Field(..., description="Original email message")
    requested_at: datetime = Field(default_factory=datetime.now, description="When approval was requested")
    approved: Optional[bool] = Field(None, description="Whether request was approved")
    approved_at: Optional[datetime] = Field(None, description="When request was approved")
    approved_by: Optional[str] = Field(None, description="Who approved the request")
    comments: Optional[str] = Field(None, description="Approval comments")
    timeout_minutes: int = Field(10, description="Approval timeout in minutes")


class SystemStatus(BaseModel):
    """System status model"""
    is_running: bool = Field(False, description="Whether system is running")
    imap_connected: bool = Field(False, description="IMAP connection status")
    smtp_connected: bool = Field(False, description="SMTP connection status")
    openai_connected: bool = Field(False, description="OpenAI API connection status")
    google_chat_connected: bool = Field(False, description="Google Chat connection status")
    last_email_check: Optional[datetime] = Field(None, description="Last email check time")
    last_response_sent: Optional[datetime] = Field(None, description="Last response sent time")
    total_emails_processed: int = Field(0, description="Total emails processed")
    total_responses_sent: int = Field(0, description="Total responses sent")
    uptime_seconds: int = Field(0, description="System uptime in seconds")
    error_count: int = Field(0, description="Total error count")
    last_error: Optional[str] = Field(None, description="Last error message")


class ProcessingStats(BaseModel):
    """Email processing statistics"""
    emails_processed: int = Field(0, description="Total emails processed")
    ai_responses: int = Field(0, description="AI-generated responses")
    human_escalations: int = Field(0, description="Human escalations")
    approvals_granted: int = Field(0, description="Approvals granted")
    approvals_denied: int = Field(0, description="Approvals denied")
    timeouts: int = Field(0, description="Approval timeouts")
    errors: int = Field(0, description="Processing errors")
    success_rate: float = Field(0.0, description="Success rate percentage")
    avg_response_time_seconds: float = Field(0.0, description="Average response time")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last stats update")


class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: datetime = Field(default_factory=datetime.now, description="Log timestamp")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    module: str = Field(..., description="Module that generated the log")
    message_id: Optional[str] = Field(None, description="Related message ID")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="Additional log data")


class EmailTemplate(BaseModel):
    """Email response template model"""
    name: str = Field(..., description="Template name")
    subject_template: str = Field(..., description="Subject line template")
    body_template: str = Field(..., description="Body template")
    urgency_levels: List[UrgencyLevel] = Field(..., description="Applicable urgency levels")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Template conditions")
    is_active: bool = Field(True, description="Whether template is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    message_id: Optional[str] = Field(None, description="Related message ID")


class ConnectionTestResult(BaseModel):
    """Connection test result model"""
    service: str = Field(..., description="Service name")
    success: bool = Field(..., description="Whether connection was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    tested_at: datetime = Field(default_factory=datetime.now, description="Test timestamp")


def create_email_from_raw(raw_email: bytes, message_id: str) -> EmailMessage:
    """Create EmailMessage from raw email bytes"""
    try:
        # Parse the raw email
        msg = email.message_from_bytes(raw_email)
        
        # Extract basic information
        subject = msg.get('Subject', 'No Subject')
        sender = msg.get('From', '')
        recipient = msg.get('To', '')
        
        # Extract body content
        body = ""
        html_body = None
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            elif content_type == "text/html":
                html_body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                body = html_body  # Fallback to HTML if no plain text
        
        # Extract attachments
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                        })
        
        # Create EmailMessage
        return EmailMessage(
            message_id=message_id,
            subject=subject,
            sender=sender,
            recipient=recipient,
            body=body,
            html_body=html_body,
            attachments=attachments,
            metadata={
                'raw_headers': dict(msg.items()),
                'content_type': msg.get_content_type(),
                'date': msg.get('Date'),
                'message_size': len(raw_email)
            }
        )
        
    except Exception as e:
        # Create a minimal EmailMessage if parsing fails
        return EmailMessage(
            message_id=message_id,
            subject="Parse Error",
            sender="unknown@unknown.com",
            recipient="unknown@unknown.com",
            body=f"Failed to parse email: {str(e)}",
            metadata={'parse_error': str(e), 'raw_size': len(raw_email)}
        )


def urgency_to_string(urgency: UrgencyLevel) -> str:
    """Convert urgency level to human-readable string"""
    urgency_map = {
        UrgencyLevel.VERY_LOW: "Very Low",
        UrgencyLevel.LOW: "Low",
        UrgencyLevel.MEDIUM: "Medium",
        UrgencyLevel.HIGH: "High",
        UrgencyLevel.URGENT: "Urgent"
    }
    return urgency_map.get(urgency, "Unknown")


def response_type_to_string(response_type: ResponseType) -> str:
    """Convert response type to human-readable string"""
    type_map = {
        ResponseType.AI_AUTO: "AI Auto-Response",
        ResponseType.AI_APPROVED: "AI Approved Response",
        ResponseType.HUMAN_RESPONSE: "Human Response",
        ResponseType.ESCALATION: "Escalation",
        ResponseType.FALLBACK: "Fallback Response"
    }
    return type_map.get(response_type, "Unknown")







