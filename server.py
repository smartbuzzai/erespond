#!/usr/bin/env python3
"""
Email Automation System - Backend Server
Production-ready FastAPI server with WebSocket support
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import websockets

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from email_processor import EmailProcessor
from config import Config, load_config
from models import EmailMessage, UrgencyLevel, ResponseType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Email Automation System",
    description="AI-powered email response system with intelligent routing",
    version="1.0.0"
)

# CORS middleware
app.middleware("http")(CORSMiddleware(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
))

# Global state
email_processor: Optional[EmailProcessor] = None
config: Optional[Config] = None
connected_clients: set = set()
system_stats = {
    "emails_processed": 0,
    "ai_responses": 0,
    "human_escalations": 0,
    "success_rate": 0,
    "last_updated": datetime.now().isoformat()
}

# Pydantic models for API
class ConfigRequest(BaseModel):
    # IMAP settings
    imap_host: str = Field(..., description="IMAP server host")
    imap_port: int = Field(993, description="IMAP server port")
    imap_email: str = Field(..., description="IMAP email address")
    imap_password: str = Field(..., description="IMAP password or app password")
    imap_check_interval: int = Field(30, description="Email check interval in seconds")
    
    # SMTP settings
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(587, description="SMTP server port")
    smtp_email: str = Field(..., description="SMTP email address")
    smtp_password: str = Field(..., description="SMTP password or app password")
    
    # OpenAI settings
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field("gpt-4o", description="OpenAI model to use")
    urgent_timeout_minutes: int = Field(10, description="Timeout for urgent email handling")
    
    # Google Chat settings
    google_chat_webhook_url: str = Field(..., description="Google Chat webhook URL")
    google_chat_oauth_client_id: Optional[str] = Field(None, description="OAuth client ID")
    google_chat_oauth_client_secret: Optional[str] = Field(None, description="OAuth client secret")
    
    # System settings
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[str] = Field("email_automation.log", description="Log file path")
    redis_url: Optional[str] = Field(None, description="Redis connection URL")

class TestConnectionsRequest(BaseModel):
    imap_host: str
    imap_port: int
    imap_email: str
    imap_password: str
    smtp_host: str
    smtp_port: int
    smtp_email: str
    smtp_password: str
    openai_api_key: str
    google_chat_webhook_url: str

class ConnectionTestResult(BaseModel):
    success: bool
    error: Optional[str] = None

class SystemStatus(BaseModel):
    is_running: bool
    imap: bool
    smtp: bool
    openai: bool
    google_chat: bool
    last_check: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# API Routes

@app.get("/")
async def serve_index():
    """Serve the main dashboard page"""
    return FileResponse("index.html")

@app.get("/api/config")
async def get_config():
    """Get current system configuration"""
    try:
        if config:
            # Return config without sensitive data
            config_dict = config.dict()
            # Mask sensitive fields
            for field in ['imap_password', 'smtp_password', 'openai_api_key', 'google_chat_oauth_client_secret']:
                if field in config_dict and config_dict[field]:
                    config_dict[field] = "***masked***"
            return config_dict
        else:
            return {"error": "Configuration not loaded"}
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def save_config(config_request: ConfigRequest):
    """Save system configuration"""
    try:
        global config
        
        # Create new config object
        new_config = Config(**config_request.dict())
        
        # Save to environment file
        env_file = Path(".env")
        env_content = []
        
        # Add all configuration to .env file
        for field, value in config_request.dict().items():
            if value is not None:
                env_content.append(f"{field.upper()}={value}")
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(env_content))
        
        # Update global config
        config = new_config
        
        # Restart email processor if running
        if email_processor and email_processor.is_running:
            await email_processor.stop()
            email_processor = EmailProcessor(config)
            await email_processor.start()
        
        logger.info("Configuration saved successfully")
        return {"message": "Configuration saved successfully"}
        
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-connections")
async def test_connections(request: TestConnectionsRequest):
    """Test all external connections"""
    try:
        results = {}
        
        # Test IMAP connection
        try:
            from imap_listener import IMAPListener
            test_config = Config(
                imap_host=request.imap_host,
                imap_port=request.imap_port,
                imap_email=request.imap_email,
                imap_password=request.imap_password,
                smtp_host=request.smtp_host,
                smtp_port=request.smtp_port,
                smtp_email=request.smtp_email,
                smtp_password=request.smtp_password,
                openai_api_key=request.openai_api_key,
                google_chat_webhook_url=request.google_chat_webhook_url
            )
            
            imap_listener = IMAPListener(test_config)
            await imap_listener.test_connection()
            results["imap"] = ConnectionTestResult(success=True)
        except Exception as e:
            results["imap"] = ConnectionTestResult(success=False, error=str(e))
        
        # Test SMTP connection
        try:
            from email_sender import EmailSender
            email_sender = EmailSender(test_config)
            await email_sender.test_connection()
            results["smtp"] = ConnectionTestResult(success=True)
        except Exception as e:
            results["smtp"] = ConnectionTestResult(success=False, error=str(e))
        
        # Test OpenAI connection
        try:
            from urgency_classifier import UrgencyClassifier
            classifier = UrgencyClassifier(test_config)
            await classifier.test_connection()
            results["openai"] = ConnectionTestResult(success=True)
        except Exception as e:
            results["openai"] = ConnectionTestResult(success=False, error=str(e))
        
        # Test Google Chat connection
        try:
            from google_chat_handler import GoogleChatHandler
            chat_handler = GoogleChatHandler(test_config)
            await chat_handler.test_connection()
            results["google_chat"] = ConnectionTestResult(success=True)
        except Exception as e:
            results["google_chat"] = ConnectionTestResult(success=False, error=str(e))
        
        # Overall result
        results["all_success"] = all(result.success for result in results.values() if isinstance(result, ConnectionTestResult))
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/start")
async def start_system():
    """Start the email automation system"""
    try:
        global email_processor, config
        
        if not config:
            raise HTTPException(status_code=400, detail="Configuration not loaded")
        
        if email_processor and email_processor.is_running:
            return {"message": "System is already running"}
        
        # Create and start email processor
        email_processor = EmailProcessor(config)
        await email_processor.start()
        
        # Start background task for status updates
        asyncio.create_task(status_update_task())
        
        logger.info("Email automation system started")
        return {"message": "System started successfully"}
        
    except Exception as e:
        logger.error(f"Error starting system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system/stop")
async def stop_system():
    """Stop the email automation system"""
    try:
        global email_processor
        
        if not email_processor or not email_processor.is_running:
            return {"message": "System is not running"}
        
        await email_processor.stop()
        email_processor = None
        
        logger.info("Email automation system stopped")
        return {"message": "System stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
async def get_system_status():
    """Get current system status"""
    try:
        if not email_processor:
            return SystemStatus(
                is_running=False,
                imap=False,
                smtp=False,
                openai=False,
                google_chat=False,
                last_check=datetime.now().isoformat()
            )
        
        status = await email_processor.get_status()
        return SystemStatus(
            is_running=email_processor.is_running,
            imap=status.get("imap", False),
            smtp=status.get("smtp", False),
            openai=status.get("openai", False),
            google_chat=status.get("google_chat", False),
            last_check=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return system_stats

@app.post("/api/test-email")
async def test_email():
    """Test email sending functionality"""
    try:
        if not email_processor:
            raise HTTPException(status_code=400, detail="System not running")
        
        # Send test email
        result = await email_processor.send_test_email()
        return {"success": result, "message": "Test email sent successfully" if result else "Failed to send test email"}
        
    except Exception as e:
        logger.error(f"Error testing email: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/logs")
async def get_logs():
    """Get system logs"""
    try:
        log_file = Path("email_automation.log")
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = f.read()
            return logs
        else:
            return "No logs available"
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return f"Error reading logs: {e}"

@app.get("/api/config/export")
async def export_config():
    """Export configuration as JSON file"""
    try:
        if not config:
            raise HTTPException(status_code=400, detail="Configuration not loaded")
        
        # Create export data (masked sensitive fields)
        export_data = config.dict()
        for field in ['imap_password', 'smtp_password', 'openai_api_key', 'google_chat_oauth_client_secret']:
            if field in export_data and export_data[field]:
                export_data[field] = "***masked***"
        
        return JSONResponse(
            content=export_data,
            headers={"Content-Disposition": "attachment; filename=email-automation-config.json"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background tasks
async def status_update_task():
    """Background task to send status updates via WebSocket"""
    while True:
        try:
            if email_processor and email_processor.is_running:
                status = await email_processor.get_status()
                message = {
                    "type": "status_update",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
                await manager.broadcast(json.dumps(message))
            
            # Update stats
            stats_message = {
                "type": "stats_update",
                "stats": system_stats,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast(json.dumps(stats_message))
            
            await asyncio.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error in status update task: {e}")
            await asyncio.sleep(10)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global config
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Create email processor (but don't start it yet)
        if config:
            global email_processor
            email_processor = EmailProcessor(config)
            logger.info("Email processor initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global email_processor
    if email_processor and email_processor.is_running:
        await email_processor.stop()
        logger.info("Email processor stopped during shutdown")

# Mount static files
app.mount("/static", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
