#!/bin/bash

# Email Automation System - Production Deployment Script
set -e

# Configuration
APP_NAME="email-automation"
APP_USER="email-automation"
APP_DIR="/opt/email-automation"
SERVICE_NAME="email-automation"
NGINX_SITE="email-automation"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check if running on supported OS
    if [[ ! -f /etc/os-release ]]; then
        error "Cannot determine OS version"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" && "$ID" != "centos" && "$ID" != "rhel" ]]; then
        warning "This script is designed for Ubuntu/Debian/CentOS/RHEL. Proceeding anyway..."
    fi
    
    # Check for required commands
    local required_commands=("python3" "pip3" "git" "systemctl" "nginx")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command '$cmd' not found"
            exit 1
        fi
    done
    
    success "System requirements check passed"
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            build-essential \
            libssl-dev \
            libffi-dev \
            nginx \
            redis-server \
            supervisor \
            curl \
            git
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum update -y
        sudo yum install -y \
            python3 \
            python3-pip \
            python3-devel \
            gcc \
            gcc-c++ \
            openssl-devel \
            libffi-devel \
            nginx \
            redis \
            supervisor \
            curl \
            git
    else
        error "Unsupported package manager"
        exit 1
    fi
    
    success "System dependencies installed"
}

# Create application user
create_user() {
    log "Creating application user..."
    
    if ! id "$APP_USER" &>/dev/null; then
        sudo useradd --system --shell /bin/bash --home-dir "$APP_DIR" --create-home "$APP_USER"
        success "Created user: $APP_USER"
    else
        log "User $APP_USER already exists"
    fi
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    # Create directories
    sudo mkdir -p "$APP_DIR"/{logs,data,ssl}
    
    # Copy application files
    sudo cp -r . "$APP_DIR/"
    
    # Set ownership
    sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    
    # Set permissions
    sudo chmod 755 "$APP_DIR"
    sudo chmod 700 "$APP_DIR"/ssl
    
    success "Application directory setup complete"
}

# Setup Python virtual environment
setup_python_env() {
    log "Setting up Python virtual environment..."
    
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
    
    success "Python environment setup complete"
}

# Setup systemd service
setup_systemd_service() {
    log "Setting up systemd service..."
    
    # Copy service file
    sudo cp "$APP_DIR/systemd/email-automation.service" /etc/systemd/system/
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable "$SERVICE_NAME"
    
    success "Systemd service setup complete"
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    # Copy nginx configuration
    sudo cp "$APP_DIR/nginx.conf" /etc/nginx/sites-available/"$NGINX_SITE"
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/"$NGINX_SITE" /etc/nginx/sites-enabled/
    
    # Remove default site if it exists
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    sudo nginx -t
    
    # Reload nginx
    sudo systemctl reload nginx
    
    success "Nginx setup complete"
}

# Setup Redis
setup_redis() {
    log "Setting up Redis..."
    
    # Start and enable Redis
    sudo systemctl start redis
    sudo systemctl enable redis
    
    # Test Redis connection
    redis-cli ping
    
    success "Redis setup complete"
}

# Setup SSL certificates (optional)
setup_ssl() {
    log "Setting up SSL certificates..."
    
    if [[ -n "$SSL_DOMAIN" ]]; then
        # Install certbot if not present
        if ! command -v certbot &> /dev/null; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get install -y certbot python3-certbot-nginx
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot python3-certbot-nginx
            fi
        fi
        
        # Generate SSL certificate
        sudo certbot --nginx -d "$SSL_DOMAIN" --non-interactive --agree-tos --email admin@"$SSL_DOMAIN"
        
        success "SSL certificate setup complete"
    else
        warning "SSL_DOMAIN not set, skipping SSL setup"
    fi
}

# Create configuration file
create_config() {
    log "Creating configuration file..."
    
    if [[ ! -f "$APP_DIR/.env" ]]; then
        sudo -u "$APP_USER" cp "$APP_DIR/.env.template" "$APP_DIR/.env"
        warning "Please edit $APP_DIR/.env with your configuration before starting the service"
    else
        log "Configuration file already exists"
    fi
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start Redis
    sudo systemctl start redis
    
    # Start application
    sudo systemctl start "$SERVICE_NAME"
    
    # Start Nginx
    sudo systemctl start nginx
    
    success "Services started"
}

# Check service status
check_status() {
    log "Checking service status..."
    
    echo "=== Service Status ==="
    sudo systemctl status redis --no-pager -l
    echo ""
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    sudo systemctl status nginx --no-pager -l
    
    echo "=== Application Health ==="
    curl -f http://localhost/api/system/status || error "Application health check failed"
    
    success "All services are running"
}

# Main deployment function
main() {
    log "Starting Email Automation System deployment..."
    
    check_root
    check_requirements
    install_dependencies
    create_user
    setup_app_directory
    setup_python_env
    setup_systemd_service
    setup_nginx
    setup_redis
    setup_ssl
    create_config
    start_services
    check_status
    
    success "Deployment completed successfully!"
    
    echo ""
    echo "=== Next Steps ==="
    echo "1. Edit configuration: sudo nano $APP_DIR/.env"
    echo "2. Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "3. Access dashboard: http://$(hostname -I | awk '{print $1}')"
    echo "4. Check logs: sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "=== Useful Commands ==="
    echo "Start service: sudo systemctl start $SERVICE_NAME"
    echo "Stop service: sudo systemctl stop $SERVICE_NAME"
    echo "Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "Check status: sudo systemctl status $SERVICE_NAME"
}

# Run main function
main "$@"


