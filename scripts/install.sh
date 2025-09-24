#!/bin/bash
# StratMaster One-File Installer
# Detects hardware and installs optimal configuration

set -euo pipefail

SCRIPT_VERSION="0.1.0"
REPO_URL="https://github.com/IAmJonoBo/StratMaster"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.stratmaster}"
INSTALL_MODE="${INSTALL_MODE:-auto}"  # auto, local, docker, k8s

# Colors for output
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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# System detection functions
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

detect_arch() {
    case "$(uname -m)" in
        x86_64)     echo "x64";;
        arm64|aarch64) echo "arm64";;
        armv7l)     echo "arm";;
        i386|i686)  echo "x86";;
        *)          echo "unknown";;
    esac
}

detect_cpu_cores() {
    if command -v nproc >/dev/null 2>&1; then
        nproc
    elif command -v sysctl >/dev/null 2>&1; then
        sysctl -n hw.ncpu 2>/dev/null || echo "4"
    else
        echo "4"  # fallback
    fi
}

detect_memory_gb() {
    if [[ "$(detect_os)" == "linux" ]]; then
        awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo "8"
    elif [[ "$(detect_os)" == "macos" ]]; then
        echo $(($(sysctl -n hw.memsize 2>/dev/null || echo 8589934592) / 1024 / 1024 / 1024))
    else
        echo "8"  # fallback
    fi
}

detect_gpu() {
    local has_nvidia=false
    local has_amd=false
    local has_apple=false
    
    # Check for NVIDIA
    if command -v nvidia-smi >/dev/null 2>&1; then
        if nvidia-smi >/dev/null 2>&1; then
            has_nvidia=true
        fi
    fi
    
    # Check for AMD (Linux)
    if command -v rocm-smi >/dev/null 2>&1; then
        has_amd=true
    fi
    
    # Check for Apple Silicon
    if [[ "$(detect_os)" == "macos" ]] && [[ "$(detect_arch)" == "arm64" ]]; then
        has_apple=true
    fi
    
    if $has_nvidia; then
        echo "nvidia"
    elif $has_amd; then
        echo "amd"
    elif $has_apple; then
        echo "apple"
    else
        echo "none"
    fi
}

check_docker() {
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            echo "available"
        else
            echo "installed_not_running"
        fi
    else
        echo "not_installed"
    fi
}

check_kubernetes() {
    if command -v kubectl >/dev/null 2>&1; then
        if kubectl cluster-info >/dev/null 2>&1; then
            echo "available"
        else
            echo "not_connected"
        fi
    else
        echo "not_installed"
    fi
}

# Hardware profiling
profile_hardware() {
    local os=$(detect_os)
    local arch=$(detect_arch)
    local cpu_cores=$(detect_cpu_cores)
    local memory_gb=$(detect_memory_gb)
    local gpu=$(detect_gpu)
    local docker_status=$(check_docker)
    local k8s_status=$(check_kubernetes)
    
    log_info "System Profile:"
    log_info "  OS: $os ($arch)"
    log_info "  CPU Cores: $cpu_cores"
    log_info "  Memory: ${memory_gb}GB"
    log_info "  GPU: $gpu"
    log_info "  Docker: $docker_status"
    log_info "  Kubernetes: $k8s_status"
    
    # Determine recommended configuration
    local config="lightweight"
    if [[ $memory_gb -ge 16 ]] && [[ "$gpu" != "none" ]]; then
        config="high-performance"
    elif [[ $memory_gb -ge 8 ]]; then
        config="standard"
    fi
    
    echo "$config"
}

# Installation mode selection
select_install_mode() {
    local recommended_config=$1
    local docker_status=$(check_docker)
    local k8s_status=$(check_kubernetes)
    
    if [[ "$INSTALL_MODE" != "auto" ]]; then
        echo "$INSTALL_MODE"
        return
    fi
    
    log_info "Selecting optimal installation mode..."
    
    # Decision matrix based on system capabilities
    if [[ "$k8s_status" == "available" ]]; then
        echo "k8s"
    elif [[ "$docker_status" == "available" ]]; then
        echo "docker"
    else
        echo "local"
    fi
}

