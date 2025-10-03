"""
Urgency Classifier - Uses OpenAI to classify email urgency
"""

import asyncio
import logging
import json
from typing import Optional
import openai
from openai import AsyncOpenAI

from config import Config
from models import EmailMessage, UrgencyLevel


class UrgencyClassifier:
    """AI-powered email urgency classifier using OpenAI"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = AsyncOpenAI(api_key=config.openai_api_key)
        self.is_connected = False
    
    async def test_connection(self):
        """Test OpenAI API connection"""
        try:
            # Test with a simple completion
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "user", "content": "Hello, this is a connection test."}
                ],
                max_tokens=10
            )
            
            self.is_connected = True
            self.logger.info("OpenAI connection test successful")
            
        except Exception as e:
            self.logger.error(f"OpenAI connection test failed: {e}")
            self.is_connected = False
            raise
    
    async def classify_urgency(self, email_msg: EmailMessage) -> UrgencyLevel:
        """Classify email urgency using AI"""
        try:
            self.logger.info(f"Classifying urgency for email: {email_msg.message_id}")
            
            # Prepare the prompt
            prompt = self._create_urgency_prompt(email_msg)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email urgency classifier. Analyze emails and determine their urgency level on a scale of 1-5."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            urgency_score = result.get('urgency', 3)
            reasoning = result.get('reasoning', 'No reasoning provided')
            
            # Validate urgency score
            if not isinstance(urgency_score, int) or not 1 <= urgency_score <= 5:
                self.logger.warning(f"Invalid urgency score {urgency_score}, defaulting to 3")
                urgency_score = 3
            
            urgency = UrgencyLevel(urgency_score)
            
            self.logger.info(f"Email urgency classified as {urgency} ({urgency_score}/5). Reasoning: {reasoning}")
            
            return urgency
            
        except Exception as e:
            self.logger.error(f"Error classifying urgency for {email_msg.message_id}: {e}")
            # Return medium urgency as fallback
            return UrgencyLevel.MEDIUM
    
    def _create_urgency_prompt(self, email_msg: EmailMessage) -> str:
        """Create prompt for urgency classification"""
        return f"""
Analyze the following email and determine its urgency level on a scale of 1-5.

URGENCY SCALE:
1 - Very Low: General inquiries, newsletters, promotional content
2 - Low: Routine business communications, scheduling requests
3 - Medium: Standard customer service requests, general questions
4 - High: Time-sensitive issues, complaints, urgent business matters
5 - Urgent: Critical issues, security concerns, immediate action required

EMAIL DETAILS:
From: {email_msg.sender}
Subject: {email_msg.subject}
Received: {email_msg.received_at.strftime('%Y-%m-%d %H:%M:%S')}

EMAIL CONTENT:
{email_msg.body}

Please respond with a JSON object containing:
- "urgency": integer from 1-5
- "reasoning": brief explanation of why this urgency level was chosen
- "key_indicators": list of specific words/phrases that influenced the decision
- "suggested_action": recommended next step (auto-respond, human-review, escalate)

Consider factors like:
- Time sensitivity
- Customer impact
- Business criticality
- Emotional tone
- Request complexity
- Security implications
"""
    
    async def classify_batch(self, emails: list[EmailMessage]) -> list[tuple[EmailMessage, UrgencyLevel]]:
        """Classify urgency for multiple emails in batch"""
        try:
            self.logger.info(f"Classifying urgency for {len(emails)} emails")
            
            # Create batch prompt
            batch_prompt = self._create_batch_prompt(emails)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email urgency classifier. Analyze multiple emails and determine their urgency levels on a scale of 1-5."
                    },
                    {
                        "role": "user",
                        "content": batch_prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            classifications = result.get('classifications', [])
            
            # Map results back to emails
            results = []
            for i, email_msg in enumerate(emails):
                if i < len(classifications):
                    urgency_score = classifications[i].get('urgency', 3)
                    if not isinstance(urgency_score, int) or not 1 <= urgency_score <= 5:
                        urgency_score = 3
                    urgency = UrgencyLevel(urgency_score)
                else:
                    urgency = UrgencyLevel.MEDIUM  # Default fallback
                
                results.append((email_msg, urgency))
            
            self.logger.info(f"Batch classification completed for {len(emails)} emails")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch classification: {e}")
            # Return default urgency for all emails
            return [(email_msg, UrgencyLevel.MEDIUM) for email_msg in emails]
    
    def _create_batch_prompt(self, emails: list[EmailMessage]) -> str:
        """Create prompt for batch urgency classification"""
        email_list = []
        for i, email_msg in enumerate(emails):
            email_list.append(f"""
EMAIL {i+1}:
From: {email_msg.sender}
Subject: {email_msg.subject}
Content: {email_msg.body[:500]}{'...' if len(email_msg.body) > 500 else ''}
""")
        
        return f"""
Analyze the following {len(emails)} emails and determine their urgency levels on a scale of 1-5.

URGENCY SCALE:
1 - Very Low: General inquiries, newsletters, promotional content
2 - Low: Routine business communications, scheduling requests
3 - Medium: Standard customer service requests, general questions
4 - High: Time-sensitive issues, complaints, urgent business matters
5 - Urgent: Critical issues, security concerns, immediate action required

EMAILS:
{''.join(email_list)}

Please respond with a JSON object containing:
- "classifications": array of objects, one for each email, containing:
  - "urgency": integer from 1-5
  - "reasoning": brief explanation
  - "key_indicators": list of specific words/phrases
  - "suggested_action": recommended next step
"""
    
    async def get_urgency_explanation(self, email_msg: EmailMessage, urgency: UrgencyLevel) -> str:
        """Get detailed explanation for urgency classification"""
        try:
            prompt = f"""
Explain why the following email was classified as urgency level {urgency.value}/5.

EMAIL:
From: {email_msg.sender}
Subject: {email_msg.subject}
Content: {email_msg.body}

Provide a detailed explanation including:
- Key factors that influenced the classification
- Specific words or phrases that indicated this urgency level
- Recommended handling approach
- Potential risks of misclassification
"""
            
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email analyst. Provide detailed explanations for urgency classifications."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error getting urgency explanation: {e}")
            return f"Urgency level {urgency.value}/5 - Detailed explanation unavailable due to error."
    
    async def is_connected(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            # Simple test call
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            self.logger.warning(f"OpenAI connection check failed: {e}")
            return False
    
    def get_classification_stats(self) -> dict:
        """Get classification statistics"""
        return {
            'model': self.config.openai_model,
            'is_connected': self.is_connected,
            'api_key_configured': bool(self.config.openai_api_key),
            'last_classification': None  # Could track this if needed
        }







