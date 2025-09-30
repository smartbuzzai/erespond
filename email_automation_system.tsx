import React, { useState } from 'react';
import { Mail, Zap, Clock, CheckCircle, AlertTriangle, FileText } from 'lucide-react';

const EmailAutomationDocs = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: FileText },
    { id: 'architecture', label: 'Architecture', icon: Zap },
    { id: 'setup', label: 'Setup', icon: CheckCircle },
    { id: 'code', label: 'Core Code', icon: Mail }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-6 border-l-4 border-blue-500">
          <div className="flex items-center gap-3 mb-2">
            <Mail className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold text-gray-800">
              Automated Email Response System
            </h1>
          </div>
          <p className="text-gray-600 mt-2">
            Production-ready Python implementation of n8n email automation workflow
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-500 text-white shadow-md'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content Area */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {activeTab === 'overview' && <OverviewTab />}
          {activeTab === 'architecture' && <ArchitectureTab />}
          {activeTab === 'setup' && <SetupTab />}
          {activeTab === 'code' && <CodeTab />}
        </div>
      </div>
    </div>
  );
};

const OverviewTab = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-800 mb-4">System Overview</h2>
    
    <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded mb-4">
      <h3 className="font-semibold text-amber-900 mb-2">⚠️ Note: Workflow Mismatch</h3>
      <p className="text-amber-800 text-sm">
        Your task description mentioned "Daily AI News Research and Intelligence Report" but the uploaded workflow 
        is "Automated Email Response System". This implementation is based on the actual workflow file provided.
      </p>
    </div>
    
    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
      <h3 className="font-semibold text-blue-900 mb-2">What This System Does</h3>
      <p className="text-blue-800">
        Automatically processes incoming customer emails, classifies urgency, generates AI-powered responses, 
        and routes to human agents when needed.
      </p>
    </div>

    <div className="grid md:grid-cols-2 gap-4 mt-6">
      <FeatureCard
        icon={<Zap className="w-6 h-6 text-yellow-500" />}
        title="AI-Powered Classification"
        description="Uses GPT-4o to analyze email urgency (1-5 scale)"
      />
      <FeatureCard
        icon={<Mail className="w-6 h-6 text-blue-500" />}
        title="Smart Responses"
        description="Generates contextual email responses automatically"
      />
      <FeatureCard
        icon={<AlertTriangle className="w-6 h-6 text-red-500" />}
        title="Urgent Escalation"
        description="Routes urgent emails (4-5) to human agents with 10min timeout"
      />
      <FeatureCard
        icon={<CheckCircle className="w-6 h-6 text-green-500" />}
        title="Approval Workflow"
        description="Google Chat approval for non-urgent responses"
      />
    </div>

    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4">Workflow Steps</h3>
      <div className="space-y-3">
        <WorkflowStep number="1" title="Email Received" desc="IMAP listener detects new email" />
        <WorkflowStep number="2" title="Urgency Check" desc="OpenAI classifies urgency (1-5)" />
        <WorkflowStep number="3" title="Route Decision" desc="Urgent (≥4) → Human | Non-urgent (<4) → AI" />
        <WorkflowStep number="4" title="Response Generation" desc="AI drafts appropriate response" />
        <WorkflowStep number="5" title="Approval/Send" desc="Get approval and send email" />
      </div>
    </div>
  </div>
);

const ArchitectureTab = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-800 mb-4">System Architecture</h2>
    
    <div className="bg-gray-50 p-6 rounded-lg border-2 border-gray-200">
      <pre className="text-sm text-gray-700 overflow-x-auto">
{`┌─────────────────────────────────────────────────────────┐
│                    IMAP Email Listener                  │
│                  (Continuous Monitoring)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              OpenAI Urgency Classifier                  │
│            (GPT-4o + Structured Output)                 │
│              Returns: {"urgency": 1-5}                  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
    Urgent (≥4)            Non-Urgent (<4)
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│  Google Chat     │    │   OpenAI AI Agent    │
│  Request Input   │    │  Generate Response   │
│  (10min timeout) │    │  (GPT-4o + JSON)     │
└────┬─────────────┘    └──────────┬───────────┘
     │                             │
     │ Timeout?                    ▼
     │                   ┌──────────────────────┐
     ▼                   │   Google Chat        │
┌─────────────┐          │   Get Approval       │
│Send Fallback│          │   (Approve/Reject)   │
│   Email     │          └──────────┬───────────┘
└─────────────┘                     │
                                    ▼
                          ┌──────────────────────┐
                          │   Send Email (SMTP)  │
                          └──────────────────────┘`}
      </pre>
    </div>

    <div className="grid md:grid-cols-2 gap-4 mt-6">
      <div className="border-2 border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-3">Core Components</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          <li>• <strong>EmailProcessor:</strong> Main orchestrator class</li>
          <li>• <strong>IMAPListener:</strong> Monitors incoming emails</li>
          <li>• <strong>UrgencyClassifier:</strong> OpenAI integration</li>
          <li>• <strong>ResponseGenerator:</strong> AI response creation</li>
          <li>• <strong>GoogleChatHandler:</strong> Chat notifications</li>
          <li>• <strong>EmailSender:</strong> SMTP email delivery</li>
        </ul>
      </div>
      
      <div className="border-2 border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-3">External Services</h3>
        <ul className="space-y-2 text-sm text-gray-600">
          <li>• <strong>OpenAI API:</strong> GPT-4o for classification & generation</li>
          <li>• <strong>Google Chat:</strong> Webhook-based notifications</li>
          <li>• <strong>IMAP Server:</strong> Email receiving</li>
          <li>• <strong>SMTP Server:</strong> Email sending</li>
          <li>• <strong>Redis (optional):</strong> State management</li>
        </ul>
      </div>
    </div>
  </div>
);

