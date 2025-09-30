"""
Google Chat Handler - Manages Google Chat notifications and approvals
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any
import aiohttp
from datetime import datetime

from config import Config
from models import EmailMessage, AIResponse


class GoogleChatHandler:
    """Handles Google Chat notifications and approval requests"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.webhook_url = config.google_chat_webhook_url
        self.is_connected = False
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Start the Google Chat handler"""
        try:
            self.session = aiohttp.ClientSession()
            await self.test_connection()
            self.logger.info("Google Chat handler started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start Google Chat handler: {e}")
            raise
    
    async def stop(self):
        """Stop the Google Chat handler"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            self.is_connected = False
            self.logger.info("Google Chat handler stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Google Chat handler: {e}")
    
    async def test_connection(self):
        """Test Google Chat webhook connection"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Send a test message
            test_message = {
                "text": "🔧 Email Automation System - Connection Test Successful"
            }
            
            async with self.session.post(self.webhook_url, json=test_message) as response:
                if response.status == 200:
                    self.is_connected = True
                    self.logger.info("Google Chat connection test successful")
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Google Chat connection test failed: {e}")
            self.is_connected = False
            raise
    
    async def send_notification(self, message: str, message_type: str = "info"):
        """Send a notification to Google Chat"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Format message based on type
            formatted_message = self._format_message(message, message_type)
            
            async with self.session.post(self.webhook_url, json=formatted_message) as response:
                if response.status == 200:
                    self.logger.info("Notification sent to Google Chat successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Failed to send notification: HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending notification to Google Chat: {e}")
            return False
    
    async def send_approval_request(self, message: str, approval_data: Dict[str, Any] = None):
        """Send an approval request to Google Chat with interactive buttons"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Create interactive card with approval buttons
            card_message = self._create_approval_card(message, approval_data)
            
            async with self.session.post(self.webhook_url, json=card_message) as response:
                if response.status == 200:
                    self.logger.info("Approval request sent to Google Chat successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Failed to send approval request: HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending approval request to Google Chat: {e}")
            return False
    
    def _format_message(self, message: str, message_type: str) -> Dict[str, Any]:
        """Format message for Google Chat"""
        # Choose emoji based on message type
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "urgent": "🚨"
        }
        
        emoji = emoji_map.get(message_type, "📧")
        
        return {
            "text": f"{emoji} {message}",
            "thread": {
                "name": "email-automation-system"
            }
        }
    
    def _create_approval_card(self, message: str, approval_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an interactive approval card for Google Chat"""
        message_id = approval_data.get('message_id', 'unknown') if approval_data else 'unknown'
        
        return {
            "cards": [
                {
                    "header": {
                        "title": "📧 Email Response Approval Required",
                        "subtitle": f"Message ID: {message_id}",
                        "imageUrl": "https://via.placeholder.com/40x40/4285f4/ffffff?text=📧"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": message
                                    }
                                }
                            ]
                        },
                        {
                            "widgets": [
                                {
                                    "buttons": [
                                        {
                                            "textButton": {
                                                "text": "✅ APPROVE",
                                                "onClick": {
                                                    "action": {
                                                        "actionMethodName": "approve_response",
                                                        "parameters": [
                                                            {
                                                                "key": "message_id",
                                                                "value": message_id
                                                            },
                                                            {
                                                                "key": "action",
                                                                "value": "approve"
                                                            }
                                                        ]
                                                    }
                                                }
                                            }
                                        },
                                        {
                                            "textButton": {
                                                "text": "❌ REJECT",
                                                "onClick": {
                                                    "action": {
                                                        "actionMethodName": "approve_response",
                                                        "parameters": [
                                                            {
                                                                "key": "message_id",
                                                                "value": message_id
                                                            },
                                                            {
                                                                "key": "action",
                                                                "value": "reject"
                                                            }
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": f"⏰ <b>Timeout:</b> {self.config.urgent_timeout_minutes} minutes"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ],
            "thread": {
                "name": "email-approval-requests"
            }
        }
    
    async def send_urgent_notification(self, email_msg: EmailMessage):
        """Send urgent email notification"""
        try:
            notification = f"""
🚨 URGENT EMAIL REQUIRES IMMEDIATE ATTENTION 🚨

**From:** {email_msg.sender}
**Subject:** {email_msg.subject}
**Received:** {email_msg.received_at.strftime('%Y-%m-%d %H:%M:%S')}
**Urgency Level:** {email_msg.urgency.value}/5

**Message Preview:**
{email_msg.body[:200]}{'...' if len(email_msg.body) > 200 else ''}

**Message ID:** {email_msg.message_id}

Please respond within {self.config.urgent_timeout_minutes} minutes or an automated fallback response will be sent.
"""
            
            return await self.send_notification(notification, "urgent")
            
        except Exception as e:
            self.logger.error(f"Error sending urgent notification: {e}")
            return False
    
    async def send_approval_notification(self, email_msg: EmailMessage, ai_response: AIResponse):
        """Send approval request notification"""
        try:
            approval_message = f"""
📧 EMAIL RESPONSE REQUIRES APPROVAL

**From:** {email_msg.sender}
**Subject:** {email_msg.subject}
**Received:** {email_msg.received_at.strftime('%Y-%m-%d %H:%M:%S')}

**Original Message:**
{email_msg.body[:300]}{'...' if len(email_msg.body) > 300 else ''}

**Proposed AI Response:**
{ai_response.response_text}

**Confidence Score:** {ai_response.confidence_score:.2f}
**Reasoning:** {ai_response.reasoning}

**Message ID:** {email_msg.message_id}
"""
            
            approval_data = {
                'message_id': email_msg.message_id,
                'email': email_msg.dict(),
                'ai_response': ai_response.dict()
            }
            
            return await self.send_approval_request(approval_message, approval_data)
            
        except Exception as e:
            self.logger.error(f"Error sending approval notification: {e}")
            return False
    
    async def send_system_status(self, status: Dict[str, Any]):
        """Send system status update"""
        try:
            status_message = f"""
📊 EMAIL AUTOMATION SYSTEM STATUS

**System Status:** {'🟢 Running' if status.get('is_running') else '🔴 Stopped'}
**IMAP:** {'🟢 Connected' if status.get('imap_connected') else '🔴 Disconnected'}
**SMTP:** {'🟢 Connected' if status.get('smtp_connected') else '🔴 Disconnected'}
**OpenAI:** {'🟢 Connected' if status.get('openai_connected') else '🔴 Disconnected'}

**Statistics:**
- Emails Processed: {status.get('total_emails_processed', 0)}
- Responses Sent: {status.get('total_responses_sent', 0)}
- Uptime: {status.get('uptime_seconds', 0)} seconds
- Errors: {status.get('error_count', 0)}

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return await self.send_notification(status_message, "info")
            
        except Exception as e:
            self.logger.error(f"Error sending system status: {e}")
            return False
    
    async def send_error_alert(self, error_message: str, error_details: str = ""):
        """Send error alert notification"""
        try:
            alert_message = f"""
🚨 SYSTEM ERROR ALERT

**Error:** {error_message}

**Details:** {error_details}

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system logs for more information.
"""
            
            return await self.send_notification(alert_message, "error")
            
        except Exception as e:
            self.logger.error(f"Error sending error alert: {e}")
            return False
    
    async def send_daily_summary(self, stats: Dict[str, Any]):
        """Send daily summary report"""
        try:
            summary_message = f"""
📈 DAILY EMAIL AUTOMATION SUMMARY

**Date:** {datetime.now().strftime('%Y-%m-%d')}

**Processing Statistics:**
- Emails Processed: {stats.get('emails_processed', 0)}
- AI Responses: {stats.get('ai_responses', 0)}
- Human Escalations: {stats.get('human_escalations', 0)}
- Approvals Granted: {stats.get('approvals_granted', 0)}
- Approvals Denied: {stats.get('approvals_denied', 0)}
- Timeouts: {stats.get('timeouts', 0)}
- Errors: {stats.get('errors', 0)}

**Success Rate:** {stats.get('success_rate', 0):.1f}%

**System Performance:**
- Average Response Time: {stats.get('avg_response_time_seconds', 0):.1f} seconds
- Uptime: {stats.get('uptime_seconds', 0)} seconds

Great work! The system is running smoothly.
"""
            
            return await self.send_notification(summary_message, "success")
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if Google Chat webhook is accessible"""
        try:
            if not self.session:
                return False
            
            # Simple test request
            test_message = {"text": "Connection test"}
            async with self.session.post(self.webhook_url, json=test_message) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.warning(f"Google Chat connection check failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'webhook_url': self.webhook_url,
            'is_connected': self.is_connected,
            'oauth_configured': bool(self.config.google_chat_oauth_client_id),
            'last_test': datetime.now().isoformat()
        }


