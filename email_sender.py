"""
Email Sender - Handles SMTP email sending
"""

import asyncio
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
import aiosmtplib

from config import Config
from models import EmailMessage, AIResponse


class EmailSender:
    """SMTP email sender for sending responses"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.smtp_client: Optional[aiosmtplib.SMTP] = None
    
    async def start(self):
        """Start the email sender"""
        try:
            await self._connect()
            self.logger.info("Email sender started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start email sender: {e}")
            raise
    
    async def stop(self):
        """Stop the email sender"""
        try:
            if self.smtp_client:
                await self.smtp_client.quit()
                self.smtp_client = None
            self.is_connected = False
            self.logger.info("Email sender stopped")
        except Exception as e:
            self.logger.error(f"Error stopping email sender: {e}")
    
    async def _connect(self):
        """Establish SMTP connection"""
        try:
            self.logger.info(f"Connecting to SMTP server: {self.config.smtp_host}:{self.config.smtp_port}")
            
            # Create SMTP client
            self.smtp_client = aiosmtplib.SMTP(
                hostname=self.config.smtp_host,
                port=self.config.smtp_port,
                use_tls=self.config.smtp_use_tls
            )
            
            # Connect and login
            await self.smtp_client.connect()
            await self.smtp_client.login(self.config.smtp_email, self.config.smtp_password)
            
            self.is_connected = True
            self.logger.info("SMTP connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {e}")
            self.is_connected = False
            raise
    
    async def test_connection(self):
        """Test SMTP connection"""
        try:
            if not self.is_connected:
                await self._connect()
            
            # Test by sending a simple command
            await self.smtp_client.noop()
            self.logger.info("SMTP connection test successful")
            
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            raise
    
    async def send_response(self, original_email: EmailMessage, ai_response: AIResponse) -> bool:
        """Send email response"""
        try:
            self.logger.info(f"Sending response for email: {original_email.message_id}")
            
            if not self.is_connected:
                await self._connect()
            
            # Create email message
            msg = await self._create_response_message(original_email, ai_response)
            
            # Send email
            await self.smtp_client.send_message(msg)
            
            self.logger.info(f"Response sent successfully for email: {original_email.message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending response for {original_email.message_id}: {e}")
            return False
    
    async def _create_response_message(self, original_email: EmailMessage, ai_response: AIResponse) -> MIMEMultipart:
        """Create response email message"""
        msg = MIMEMultipart()
        
        # Parse the AI response to extract subject and body
        response_text = ai_response.response_text
        
        # Extract subject line (first line if it starts with "Subject:")
        subject = original_email.subject
        body = response_text
        
        if response_text.startswith("Subject:"):
            lines = response_text.split('\n', 1)
            if len(lines) > 1:
                subject = lines[0].replace("Subject:", "").strip()
                body = lines[1].strip()
        
        # Add subject prefix if configured
        if self.config.auto_reply_subject_prefix and not subject.startswith(self.config.auto_reply_subject_prefix):
            subject = f"{self.config.auto_reply_subject_prefix}{subject}"
        
        # Set headers
        msg['From'] = self.config.smtp_email
        msg['To'] = original_email.sender
        msg['Subject'] = subject
        msg['In-Reply-To'] = original_email.message_id
        msg['References'] = original_email.message_id
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add metadata headers
        msg['X-Auto-Response'] = 'true'
        msg['X-AI-Confidence'] = str(ai_response.confidence_score)
        msg['X-Response-Type'] = 'ai-generated'
        
        return msg
    
    async def send_test_email(self, recipient: str = None) -> bool:
        """Send a test email"""
        try:
            if not recipient:
                recipient = self.config.smtp_email
            
            self.logger.info(f"Sending test email to: {recipient}")
            
            if not self.is_connected:
                await self._connect()
            
            # Create test message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_email
            msg['To'] = recipient
            msg['Subject'] = "Email Automation System - Test Email"
            
            body = f"""
This is a test email from the Email Automation System.

System Information:
- SMTP Host: {self.config.smtp_host}
- SMTP Port: {self.config.smtp_port}
- From Email: {self.config.smtp_email}
- Test Time: {asyncio.get_event_loop().time()}