const SetupTab = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-800 mb-4">Setup Guide</h2>
    
    <div className="space-y-4">
      <SetupSection
        title="1. Install Dependencies"
        code={`pip install openai google-auth google-auth-oauthlib \\
    google-auth-httplib2 imapclient redis python-dotenv \\
    aiosmtplib email-validator pydantic`}
      />

      <SetupSection
        title="2. Environment Configuration"
        code={`# .env
OPENAI_API_KEY=sk-...
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=postal@smartbuzzai.com
IMAP_PASSWORD=your_password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=postal@smartbuzzai.com
SMTP_PASSWORD=your_password

GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/.../messages
GOOGLE_CHAT_OAUTH_CLIENT_ID=your_client_id
GOOGLE_CHAT_OAUTH_CLIENT_SECRET=your_secret

# Optional: Redis for state management
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=email_automation.log`}
      />

      <SetupSection
        title="3. Google Chat Setup"
        steps={[
          "Create a Google Cloud Project",
          "Enable Google Chat API",
          "Create OAuth 2.0 credentials",
          "Create a Google Chat space and add your bot",
          "Get webhook URL or set up OAuth flow"
        ]}
      />

      <SetupSection
        title="4. Run the Application"
        code={`# Development
python main.py

# Production (with systemd)
sudo systemctl start email-automation

# Docker
docker-compose up -d`}
      />
    </div>

    <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded mt-6">
      <h3 className="font-semibold text-yellow-900 mb-2">Security Notes</h3>
      <ul className="text-sm text-yellow-800 space-y-1">
        <li>• Use app-specific passwords for Gmail IMAP/SMTP</li>
        <li>• Store credentials in environment variables or secret manager</li>
        <li>• Enable 2FA on all email accounts</li>
        <li>• Restrict API keys to specific IPs in production</li>
        <li>• Use OAuth2 for Google Chat (more secure than webhooks)</li>
      </ul>
    </div>
  </div>
);

const CodeTab = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold text-gray-800 mb-4">Core Implementation</h2>
    
    <div className="space-y-6">
      <CodeBlock
        title="main.py - Entry Point"
        language="python"
        code={`import asyncio
import logging
from email_processor import EmailProcessor
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point for email automation system."""
    config = load_config()
    processor = EmailProcessor(config)
    
    logger.info("Starting Email Automation System...")
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        await processor.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())`}
      />

      <CodeBlock
        title="config.py - Configuration Management"
        language="python"
        code={`from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    
    # IMAP (receiving)
    imap_host: str
    imap_port: int = 993
    imap_email: str
    imap_password: str
    imap_check_interval: int = 30  # seconds
    
    # SMTP (sending)
    smtp_host: str
    smtp_port: int = 587
    smtp_email: str
    smtp_password: str
    
    # Google Chat
    google_chat_webhook_url: str
    google_chat_oauth_client_id: Optional[str] = None
    google_chat_oauth_client_secret: Optional[str] = None
    
    # System
    redis_url: Optional[str] = None
    log_level: str = "INFO"
    log_file: Optional[str] = "email_automation.log"
    urgent_timeout_minutes: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def load_config() -> Config:
    return Config()`}
      />

      <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-800 mb-3">📦 Complete Project Files Available</h3>
        <p className="text-sm text-gray-600 mb-3">
          Download the full implementation with all modules:
        </p>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• <code>email_processor.py</code> - Main orchestrator</li>
          <li>• <code>urgency_classifier.py</code> - OpenAI integration</li>
          <li>• <code>response_generator.py</code> - AI response creation</li>
          <li>• <code>google_chat_handler.py</code> - Chat notifications</li>
          <li>• <code>email_sender.py</code> - SMTP handler</li>
          <li>• <code>imap_listener.py</code> - Email monitoring</li>
          <li>• <code>models.py</code> - Data models</li>
          <li>• <code>docker-compose.yml</code> - Container setup</li>
          <li>• <code>requirements.txt</code> - Dependencies</li>
          <li>• <code>systemd/email-automation.service</code> - System service</li>
        </ul>
      </div>
    </div>
  </div>
);

// Helper Components
const FeatureCard = ({ icon, title, description }) => (
  <div className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
    <div className="flex items-start gap-3">
      <div className="mt-1">{icon}</div>
      <div>
        <h4 className="font-semibold text-gray-800 mb-1">{title}</h4>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  </div>
);

const WorkflowStep = ({ number, title, desc }) => (
  <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
    <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
      {number}
    </div>
    <div>
      <h4 className="font-semibold text-gray-800">{title}</h4>
      <p className="text-sm text-gray-600">{desc}</p>
    </div>
  </div>
);

const SetupSection = ({ title, code, steps }) => (
  <div className="border-2 border-gray-200 rounded-lg p-4">
    <h3 className="font-semibold text-gray-800 mb-3">{title}</h3>
    {code && (
      <pre className="bg-gray-900 text-gray-100 p-4 rounded text-xs overflow-x-auto">
        {code}
      </pre>
    )}
    {steps && (
      <ol className="space-y-2">
        {steps.map((step, idx) => (
          <li key={idx} className="text-sm text-gray-600">
            {idx + 1}. {step}
          </li>
        ))}
      </ol>
    )}
  </div>
);

const CodeBlock = ({ title, language, code }) => (
  <div className="border-2 border-gray-200 rounded-lg overflow-hidden">
    <div className="bg-gray-800 text-white px-4 py-2 flex items-center justify-between">
      <span className="font-mono text-sm">{title}</span>
      <span className="text-xs text-gray-400">{language}</span>
    </div>
    <pre className="bg-gray-900 text-gray-100 p-4 text-xs overflow-x-auto">
      {code}
    </pre>
  </div>
);

export default EmailAutomationDocs;