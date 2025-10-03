# Email Automation System - Windows Quick Start

## 🚀 Super Easy Setup (3 Steps)

### Step 1: Install Python 3.11
- Download from https://python.org/downloads/
- **Important**: Check "Add Python to PATH" during installation

### Step 2: Run Setup
- Double-click `setup.bat`
- Follow the prompts to configure your `.env` file

### Step 3: Start the App
- Double-click `start_app.bat`
- Your browser will open automatically to http://localhost:8000

## 📋 What You Need

### Required Accounts & Keys:
1. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
2. **Gmail Account** - With app password enabled
3. **Google Chat Space** - With webhook configured

### Gmail Setup:
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Create password for "Mail"
3. Use the app password (not your regular password) in the configuration

### Google Chat Setup:
1. Create a Google Chat space
2. Add webhook:
   - Click space name → Manage webhooks
   - Add webhook → Copy the URL
3. Use this URL in your configuration

## 🔧 Configuration

When you run `setup.bat`, it will create a `.env` file with these key settings:

```env
# Required - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-key-here

# Required - Your Gmail with app password
IMAP_EMAIL=your-email@gmail.com
IMAP_PASSWORD=your-gmail-app-password
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Required - Google Chat webhook
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/your-space/messages
```

## 🎯 Using the App

1. **Start**: Double-click `start_app.bat`
2. **Configure**: Go to Settings (gear icon) in the web interface
3. **Test**: Click "Test Connections" to verify everything works
4. **Start**: Click "Start System" to begin processing emails

## 🆘 Troubleshooting

### "Python 3.11 not found"
- Install Python 3.11 from python.org
- Make sure "Add Python to PATH" is checked during installation

### "Module not found" errors
- Run `setup.bat` again to reinstall dependencies

### Gmail connection fails
- Use app password, not regular password
- Enable 2FA on your Gmail account
- Check IMAP is enabled in Gmail settings

### OpenAI errors
- Verify API key starts with `sk-`
- Check you have credits/quota available

## 📁 Files

- `start_app.bat` - Starts the application
- `setup.bat` - Initial setup and dependency installation
- `.env` - Your configuration (created after setup)
- `index.html` - Web interface (opens automatically)

## 🔄 Updates

To update the app:
1. Download new files
2. Run `setup.bat` again
3. Your `.env` configuration will be preserved

---

**That's it! Your email automation system is ready to go!** 🎉





