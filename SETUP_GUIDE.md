# Email Automation System - Quick Setup Guide

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites
- Python 3.11+ installed
- OpenAI API key
- Gmail account with app password
- Google Chat webhook URL

### 2. Installation
```bash
# Clone or download the project files
# Navigate to the project directory

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp env.template .env
```

### 3. Configuration
Edit the `.env` file with your credentials:

```env
# Required: OpenAI API Key
OPENAI_API_KEY=sk-your-actual-openai-key

# Required: Gmail IMAP (receiving emails)
IMAP_EMAIL=your-email@gmail.com
IMAP_PASSWORD=your-gmail-app-password

# Required: Gmail SMTP (sending emails)  
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Required: Google Chat webhook
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/your-space/messages
```

### 4. Run the System
```bash
# Start the server
python server.py

# Open your browser to:
# http://localhost:8000
```

### 5. Configure via Web Interface
1. Click the **Settings** button (gear icon)
2. Fill in all your email credentials
3. Click **Test Connections** to verify
4. Click **Save Configuration**
5. Click **Start System** to begin processing emails

## 📧 Gmail Setup

### Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Go to App passwords
4. Generate password for "Mail"
5. Use this password in your configuration

## 💬 Google Chat Setup

### Create Webhook
1. Create a new Google Chat space
2. Click the space name → Manage webhooks
3. Add webhook → Copy the URL
4. Use this URL in your configuration

## 🐳 Docker Deployment

### Quick Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost
```

### Production Docker
```bash
# Build production image
docker build -t email-automation .

# Run with environment file
docker run -d \
  --name email-automation \
  -p 8000:8000 \
  --env-file .env \
  email-automation
```

## 🔧 Production Deployment

### Automated Deployment
```bash
# Make script executable
chmod +x deploy.sh

# Run deployment (requires sudo)
./deploy.sh
```

### Manual Production Setup
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3 python3-pip nginx redis-server

# Setup application
sudo mkdir -p /opt/email-automation
sudo cp -r . /opt/email-automation/
sudo chown -R www-data:www-data /opt/email-automation

# Install Python dependencies
cd /opt/email-automation
sudo pip3 install -r requirements.txt

# Setup systemd service
sudo cp systemd/email-automation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable email-automation
sudo systemctl start email-automation

# Setup Nginx
sudo cp nginx.conf /etc/nginx/sites-available/email-automation
sudo ln -s /etc/nginx/sites-available/email-automation /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 🔍 Testing

### Test Individual Components
```bash
# Test configuration loading
python -c "from config import load_config; print('Config OK')"

# Test IMAP connection
python -c "from imap_listener import IMAPListener; from config import load_config; print('IMAP OK')"

# Test OpenAI connection
python -c "from urgency_classifier import UrgencyClassifier; from config import load_config; print('OpenAI OK')"
```

### Test via Web Interface
1. Go to Settings → Test Connections
2. Verify all services show ✅ Connected
3. Send a test email to your configured address
4. Check the dashboard for processing activity

## 🚨 Troubleshooting

### Common Issues

**IMAP Connection Failed**
- Verify Gmail app password (not regular password)
- Ensure 2FA is enabled
- Check IMAP is enabled in Gmail settings

**OpenAI API Errors**
- Verify API key starts with `sk-`
- Check API quota and billing
- Ensure model `gpt-4o` is available

**Google Chat Not Working**
- Verify webhook URL is correct
- Test webhook manually with curl
- Check space permissions

**SMTP Sending Failed**
- Use Gmail app password
- Check firewall/port 587 access
- Verify SMTP settings

### Debug Mode
```env
LOG_LEVEL=DEBUG
```

### View Logs
```bash
# Application logs
tail -f email_automation.log

# System logs (if using systemd)
sudo journalctl -u email-automation -f

# Docker logs
docker-compose logs -f
```

## 📊 Monitoring

### Dashboard Features
- Real-time system status
- Email processing statistics
- Connection health monitoring
- Activity feed
- System logs viewer

### API Endpoints
- `GET /api/system/status` - System health
- `GET /api/stats` - Processing statistics
- `GET /api/logs` - System logs
- `POST /api/test-connections` - Test all services

## 🔒 Security

### Built-in Security Features
- Input validation and sanitization
- Rate limiting protection
- IP filtering capabilities
- Encrypted credential storage
- Security event logging
- HTTPS support

### Production Security Checklist
- [ ] Use strong passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup configuration

## 📈 Performance

### Optimization Tips
- Use Redis for caching (optional)
- Monitor API rate limits
- Adjust email check interval
- Use connection pooling
- Monitor system resources

### Scaling
- Run multiple instances behind load balancer
- Use external Redis instance
- Implement database for state persistence
- Use message queues for high volume

## 🆘 Support

### Getting Help
1. Check this setup guide
2. Review the main README.md
3. Check system logs for errors
4. Test individual components
5. Verify all credentials are correct

### Useful Commands
```bash
# Check system status
curl http://localhost:8000/api/system/status

# View recent logs
tail -n 50 email_automation.log

# Restart service (systemd)
sudo systemctl restart email-automation

# Restart Docker containers
docker-compose restart
```

---

**🎉 You're all set! Your email automation system is ready to process emails intelligently.**


