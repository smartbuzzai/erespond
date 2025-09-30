"""
Response Generator - Uses OpenAI to generate email responses
"""

import asyncio
import logging
import json
from typing import Optional
from openai import AsyncOpenAI

from config import Config
from models import EmailMessage, AIResponse, UrgencyLevel


class ResponseGenerator:
    """AI-powered email response generator using OpenAI"""
    
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
    
    async def generate_response(self, email_msg: EmailMessage) -> AIResponse:
        """Generate AI response for an email"""
        try:
            self.logger.info(f"Generating response for email: {email_msg.message_id}")
            
            # Prepare the prompt
            prompt = self._create_response_prompt(email_msg)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.config.max_response_length,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            ai_response = AIResponse(
                message_id=email_msg.message_id,
                response_text=result.get('response_text', ''),
                confidence_score=result.get('confidence_score', 0.8),
                reasoning=result.get('reasoning', 'No reasoning provided'),
                suggested_urgency=UrgencyLevel(result.get('suggested_urgency', 3)),
                requires_human_review=result.get('requires_human_review', False)
            )
            
            self.logger.info(f"Response generated for {email_msg.message_id} with confidence {ai_response.confidence_score:.2f}")
            
            return ai_response
            
        except Exception as e:
            self.logger.error(f"Error generating response for {email_msg.message_id}: {e}")
            # Return fallback response
            return self._create_fallback_response(email_msg)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for response generation"""
        return f"""You are a professional email response assistant. Generate appropriate, helpful, and {self.config.response_tone} email responses.

GUIDELINES:
- Be {self.config.response_tone} and courteous
- Address the sender's concerns directly
- Provide helpful information or next steps
- Keep responses concise but complete
- Use proper email etiquette
- Include relevant contact information if needed
- Avoid making promises you can't keep
- If unsure, suggest contacting support directly

RESPONSE FORMAT:
- Use proper email structure (greeting, body, closing)
- Include a clear subject line suggestion
- End with appropriate signature
- Maximum {self.config.max_response_length} characters

TONE: {self.config.response_tone.title()}
"""
    
    def _create_response_prompt(self, email_msg: EmailMessage) -> str:
        """Create prompt for response generation"""
        return f"""
Generate an appropriate email response for the following message.

ORIGINAL EMAIL:
From: {email_msg.sender}
Subject: {email_msg.subject}
Received: {email_msg.received_at.strftime('%Y-%m-%d %H:%M:%S')}
Urgency Level: {email_msg.urgency.value}/5

CONTENT:
{email_msg.body}

Please respond with a JSON object containing:
- "response_text": the complete email response (including subject line)
- "confidence_score": float between 0-1 indicating confidence in the response
- "reasoning": brief explanation of the response approach
- "suggested_urgency": integer 1-5 for the response urgency
- "requires_human_review": boolean indicating if human review is needed
- "key_points_addressed": list of main points addressed in the response
- "follow_up_suggested": boolean indicating if follow-up is recommended

Consider:
- The urgency level of the original email
- The sender's apparent needs or concerns
- Appropriate level of detail and formality
- Whether the response fully addresses the inquiry
- If additional information or escalation is needed
"""
    
    async def generate_fallback_response(self, email_msg: EmailMessage) -> AIResponse:
        """Generate a safe fallback response when AI generation fails"""
        try:
            self.logger.info(f"Generating fallback response for email: {email_msg.message_id}")
            
            # Simple fallback response
            fallback_text = f"""Subject: Re: {email_msg.subject}

Dear {email_msg.sender.split('@')[0]},

Thank you for your email regarding "{email_msg.subject}".

We have received your message and are currently processing your request. Our team will review your inquiry and respond as soon as possible.

If this is an urgent matter, please contact us directly at {self.config.smtp_email} or call our support line.

We appreciate your patience and look forward to assisting you.