# Desktop application installation
install_desktop_app() {
    local os=$(detect_os)
    local arch=$(detect_arch)
    
    log_info "Installing StratMaster Desktop Application..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR/bin"
    
    # Download appropriate binary (would be from releases in production)
    local binary_name="stratmaster-desktop"
    if [[ "$os" == "windows" ]]; then
        binary_name="stratmaster-desktop.exe"
    fi
    
    local download_url="$REPO_URL/releases/latest/download/stratmaster-desktop-${os}-${arch}"
    if [[ "$os" == "windows" ]]; then
        download_url="${download_url}.exe"
    fi
    
    log_info "Downloading desktop application from: $download_url"
    
    # For demo purposes, create a placeholder script
    cat > "$INSTALL_DIR/bin/$binary_name" << 'EOF'
#!/bin/bash
# StratMaster Desktop Launcher
echo "StratMaster Desktop Application"
echo "This would launch the Tauri-based desktop app"
echo "Install directory: $INSTALL_DIR"
echo "For development, run: cd apps/desktop && npm run tauri dev"
EOF
    chmod +x "$INSTALL_DIR/bin/$binary_name"
    
    # Create desktop entry (Linux)
    if [[ "$os" == "linux" ]]; then
        mkdir -p "$HOME/.local/share/applications"
        cat > "$HOME/.local/share/applications/stratmaster.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=StratMaster
Comment=AI-powered Brand Strategy platform
Exec=$INSTALL_DIR/bin/$binary_name
Icon=$INSTALL_DIR/icons/stratmaster.png
Terminal=false
Categories=Office;
EOF
    fi
    
    log_success "Desktop application installed to $INSTALL_DIR/bin/$binary_name"
}

