# Email Automation System

A production-ready, AI-powered email automation system that intelligently processes incoming emails, classifies urgency, generates responses, and routes to human agents when needed.

## 🚀 Features

- **AI-Powered Email Classification**: Uses OpenAI GPT-4o to analyze email urgency (1-5 scale)
- **Intelligent Response Generation**: Automatically generates contextual email responses
- **Smart Routing**: Routes urgent emails to human agents with timeout handling
- **Approval Workflow**: Google Chat integration for human approval of AI responses
- **Real-time Dashboard**: Web-based monitoring and control interface
- **Production Ready**: Docker, systemd, and comprehensive security features
- **WebSocket Support**: Real-time updates and notifications

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
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
                          └──────────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Redis (optional, for state management)
- OpenAI API key
- Gmail/IMAP account with app password
- Google Chat webhook URL
- Docker (for containerized deployment)

## 🛠️ Installation

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd email-automation-system
   ```

2. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboard**
   - Open http://localhost in your browser
   - Configure your email settings through the web interface

### Option 2: Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

3. **Run the application**
   ```bash
   python server.py
   ```

### Option 3: Production Deployment

1. **Run the deployment script**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Configure your settings**
   ```bash
   sudo nano /opt/email-automation/.env
   sudo systemctl restart email-automation
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# IMAP Configuration (Email Receiving)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=your-email@domain.com
IMAP_PASSWORD=your-app-password-here
IMAP_CHECK_INTERVAL=30

# SMTP Configuration (Email Sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@domain.com
SMTP_PASSWORD=your-app-password-here

# Google Chat Configuration
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/your-space-id/messages

# System Configuration
LOG_LEVEL=INFO
URGENT_TIMEOUT_MINUTES=10
```

### Gmail Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Use the app password** in your configuration

### Google Chat Setup

1. **Create a Google Chat space**
2. **Add a webhook**:
   - Go to space settings
   - Add webhook
   - Copy the webhook URL
3. **Configure the webhook URL** in your environment

## 🎯 Usage

### Web Dashboard

1. **Access the dashboard** at http://localhost:8000
2. **Configure settings** through the Settings modal
3. **Test connections** to verify all services
4. **Start the system** using the Start/Stop button
5. **Monitor activity** in real-time

### API Endpoints

- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `POST /api/system/start` - Start the system
- `POST /api/system/stop` - Stop the system
- `GET /api/system/status` - Get system status
- `GET /api/stats` - Get processing statistics
- `POST /api/test-connections` - Test all connections
- `GET /api/logs` - Get system logs

### WebSocket Events

- `status_update` - System status changes
- `stats_update` - Statistics updates
- `activity` - New activity events
- `log` - New log entries

## 🔒 Security Features

- **Input Validation**: Comprehensive validation for all inputs
- **Rate Limiting**: Protection against abuse
- **IP Filtering**: Block/allow specific IP addresses
- **Encryption**: Sensitive data encryption at rest
- **JWT Authentication**: Secure API access
- **Security Auditing**: Comprehensive security event logging
- **HTTPS Support**: SSL/TLS encryption in transit

## 📊 Monitoring

### System Metrics

- Emails processed
- AI responses generated
- Human escalations
- Success rate
- Response times
- Error counts

### Logs

- Application logs: `email_automation.log`
- System logs: `journalctl -u email-automation`
- Docker logs: `docker-compose logs -f`

### Health Checks

- System status endpoint: `/api/system/status`
- Health check: `/health`
- Connection tests available in dashboard

## 🚨 Troubleshooting

### Common Issues

1. **IMAP Connection Failed**
   - Verify Gmail app password
   - Check IMAP settings
   - Ensure 2FA is enabled

2. **OpenAI API Errors**
   - Verify API key
   - Check API quota
   - Monitor rate limits

3. **Google Chat Not Working**
   - Verify webhook URL
   - Check space permissions
   - Test webhook manually

4. **SMTP Sending Failed**
   - Verify SMTP credentials
   - Check firewall settings
   - Test with telnet

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

### Manual Testing

Test individual components:
```bash
python -c "from config import load_config; print('Config loaded successfully')"
python -c "from imap_listener import IMAPListener; print('IMAP module loaded')"
```

## 🔧 Development

### Project Structure

```
email-automation-system/
├── server.py                 # FastAPI server
├── email_processor.py        # Main orchestrator
├── imap_listener.py         # Email monitoring
├── urgency_classifier.py    # AI urgency classification
├── response_generator.py    # AI response generation
├── google_chat_handler.py   # Chat notifications
├── email_sender.py          # SMTP sending
├── config.py               # Configuration management
├── models.py               # Data models
├── security.py             # Security utilities
├── index.html              # Web dashboard
├── app.js                  # Frontend JavaScript
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-service setup
├── nginx.conf             # Reverse proxy config
└── deploy.sh              # Production deployment
```

### Adding New Features

1. **Create new module** in appropriate file
2. **Add tests** for new functionality
3. **Update API endpoints** if needed
4. **Update documentation**
5. **Test thoroughly** before deployment

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings
- Write tests for new features
- Use logging instead of print statements

## 📈 Performance

### Optimization Tips

1. **Redis Caching**: Enable Redis for better performance
2. **Connection Pooling**: Reuse database connections
3. **Batch Processing**: Process multiple emails together
4. **Rate Limiting**: Respect API rate limits
5. **Monitoring**: Monitor system performance

### Scaling

- **Horizontal Scaling**: Run multiple instances behind load balancer
- **Database**: Use PostgreSQL for production
- **Caching**: Implement Redis for session management
- **Queue**: Use Celery for background tasks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Use GitHub discussions for questions
- **Email**: Contact support@your-domain.com

## 🔄 Updates

### Version 1.0.0
- Initial release
- Core email automation functionality
- Web dashboard
- Docker support
- Production deployment scripts

### Roadmap
- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Custom AI models
- [ ] Mobile app
- [ ] Enterprise features

---

**Made with ❤️ for efficient email management**


