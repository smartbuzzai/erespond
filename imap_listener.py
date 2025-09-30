"""
IMAP Email Listener - Monitors incoming emails
"""

import asyncio
import logging
import email
from datetime import datetime, timedelta
from typing import List, Optional
import imaplib
import ssl

from config import Config
from models import EmailMessage, create_email_from_raw


class IMAPListener:
    """IMAP email listener for monitoring incoming emails"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.imap_client: Optional[imaplib.IMAP4_SSL] = None
        self.is_connected = False
        self.last_check_time: Optional[datetime] = None
        self.processed_message_ids: set = set()
    
    async def start(self):
        """Start the IMAP listener"""
        try:
            await self._connect()
            self.logger.info("IMAP listener started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start IMAP listener: {e}")
            raise
    
    async def stop(self):
        """Stop the IMAP listener"""
        try:
            if self.imap_client:
                self.imap_client.close()
                self.imap_client.logout()
                self.imap_client = None
            self.is_connected = False
            self.logger.info("IMAP listener stopped")
        except Exception as e:
            self.logger.error(f"Error stopping IMAP listener: {e}")
    
    async def _connect(self):
        """Establish IMAP connection"""
        try:
            self.logger.info(f"Connecting to IMAP server: {self.config.imap_host}:{self.config.imap_port}")
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to IMAP server
            if self.config.imap_use_ssl:
                self.imap_client = imaplib.IMAP4_SSL(
                    self.config.imap_host, 
                    self.config.imap_port, 
                    ssl_context=context
                )
            else:
                self.imap_client = imaplib.IMAP4(self.config.imap_host, self.config.imap_port)
            
            # Login
            self.imap_client.login(self.config.imap_email, self.config.imap_password)
            
            # Select inbox
            self.imap_client.select('INBOX')
            
            self.is_connected = True
            self.logger.info("IMAP connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to IMAP server: {e}")
            self.is_connected = False
            raise
    
    async def test_connection(self):
        """Test IMAP connection"""
        try:
            if not self.is_connected:
                await self._connect()
            
            # Test by selecting inbox
            self.imap_client.select('INBOX')
            self.logger.info("IMAP connection test successful")
            
        except Exception as e:
            self.logger.error(f"IMAP connection test failed: {e}")
            raise
    
    async def get_new_emails(self) -> List[EmailMessage]:
        """Get new emails since last check"""
        try:
            if not self.is_connected:
                await self._connect()
            
            # Select inbox
            self.imap_client.select('INBOX')
            
            # Search for unread emails
            status, messages = self.imap_client.search(None, 'UNSEEN')
            
            if status != 'OK':
                self.logger.error("Failed to search for emails")
                return []
            
            email_ids = messages[0].split()
            new_emails = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = self.imap_client.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_msg = create_email_from_raw(raw_email, email_id.decode())
                    
                    # Check if we've already processed this email
                    if email_msg.message_id in self.processed_message_ids:
                        continue
                    
                    # Add to processed set
                    self.processed_message_ids.add(email_msg.message_id)
                    
                    # Mark as read
                    self.imap_client.store(email_id, '+FLAGS', '\\Seen')
                    
                    new_emails.append(email_msg)
                    
                    self.logger.info(f"Retrieved new email: {email_msg.message_id} from {email_msg.sender}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            self.last_check_time = datetime.now()
            self.logger.info(f"Retrieved {len(new_emails)} new emails")
            
            return new_emails
            
        except Exception as e:
            self.logger.error(f"Error getting new emails: {e}")
            self.is_connected = False
            return []
    
    async def get_emails_since(self, since_time: datetime) -> List[EmailMessage]:
        """Get emails since a specific time"""
        try:
            if not self.is_connected:
                await self._connect()
            
            # Select inbox
            self.imap_client.select('INBOX')
            
            # Format date for IMAP search
            date_str = since_time.strftime('%d-%b-%Y')
            
            # Search for emails since date
            status, messages = self.imap_client.search(None, f'SINCE {date_str}')
            
            if status != 'OK':
                self.logger.error("Failed to search for emails since date")
                return []
            
            email_ids = messages[0].split()
            emails = []
            
            for email_id in email_ids:
                try:
                    # Fetch email
                    status, msg_data = self.imap_client.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_msg = create_email_from_raw(raw_email, email_id.decode())
                    
                    # Check if email is newer than since_time
                    if email_msg.received_at > since_time:
                        emails.append(email_msg)
                    
                except Exception as e:
                    self.logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(emails)} emails since {since_time}")
            return emails
            
        except Exception as e:
            self.logger.error(f"Error getting emails since {since_time}: {e}")
            return []
    
    async def mark_as_read(self, message_id: str):
        """Mark an email as read"""
        try:
            if not self.is_connected:
                await self._connect()
            
            # Search for the specific message
            status, messages = self.imap_client.search(None, f'HEADER Message-ID "{message_id}"')
            
            if status != 'OK' or not messages[0]:
                self.logger.warning(f"Could not find message with ID: {message_id}")
                return False
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                # Mark as read
                self.imap_client.store(email_id, '+FLAGS', '\\Seen')
            
            self.logger.info(f"Marked email as read: {message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking email as read {message_id}: {e}")
            return False
    
    async def move_to_folder(self, message_id: str, folder_name: str):
        """Move an email to a specific folder"""
        try:
            if not self.is_connected:
                await self._connect()
            
            # Create folder if it doesn't exist
            try:
                self.imap_client.create(folder_name)
            except imaplib.IMAP4.error:
                pass  # Folder already exists
            
            # Search for the specific message
            status, messages = self.imap_client.search(None, f'HEADER Message-ID "{message_id}"')
            
            if status != 'OK' or not messages[0]:
                self.logger.warning(f"Could not find message with ID: {message_id}")
                return False
            
            email_ids = messages[0].split()
            
            for email_id in email_ids:
                # Copy to folder
                self.imap_client.copy(email_id, folder_name)
                # Delete from inbox
                self.imap_client.store(email_id, '+FLAGS', '\\Deleted')
            
            # Expunge deleted messages
            self.imap_client.expunge()
            
            self.logger.info(f"Moved email to {folder_name}: {message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error moving email to folder {message_id}: {e}")
            return False
    
    async def get_folder_list(self) -> List[str]:
        """Get list of available folders"""
        try:
            if not self.is_connected:
                await self._connect()
            
            status, folders = self.imap_client.list()
            
            if status != 'OK':
                self.logger.error("Failed to get folder list")
                return []
            
            folder_names = []
            for folder in folders:
                # Parse folder name from IMAP response
                folder_str = folder.decode()
                if '"/"' in folder_str:
                    folder_name = folder_str.split('"/"')[1].strip('"')
                    folder_names.append(folder_name)
            
            return folder_names
            
        except Exception as e:
            self.logger.error(f"Error getting folder list: {e}")
            return []
    
    async def is_connected(self) -> bool:
        """Check if IMAP connection is active"""
        try:
            if not self.imap_client:
                return False
            
            # Test connection by selecting inbox
            self.imap_client.select('INBOX')
            return True
            
        except Exception as e:
            self.logger.warning(f"IMAP connection check failed: {e}")
            self.is_connected = False
            return False
    
    async def reconnect(self):
        """Reconnect to IMAP server"""
        try:
            await self.stop()
            await asyncio.sleep(1)  # Brief pause before reconnecting
            await self._connect()
            self.logger.info("IMAP reconnected successfully")
        except Exception as e:
            self.logger.error(f"Failed to reconnect to IMAP: {e}")
            raise
    
    def get_connection_info(self) -> dict:
        """Get connection information"""
        return {
            'host': self.config.imap_host,
            'port': self.config.imap_port,
            'email': self.config.imap_email,
            'use_ssl': self.config.imap_use_ssl,
            'is_connected': self.is_connected,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None
        }