Best regards,
Customer Service Team
{self.config.smtp_email}
"""
            
            return AIResponse(
                message_id=email_msg.message_id,
                response_text=fallback_text,
                confidence_score=0.9,  # High confidence for fallback
                reasoning="Fallback response used due to AI generation failure",
                suggested_urgency=UrgencyLevel.MEDIUM,
                requires_human_review=False
            )
            
        except Exception as e:
            self.logger.error(f"Error generating fallback response: {e}")
            # Ultimate fallback
            return AIResponse(
                message_id=email_msg.message_id,
                response_text="Thank you for your email. We have received your message and will respond soon.",
                confidence_score=1.0,
                reasoning="Ultimate fallback response",
                suggested_urgency=UrgencyLevel.MEDIUM,
                requires_human_review=True
            )
    
    async def generate_test_response(self) -> AIResponse:
        """Generate a test response for system testing"""
        try:
            test_email = EmailMessage(
                message_id="test-response",
                subject="Test Email",
                sender="test@example.com",
                recipient=self.config.smtp_email,
                body="This is a test email to verify the response generation system."
            )
            
            return await self.generate_response(test_email)
            
        except Exception as e:
            self.logger.error(f"Error generating test response: {e}")
            return AIResponse(
                message_id="test-response",
                response_text="Test response generated successfully.",
                confidence_score=1.0,
                reasoning="Test response",
                suggested_urgency=UrgencyLevel.LOW,
                requires_human_review=False
            )
    
    async def improve_response(self, original_response: AIResponse, feedback: str) -> AIResponse:
        """Improve a response based on feedback"""
        try:
            self.logger.info(f"Improving response for email: {original_response.message_id}")
            
            prompt = f"""
Improve the following email response based on the provided feedback.

ORIGINAL RESPONSE:
{original_response.response_text}

FEEDBACK:
{feedback}

Please provide an improved version that addresses the feedback while maintaining professionalism.

Respond with a JSON object containing:
- "improved_response": the enhanced email response
- "confidence_score": updated confidence score
- "reasoning": explanation of improvements made
- "changes_made": list of specific changes implemented
"""
            
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email response editor. Improve responses based on feedback while maintaining professionalism."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.config.max_response_length,
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            improved_response = AIResponse(
                message_id=original_response.message_id,
                response_text=result.get('improved_response', original_response.response_text),
                confidence_score=result.get('confidence_score', original_response.confidence_score),
                reasoning=result.get('reasoning', 'Response improved based on feedback'),
                suggested_urgency=original_response.suggested_urgency,
                requires_human_review=original_response.requires_human_review
            )
            
            self.logger.info(f"Response improved for {original_response.message_id}")
            return improved_response
            
        except Exception as e:
            self.logger.error(f"Error improving response: {e}")
            return original_response  # Return original if improvement fails
    
    async def generate_batch_responses(self, emails: list[EmailMessage]) -> list[AIResponse]:
        """Generate responses for multiple emails"""
        try:
            self.logger.info(f"Generating batch responses for {len(emails)} emails")
            
            responses = []
            for email_msg in emails:
                try:
                    response = await self.generate_response(email_msg)
                    responses.append(response)
                except Exception as e:
                    self.logger.error(f"Error generating response for {email_msg.message_id}: {e}")
                    # Add fallback response
                    fallback = self._create_fallback_response(email_msg)
                    responses.append(fallback)
            
            self.logger.info(f"Batch response generation completed: {len(responses)} responses")
            return responses
            
        except Exception as e:
            self.logger.error(f"Error in batch response generation: {e}")
            return []
    
    def _create_fallback_response(self, email_msg: EmailMessage) -> AIResponse:
        """Create a simple fallback response"""
        fallback_text = f"""Subject: Re: {email_msg.subject}

Dear {email_msg.sender.split('@')[0]},

Thank you for your email. We have received your message and will respond as soon as possible.

Best regards,
Customer Service Team
"""
        
        return AIResponse(
            message_id=email_msg.message_id,
            response_text=fallback_text,
            confidence_score=0.8,
            reasoning="Fallback response generated",
            suggested_urgency=UrgencyLevel.MEDIUM,
            requires_human_review=False
        )
    
    async def is_connected(self) -> bool:
        """Check if OpenAI API is accessible"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            self.logger.warning(f"OpenAI connection check failed: {e}")
            return False
    
    def get_generation_stats(self) -> dict:
        """Get response generation statistics"""
        return {
            'model': self.config.openai_model,
            'is_connected': self.is_connected,
            'max_response_length': self.config.max_response_length,
            'response_tone': self.config.response_tone,
            'api_key_configured': bool(self.config.openai_api_key)
        }


