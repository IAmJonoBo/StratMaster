#!/usr/bin/env bash

# StratMaster Local Deployment Script
# User-friendly setup for non-power-users

set -euo pipefail

# Colors for better UX
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Progress indicator
show_progress() {
    local pid=$1
    local delay=0.75
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local required_version="3.11"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        log_error "Python 3.11+ is required, but you have Python $python_version"
        log_info "Please upgrade Python or use pyenv to install Python 3.11+"
        exit 1
    fi
    
    log_success "Python $python_version detected"
    
    # Check Docker (optional but recommended)
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            log_success "Docker is available and running"
            DOCKER_AVAILABLE=true
        else
            log_warning "Docker is installed but not running"
            DOCKER_AVAILABLE=false
        fi
    else
        log_warning "Docker is not installed (optional for full stack)"
        DOCKER_AVAILABLE=false
    fi
    
    # Check disk space
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 2000000 ]; then # 2GB in KB
        log_warning "Less than 2GB disk space available. Installation may fail."
    fi
    
    # Check memory
    if command -v free &> /dev/null; then
        local available_mem=$(free -m | awk 'NR==2{printf "%.0f", $7/1024}')
        if [ "$available_mem" -lt 2 ]; then
            log_warning "Less than 2GB RAM available. Performance may be limited."
        fi
    fi
}

# Setup virtual environment with better error handling
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    if [ -d ".venv" ]; then
        log_info "Virtual environment already exists, checking validity..."
        if .venv/bin/python -c "import sys; print(sys.version)" &> /dev/null; then
            log_success "Existing virtual environment is valid"
            return 0
        else
            log_warning "Existing virtual environment is corrupted, recreating..."
            rm -rf .venv
        fi
    fi
    
    # Create virtual environment with progress
    python3 -m venv .venv &
    local venv_pid=$!
    show_progress $venv_pid
    wait $venv_pid
    
    if [ $? -eq 0 ]; then
        log_success "Virtual environment created successfully"
    else
        log_error "Failed to create virtual environment"
        exit 1
    fi
    
    # Upgrade pip in virtual environment
    log_info "Upgrading pip in virtual environment..."
    .venv/bin/python -m pip install --upgrade pip --quiet
    
    if [ $? -eq 0 ]; then
        log_success "Pip upgraded successfully"
    else
        log_warning "Pip upgrade failed, continuing anyway..."
    fi
}

# Install dependencies with retry logic
install_dependencies() {
    log_info "Installing StratMaster dependencies..."
    
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Installation attempt $attempt of $max_attempts..."
        
        # Set timeout and retry settings for pip
        if PYTHONNOUSERSITE=1 PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install \
            --timeout=60 --retries=3 \
            -e packages/api pytest pre-commit &> /tmp/pip_install.log; then
            
            log_success "Dependencies installed successfully"
            return 0
        else
            log_warning "Installation attempt $attempt failed"
            
            if [ $attempt -eq $max_attempts ]; then
                log_error "All installation attempts failed"
                log_info "Error details:"
                tail -20 /tmp/pip_install.log
                log_info ""
                log_info "Common solutions:"
                log_info "1. Check your internet connection"
                log_info "2. Try again later (PyPI may be experiencing issues)"
                log_info "3. Use 'make test-docker' instead of local installation"
                exit 1
            else
                log_info "Waiting 10 seconds before retry..."
                sleep 10
            fi
        fi
        
        ((attempt++))
    done
}

# Health check function
health_check() {
    log_info "Running system health checks..."
    
    # Test Python imports
    log_info "Testing Python environment..."
    if .venv/bin/python -c "import fastapi, pydantic, httpx" 2>/dev/null; then
        log_success "Python dependencies are working"
    else
        log_warning "Some Python dependencies may not be fully functional"
    fi
    
    # Test API server startup (quick check)
    log_info "Testing API server startup..."
    if timeout 10 .venv/bin/python -c "
from packages.api.src.stratmaster_api.app import create_app
app = create_app()
print('API server can be created successfully')
" 2>/dev/null; then
        log_success "API server startup test passed"
    else
        log_warning "API server startup test failed (this may be normal in restricted environments)"
    fi
    
    # Check Docker services if available
    if [ "$DOCKER_AVAILABLE" = true ]; then
        log_info "Testing Docker services availability..."
        if docker-compose config &> /dev/null; then
            log_success "Docker Compose configuration is valid"
        else
            log_warning "Docker Compose configuration issues detected"
        fi
    fi
}

# Create easy-to-use wrapper scripts
create_scripts() {
    log_info "Creating convenience scripts..."
    
    # Create start script
    cat > start.sh << 'EOF'
#!/bin/bash
# Quick start script for StratMaster API
echo "Starting StratMaster API server..."
echo "Access at: http://127.0.0.1:8080"
echo "API docs at: http://127.0.0.1:8080/docs"
echo "Press Ctrl+C to stop"
echo ""

.venv/bin/uvicorn stratmaster_api.app:create_app \
    --factory \
    --reload \
    --host 127.0.0.1 \
    --port 8080
EOF
    
    chmod +x start.sh
    
    # Create test script
    cat > test.sh << 'EOF'
#!/bin/bash
# Quick test script for StratMaster
echo "Running StratMaster tests..."

PYTHONNOUSERSITE=1 .venv/bin/python -m pytest packages/api/tests/ -q
EOF
    
    chmod +x test.sh
    
    # Create full stack script (if Docker available)
    if [ "$DOCKER_AVAILABLE" = true ]; then
        cat > start-full.sh << 'EOF'
#!/bin/bash
# Start full StratMaster stack with Docker
echo "Starting full StratMaster stack..."
echo "This may take a few minutes on first run..."

make dev.up
echo ""
echo "Services starting up. Check status with: make dev.logs"
echo "API will be available at: http://127.0.0.1:8080"
echo ""
echo "To stop all services: make dev.down"
EOF
        
        chmod +x start-full.sh
        log_success "Full stack script created (start-full.sh)"
    fi
    
    log_success "Convenience scripts created (start.sh, test.sh)"
}

# Provide next steps guidance
show_next_steps() {
    log_success "StratMaster setup complete!"
    echo ""
    log_info "Next steps:"
    echo ""
    echo "  1. Test the installation:"
    echo "     ${GREEN}./test.sh${NC}"
    echo ""
    echo "  2. Start the API server:"
    echo "     ${GREEN}./start.sh${NC}"
    echo ""
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo "  3. Or start the full stack:"
        echo "     ${GREEN}./start-full.sh${NC}"
        echo ""
    fi
    echo "  ${BLUE}Access the API at: http://127.0.0.1:8080${NC}"
    echo "  ${BLUE}API documentation: http://127.0.0.1:8080/docs${NC}"
    echo ""
    log_info "For more information, see README.md or docs/"
    echo ""
    log_info "If you encounter issues:"
    echo "  - Check the troubleshooting section in README.md"
    echo "  - Ensure you have Python 3.11+ and good internet connection"
    echo "  - Try 'make test-docker' for Docker-based testing"
}

# Main execution
main() {
    echo "🚀 StratMaster Local Setup"
    echo "========================"
    echo ""
    
    # Initialize variables
    DOCKER_AVAILABLE=false
    
    # Run setup steps
    check_requirements
    setup_venv
    install_dependencies
    health_check
    create_scripts
    show_next_steps
    
    log_success "Setup completed successfully! 🎉"
}

# Run main function
main "$@"