# Docker-based installation
install_docker_mode() {
    log_info "Installing StratMaster in Docker mode..."
    
    # Clone or download docker-compose.yml
    mkdir -p "$INSTALL_DIR/docker"
    
    # Create production docker-compose.yml
    cat > "$INSTALL_DIR/docker/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  stratmaster-api:
    image: stratmaster/stratmaster-api:latest
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://stratmaster:password@postgres:5432/stratmaster
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - OPENSEARCH_URL=http://opensearch:9200
    depends_on:
      - postgres
      - redis
      - qdrant
      - opensearch
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  research-mcp:
    image: stratmaster/research-mcp:latest
    ports:
      - "8081:8081"
    depends_on:
      - opensearch

  knowledge-mcp:
    image: stratmaster/knowledge-mcp:latest
    ports:
      - "8082:8082"
    depends_on:
      - qdrant

  router-mcp:
    image: stratmaster/router-mcp:latest
    ports:
      - "8083:8083"

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=stratmaster
      - POSTGRES_USER=stratmaster
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"

  opensearch:
    image: opensearchproject/opensearch:2
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
      - bootstrap.memory_lock=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    ports:
      - "9200:9200"

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  opensearch_data:
EOF
    
    # Create helper scripts
    cat > "$INSTALL_DIR/docker/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker compose up -d
echo "StratMaster services starting..."
echo "API will be available at: http://localhost:8080"
echo "Check status with: ./status.sh"
EOF
    
    cat > "$INSTALL_DIR/docker/stop.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker compose down
echo "StratMaster services stopped"
EOF
    
    cat > "$INSTALL_DIR/docker/status.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker compose ps
echo ""
echo "Health check:"
curl -s http://localhost:8080/healthz | jq . || echo "API not ready"
EOF
    
    chmod +x "$INSTALL_DIR/docker"/*.sh
    
    log_success "Docker configuration installed to $INSTALL_DIR/docker"
    log_info "Start with: $INSTALL_DIR/docker/start.sh"
}

# Kubernetes installation
install_k8s_mode() {
    log_info "Installing StratMaster in Kubernetes mode..."
    
    mkdir -p "$INSTALL_DIR/k8s"
    
    # Create namespace
    kubectl create namespace stratmaster --dry-run=client -o yaml > "$INSTALL_DIR/k8s/namespace.yaml"
    
    # Create helper script for Helm installation
    cat > "$INSTALL_DIR/k8s/install.sh" << EOF
#!/bin/bash
# StratMaster Kubernetes Installation

set -e

echo "Installing StratMaster on Kubernetes..."

# Create namespace
kubectl apply -f namespace.yaml

# Add Helm repository (placeholder)
echo "Adding StratMaster Helm repository..."
# helm repo add stratmaster https://charts.stratmaster.com
# helm repo update

# Install main API
echo "Installing StratMaster API..."
# helm install stratmaster-api stratmaster/stratmaster-api -n stratmaster

# Install MCP servers
echo "Installing MCP servers..."
# helm install research-mcp stratmaster/research-mcp -n stratmaster
# helm install knowledge-mcp stratmaster/knowledge-mcp -n stratmaster  
# helm install router-mcp stratmaster/router-mcp -n stratmaster

echo "Installation complete!"
echo "Get status with: kubectl get pods -n stratmaster"
echo "Port forward API: kubectl port-forward -n stratmaster svc/stratmaster-api 8080:80"
EOF
    
    chmod +x "$INSTALL_DIR/k8s/install.sh"
    
    log_success "Kubernetes configuration installed to $INSTALL_DIR/k8s"
    log_info "Install with: $INSTALL_DIR/k8s/install.sh"
}

# Local development installation
install_local_mode() {
    log_info "Installing StratMaster in Local Development mode..."
    
    # Check dependencies
    local missing_deps=()
    
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python3")
    fi
    
    if ! command -v make >/dev/null 2>&1; then
        missing_deps+=("make")
    fi
    
    if ! command -v git >/dev/null 2>&1; then  
        missing_deps+=("git")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and run the installer again"
        exit 1
    fi
    
    # Clone repository
    if [[ ! -d "$INSTALL_DIR/stratmaster" ]]; then
        log_info "Cloning StratMaster repository..."
        git clone "$REPO_URL.git" "$INSTALL_DIR/stratmaster"
    else
        log_info "Updating existing StratMaster installation..."
        cd "$INSTALL_DIR/stratmaster"
        git pull origin main
    fi
    
    cd "$INSTALL_DIR/stratmaster"
    
    # Bootstrap environment
    log_info "Bootstrapping development environment..."
    make bootstrap
    
    # Create startup script
    cat > "$INSTALL_DIR/start-local.sh" << EOF
#!/bin/bash
cd "$INSTALL_DIR/stratmaster"
echo "Starting StratMaster API server..."
.venv/bin/uvicorn stratmaster_api.app:create_app --factory --reload --host 0.0.0.0 --port 8080
EOF
    chmod +x "$INSTALL_DIR/start-local.sh"
    
    log_success "Local development installation complete"
    log_info "Start API with: $INSTALL_DIR/start-local.sh"
}

# Configuration wizard
run_config_wizard() {
    local install_mode=$1
    
    log_info "Running configuration wizard..."
    
    # Create config directory
    mkdir -p "$INSTALL_DIR/config"
    
    # Basic configuration
    cat > "$INSTALL_DIR/config/stratmaster.yaml" << EOF
# StratMaster Configuration
version: "0.1.0"
installation:
  mode: "$install_mode"
  directory: "$INSTALL_DIR"
  created: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

api:
  base_url: "http://localhost:8080"
  timeout: 30

hardware:
  profile: "$(profile_hardware)"
  auto_detect: true

ui:
  theme: "auto"
  enable_desktop_app: true

services:
  auto_start: false
  health_check_interval: 30
EOF
    
    log_success "Configuration created at $INSTALL_DIR/config/stratmaster.yaml"
}

# Post-installation setup
post_install() {
    local install_mode=$1
    
    log_info "Running post-installation setup..."
    
    # Create bin directory and add to PATH suggestion
    mkdir -p "$INSTALL_DIR/bin"
    
    # Create main launcher script
    cat > "$INSTALL_DIR/bin/stratmaster" << 'EOF'
#!/bin/bash
# StratMaster Launcher
INSTALL_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
source "$INSTALL_DIR/config/stratmaster.yaml" 2>/dev/null || true

case "${1:-help}" in
    start)
        echo "Starting StratMaster..."
        case "$installation_mode" in
            docker) "$INSTALL_DIR/docker/start.sh" ;;
            k8s) echo "Use kubectl to manage Kubernetes installation" ;;
            local) "$INSTALL_DIR/start-local.sh" ;;
            *) echo "Unknown installation mode" ;;
        esac
        ;;
    stop)
        echo "Stopping StratMaster..."
        case "$installation_mode" in
            docker) "$INSTALL_DIR/docker/stop.sh" ;;
            k8s) echo "Use kubectl to manage Kubernetes installation" ;;
            local) pkill -f "stratmaster_api" ;;
            *) echo "Unknown installation mode" ;;
        esac
        ;;
    status)
        curl -s http://localhost:8080/healthz | jq . || echo "StratMaster API not responding"
        ;;
    config)
        echo "Configuration file: $INSTALL_DIR/config/stratmaster.yaml"
        cat "$INSTALL_DIR/config/stratmaster.yaml"
        ;;
    help|*)
        echo "StratMaster CLI"
        echo "Commands:"
        echo "  start   - Start StratMaster services"
        echo "  stop    - Stop StratMaster services"  
        echo "  status  - Check service health"
        echo "  config  - Show configuration"
        echo "  help    - Show this help"
        ;;
esac
EOF
    chmod +x "$INSTALL_DIR/bin/stratmaster"
    
    # Installation summary
    echo ""
    log_success "StratMaster installation completed!"
    echo ""
    log_info "Installation Summary:"
    log_info "  Mode: $install_mode"
    log_info "  Directory: $INSTALL_DIR"
    log_info "  Launcher: $INSTALL_DIR/bin/stratmaster"
    echo ""
    log_info "Next Steps:"
    log_info "  1. Add $INSTALL_DIR/bin to your PATH"
    log_info "  2. Run: stratmaster start"
    log_info "  3. Visit: http://localhost:8080"
    echo ""
    
    # PATH suggestion
    if [[ ":$PATH:" != *":$INSTALL_DIR/bin:"* ]]; then
        log_info "To add StratMaster to your PATH, run:"
        echo "  echo 'export PATH=\"\$PATH:$INSTALL_DIR/bin\"' >> ~/.bashrc"
        echo "  source ~/.bashrc"
    fi
}

# Main installation flow
main() {
    log_info "StratMaster Installer v$SCRIPT_VERSION"
    echo ""
    
    # System detection
    log_info "Detecting system configuration..."
    local hardware_profile=$(profile_hardware)
    local install_mode=$(select_install_mode "$hardware_profile")
    
    echo ""
    log_info "Recommended installation mode: $install_mode"
    log_info "Hardware profile: $hardware_profile"
    echo ""
    
    # Confirm installation
    if [[ "${STRATMASTER_AUTO_INSTALL:-}" != "true" ]]; then
        read -p "Proceed with installation? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Installation cancelled"
            exit 0
        fi
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    log_info "Installing to: $INSTALL_DIR"
    
    # Install based on mode
    case "$install_mode" in
        local)
            install_local_mode
            install_desktop_app
            ;;
        docker)
            install_docker_mode
            install_desktop_app
            ;;
        k8s)
            install_k8s_mode 
            install_desktop_app
            ;;
        *)
            log_error "Unknown installation mode: $install_mode"
            exit 1
            ;;
    esac
    
    # Configuration and finalization
    run_config_wizard "$install_mode"
    post_install "$install_mode"
}

# Error handling
trap 'log_error "Installation failed at line $LINENO"' ERR

# Run main installation
main "$@"