"""
Main Email Processor - Orchestrates the entire email automation workflow
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from config import Config
from models import EmailMessage, UrgencyLevel, ResponseType, SystemStatus, ProcessingStats
from imap_listener import IMAPListener
from urgency_classifier import UrgencyClassifier
from response_generator import ResponseGenerator
from google_chat_handler import GoogleChatHandler
from email_sender import EmailSender


class EmailProcessor:
    """Main orchestrator for email automation system"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.imap_listener = IMAPListener(config)
        self.urgency_classifier = UrgencyClassifier(config)
        self.response_generator = ResponseGenerator(config)
        self.google_chat_handler = GoogleChatHandler(config)
        self.email_sender = EmailSender(config)
        
        # System state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.stats = ProcessingStats()
        self.pending_approvals: Dict[str, Any] = {}
        
        # Background tasks
        self.email_check_task: Optional[asyncio.Task] = None
        self.approval_timeout_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the email automation system"""
        try:
            self.logger.info("Starting Email Automation System...")
            
            # Test all connections first
            await self._test_connections()
            
            # Start IMAP listener
            await self.imap_listener.start()
            
            # Start background tasks
            self.email_check_task = asyncio.create_task(self._email_check_loop())
            self.approval_timeout_task = asyncio.create_task(self._approval_timeout_loop())
            
            self.is_running = True
            self.start_time = datetime.now()
            
            self.logger.info("Email Automation System started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Email Automation System: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the email automation system"""
        try:
            self.logger.info("Stopping Email Automation System...")
            
            self.is_running = False
            
            # Cancel background tasks
            if self.email_check_task:
                self.email_check_task.cancel()
                try:
                    await self.email_check_task
                except asyncio.CancelledError:
                    pass
            
            if self.approval_timeout_task:
                self.approval_timeout_task.cancel()
                try:
                    await self.approval_timeout_task
                except asyncio.CancelledError:
                    pass
            
            # Stop IMAP listener
            await self.imap_listener.stop()
            
            self.logger.info("Email Automation System stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Email Automation System: {e}")
    
    async def _test_connections(self):
        """Test all external connections"""
        self.logger.info("Testing external connections...")
        
        # Test IMAP
        try:
            await self.imap_listener.test_connection()
            self.logger.info("IMAP connection test passed")
        except Exception as e:
            self.logger.error(f"IMAP connection test failed: {e}")
            raise
        
        # Test SMTP
        try:
            await self.email_sender.test_connection()
            self.logger.info("SMTP connection test passed")
        except Exception as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            raise
        
        # Test OpenAI
        try:
            await self.urgency_classifier.test_connection()
            self.logger.info("OpenAI connection test passed")
        except Exception as e:
            self.logger.error(f"OpenAI connection test failed: {e}")
            raise
        
        # Test Google Chat
        try:
            await self.google_chat_handler.test_connection()
            self.logger.info("Google Chat connection test passed")
        except Exception as e:
            self.logger.error(f"Google Chat connection test failed: {e}")
            raise
        
        self.logger.info("All connection tests passed")
    
    async def _email_check_loop(self):
        """Main email checking loop"""
        while self.is_running:
            try:
                # Check for new emails
                new_emails = await self.imap_listener.get_new_emails()
                
                for email_msg in new_emails:
                    await self._process_email(email_msg)
                
                # Wait before next check
                await asyncio.sleep(self.config.imap_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in email check loop: {e}")
                self.stats.errors += 1
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _process_email(self, email_msg: EmailMessage):
        """Process a single email through the automation workflow"""
        try:
            self.logger.info(f"Processing email: {email_msg.message_id}")
            self.stats.emails_processed += 1
            
            # Step 1: Classify urgency
            urgency = await self.urgency_classifier.classify_urgency(email_msg)
            email_msg.urgency = urgency
            
            self.logger.info(f"Email urgency classified as: {urgency} ({urgency_to_string(urgency)})")
            
            # Step 2: Route based on urgency
            if urgency >= self.config.urgency_threshold:
                # High urgency - escalate to human
                await self._handle_urgent_email(email_msg)
            else:
                # Low urgency - generate AI response
                await self._handle_non_urgent_email(email_msg)
            
        except Exception as e:
            self.logger.error(f"Error processing email {email_msg.message_id}: {e}")
            self.stats.errors += 1
    
    async def _handle_urgent_email(self, email_msg: EmailMessage):
        """Handle urgent emails by escalating to human agents"""
        try:
            self.logger.info(f"Escalating urgent email: {email_msg.message_id}")
            self.stats.human_escalations += 1
            
            # Send notification to Google Chat
            notification_message = self._create_urgent_notification(email_msg)
            await self.google_chat_handler.send_notification(notification_message)
            
            # Set up approval request with timeout
            approval_request = {
                'message_id': email_msg.message_id,
                'email': email_msg,
                'requested_at': datetime.now(),
                'timeout_at': datetime.now() + timedelta(minutes=self.config.urgent_timeout_minutes),
                'status': 'pending'
            }
            
            self.pending_approvals[email_msg.message_id] = approval_request
            
            # Generate fallback response for timeout
            fallback_response = await self.response_generator.generate_fallback_response(email_msg)
            
            # Store fallback response for potential use
            approval_request['fallback_response'] = fallback_response
            
        except Exception as e:
            self.logger.error(f"Error handling urgent email {email_msg.message_id}: {e}")
            self.stats.errors += 1
    
    async def _handle_non_urgent_email(self, email_msg: EmailMessage):
        """Handle non-urgent emails with AI response generation"""
        try:
            self.logger.info(f"Generating AI response for email: {email_msg.message_id}")
            
            # Generate AI response
            ai_response = await self.response_generator.generate_response(email_msg)
            
            # Check if approval is required
            if self._requires_approval(email_msg):
                await self._request_approval(email_msg, ai_response)
            else:
                # Send response immediately
                await self._send_response(email_msg, ai_response, ResponseType.AI_AUTO)
            
        except Exception as e:
            self.logger.error(f"Error handling non-urgent email {email_msg.message_id}: {e}")
            self.stats.errors += 1
    
    def _requires_approval(self, email_msg: EmailMessage) -> bool:
        """Determine if email response requires human approval"""
        # Check if external domain requires approval
        if self.config.require_approval_for_external:
            sender_domain = email_msg.sender.split('@')[1]
            if sender_domain not in (self.config.allowed_senders or []):
                return True
        
        # Check if sender is in blocked list
        if self.config.blocked_senders:
            sender_domain = email_msg.sender.split('@')[1]
            if sender_domain in self.config.blocked_senders:
                return True
        
        return False
    
    async def _request_approval(self, email_msg: EmailMessage, ai_response):
        """Request human approval for AI response"""
        try:
            self.logger.info(f"Requesting approval for email: {email_msg.message_id}")
            
            # Send approval request to Google Chat
            approval_message = self._create_approval_message(email_msg, ai_response)
            await self.google_chat_handler.send_approval_request(approval_message)
            
            # Set up approval request
            approval_request = {
                'message_id': email_msg.message_id,
                'email': email_msg,
                'ai_response': ai_response,
                'requested_at': datetime.now(),
                'timeout_at': datetime.now() + timedelta(minutes=self.config.urgent_timeout_minutes),
                'status': 'pending'
            }
            
            self.pending_approvals[email_msg.message_id] = approval_request
            
        except Exception as e:
            self.logger.error(f"Error requesting approval for {email_msg.message_id}: {e}")
            self.stats.errors += 1
    
    async def _send_response(self, email_msg: EmailMessage, response, response_type: ResponseType):
        """Send email response"""
        try:
            self.logger.info(f"Sending {response_type} response for email: {email_msg.message_id}")
            
            # Send the email
            success = await self.email_sender.send_response(email_msg, response)
            
            if success:
                email_msg.response_sent = True
                email_msg.response_sent_at = datetime.now()
                email_msg.response_type = response_type
                
                if response_type == ResponseType.AI_AUTO:
                    self.stats.ai_responses += 1
                
                self.logger.info(f"Response sent successfully for email: {email_msg.message_id}")
            else:
                self.logger.error(f"Failed to send response for email: {email_msg.message_id}")
                self.stats.errors += 1
            
        except Exception as e:
            self.logger.error(f"Error sending response for {email_msg.message_id}: {e}")
            self.stats.errors += 1
    
    async def _approval_timeout_loop(self):
        """Handle approval timeouts"""
        while self.is_running:
            try:
                current_time = datetime.now()
                timed_out_approvals = []
                
                for message_id, approval_request in self.pending_approvals.items():
                    if current_time > approval_request['timeout_at']:
                        timed_out_approvals.append(message_id)
                
                # Handle timed out approvals
                for message_id in timed_out_approvals:
                    await self._handle_approval_timeout(message_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in approval timeout loop: {e}")
                await asyncio.sleep(60)
    
    async def _handle_approval_timeout(self, message_id: str):
        """Handle approval timeout"""
        try:
            approval_request = self.pending_approvals.get(message_id)
            if not approval_request:
                return
            
            self.logger.info(f"Handling approval timeout for email: {message_id}")
            self.stats.timeouts += 1
            
            email_msg = approval_request['email']
            
            # Use fallback response if available
            if 'fallback_response' in approval_request:
                fallback_response = approval_request['fallback_response']
                await self._send_response(email_msg, fallback_response, ResponseType.FALLBACK)
            else:
                # Generate new fallback response
                fallback_response = await self.response_generator.generate_fallback_response(email_msg)
                await self._send_response(email_msg, fallback_response, ResponseType.FALLBACK)
            
            # Remove from pending approvals
            del self.pending_approvals[message_id]
            
        except Exception as e:
            self.logger.error(f"Error handling approval timeout for {message_id}: {e}")
            self.stats.errors += 1
    
    async def approve_response(self, message_id: str, approved: bool, approved_by: str, comments: str = ""):
        """Handle approval decision"""
        try:
            approval_request = self.pending_approvals.get(message_id)
            if not approval_request:
                self.logger.warning(f"No pending approval found for message: {message_id}")
                return False
            
            self.logger.info(f"Processing approval decision for {message_id}: {approved}")
            
            if approved:
                self.stats.approvals_granted += 1
                # Send the approved response
                ai_response = approval_request['ai_response']
                email_msg = approval_request['email']
                await self._send_response(email_msg, ai_response, ResponseType.AI_APPROVED)
            else:
                self.stats.approvals_denied += 1
                # Send notification that response was rejected
                await self.google_chat_handler.send_notification(
                    f"Response for email {message_id} was rejected by {approved_by}. Comments: {comments}"
                )
            
            # Remove from pending approvals
            del self.pending_approvals[message_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing approval for {message_id}: {e}")
            self.stats.errors += 1
            return False
    
    async def get_status(self) -> SystemStatus:
        """Get current system status"""
        try:
            # Test connections
            imap_connected = await self.imap_listener.is_connected()
            smtp_connected = await self.email_sender.is_connected()
            openai_connected = await self.urgency_classifier.is_connected()
            google_chat_connected = await self.google_chat_handler.is_connected()
            
            uptime = 0
            if self.start_time:
                uptime = int((datetime.now() - self.start_time).total_seconds())
            
            return SystemStatus(
                is_running=self.is_running,
                imap_connected=imap_connected,
                smtp_connected=smtp_connected,
                openai_connected=openai_connected,
                google_chat_connected=google_chat_connected,
                last_email_check=datetime.now(),
                total_emails_processed=self.stats.emails_processed,
                total_responses_sent=self.stats.ai_responses + self.stats.human_escalations,
                uptime_seconds=uptime,
                error_count=self.stats.errors
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return SystemStatus(is_running=False)
    
    def get_stats(self) -> ProcessingStats:
        """Get processing statistics"""
        # Calculate success rate
        total_processed = self.stats.emails_processed
        if total_processed > 0:
            successful = self.stats.ai_responses + self.stats.human_escalations
            self.stats.success_rate = (successful / total_processed) * 100
        
        self.stats.last_updated = datetime.now()
        return self.stats
    
    async def send_test_email(self) -> bool:
        """Send a test email to verify system functionality"""
        try:
            test_email = EmailMessage(
                message_id="test-" + str(int(datetime.now().timestamp())),
                subject="Test Email - Email Automation System",
                sender="test@example.com",
                recipient=self.config.smtp_email,
                body="This is a test email to verify the email automation system is working correctly."
            )
            
            test_response = await self.response_generator.generate_test_response()
            success = await self.email_sender.send_response(test_email, test_response)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending test email: {e}")
            return False
    
    def _create_urgent_notification(self, email_msg: EmailMessage) -> str:
        """Create urgent email notification message"""
        return f"""
🚨 URGENT EMAIL REQUIRES IMMEDIATE ATTENTION 🚨

**From:** {email_msg.sender}
**Subject:** {email_msg.subject}
**Received:** {email_msg.received_at.strftime('%Y-%m-%d %H:%M:%S')}
**Urgency Level:** {email_msg.urgency} ({urgency_to_string(email_msg.urgency)})

**Message Preview:**
{email_msg.body[:200]}{'...' if len(email_msg.body) > 200 else ''}

**Message ID:** {email_msg.message_id}

Please respond within {self.config.urgent_timeout_minutes} minutes or an automated fallback response will be sent.
"""
    
    def _create_approval_message(self, email_msg: EmailMessage, ai_response) -> str:
        """Create approval request message"""
        return f"""
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

Please approve or reject this response within {self.config.urgent_timeout_minutes} minutes.
"""


def urgency_to_string(urgency: UrgencyLevel) -> str:
    """Convert urgency level to string"""
    urgency_map = {
        UrgencyLevel.VERY_LOW: "Very Low",
        UrgencyLevel.LOW: "Low",
        UrgencyLevel.MEDIUM: "Medium",
        UrgencyLevel.HIGH: "High",
        UrgencyLevel.URGENT: "Urgent"
    }
    return urgency_map.get(urgency, "Unknown")