If you receive this email, the SMTP configuration is working correctly.

Best regards,
Email Automation System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            await self.smtp_client.send_message(msg)
            
            self.logger.info("Test email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending test email: {e}")
            return False
    
    async def send_notification_email(self, subject: str, body: str, recipients: List[str] = None) -> bool:
        """Send notification email to specified recipients"""
        try:
            if not recipients:
                recipients = [self.config.smtp_email]
            
            self.logger.info(f"Sending notification email to {len(recipients)} recipients")
            
            if not self.is_connected:
                await self._connect()
            
            # Create notification message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_email
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[Email Automation] {subject}"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            await self.smtp_client.send_message(msg)
            
            self.logger.info("Notification email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending notification email: {e}")
            return False
    
    async def send_error_report(self, error_message: str, error_details: str = "", email_context: Dict[str, Any] = None) -> bool:
        """Send error report email"""
        try:
            self.logger.info("Sending error report email")
            
            subject = "Email Automation System - Error Report"
            body = f"""
An error occurred in the Email Automation System.

ERROR DETAILS:
{error_message}

ADDITIONAL INFORMATION:
{error_details}

EMAIL CONTEXT:
{json.dumps(email_context, indent=2) if email_context else 'No email context available'}

SYSTEM INFORMATION:
- SMTP Host: {self.config.smtp_host}
- SMTP Port: {self.config.smtp_port}
- Error Time: {asyncio.get_event_loop().time()}

Please check the system logs for more detailed information.

Best regards,
Email Automation System
"""
            
            return await self.send_notification_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"Error sending error report: {e}")
            return False
    
    async def send_daily_report(self, stats: Dict[str, Any]) -> bool:
        """Send daily processing report"""
        try:
            self.logger.info("Sending daily report email")
            
            subject = "Email Automation System - Daily Report"
            body = f"""
Daily Email Automation System Report

PROCESSING STATISTICS:
- Emails Processed: {stats.get('emails_processed', 0)}
- AI Responses: {stats.get('ai_responses', 0)}
- Human Escalations: {stats.get('human_escalations', 0)}
- Approvals Granted: {stats.get('approvals_granted', 0)}
- Approvals Denied: {stats.get('approvals_denied', 0)}
- Timeouts: {stats.get('timeouts', 0)}
- Errors: {stats.get('errors', 0)}

PERFORMANCE METRICS:
- Success Rate: {stats.get('success_rate', 0):.1f}%
- Average Response Time: {stats.get('avg_response_time_seconds', 0):.1f} seconds
- Uptime: {stats.get('uptime_seconds', 0)} seconds

SYSTEM STATUS:
- IMAP: {'Connected' if stats.get('imap_connected') else 'Disconnected'}
- SMTP: {'Connected' if stats.get('smtp_connected') else 'Disconnected'}
- OpenAI: {'Connected' if stats.get('openai_connected') else 'Disconnected'}
- Google Chat: {'Connected' if stats.get('google_chat_connected') else 'Disconnected'}

The system is running smoothly. Great work!

Best regards,
Email Automation System
"""
            
            return await self.send_notification_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if SMTP connection is active"""
        try:
            if not self.smtp_client:
                return False
            
            # Test connection with NOOP command
            await self.smtp_client.noop()
            return True
            
        except Exception as e:
            self.logger.warning(f"SMTP connection check failed: {e}")
            self.is_connected = False
            return False
    
    async def reconnect(self):
        """Reconnect to SMTP server"""
        try:
            await self.stop()
            await asyncio.sleep(1)  # Brief pause before reconnecting
            await self._connect()
            self.logger.info("SMTP reconnected successfully")
        except Exception as e:
            self.logger.error(f"Failed to reconnect to SMTP: {e}")
            raise
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'host': self.config.smtp_host,
            'port': self.config.smtp_port,
            'email': self.config.smtp_email,
            'use_tls': self.config.smtp_use_tls,
            'is_connected': self.is_connected,
            'last_activity': asyncio.get_event_loop().time()
        }


