#!/bin/bash

# StratMaster Production Deployment Automation Script
# This script automates the deployment of StratMaster using Helm and ArgoCD

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
NAMESPACE_PREFIX="stratmaster"
ARGOCD_NAMESPACE="argocd"
CHART_PATH="${PROJECT_ROOT}/helm"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Help function
show_help() {
    cat << EOF
StratMaster Deployment Automation

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  deploy-dev          Deploy to development environment
  deploy-staging      Deploy to staging environment  
  deploy-prod         Deploy to production environment
  install-argocd      Install ArgoCD in the cluster
  setup-project       Setup ArgoCD project and applications
  validate            Validate Helm charts and manifests
  rollback            Rollback to previous version
  status              Check deployment status
  logs                Show application logs
  help                Show this help message

Options:
  --namespace         Override default namespace
  --chart-version     Specify chart version to deploy
  --image-tag         Specify image tag to deploy
  --values-file       Additional values file to use
  --dry-run           Perform a dry run without actual deployment
  --wait              Wait for deployment to complete
  --timeout           Timeout for deployment (default: 300s)

Environment Variables:
  KUBECONFIG          Path to kubectl config file
  HELM_NAMESPACE      Default Helm namespace
  DOCKER_REGISTRY     Docker registry for images

Examples:
  $0 deploy-dev --dry-run
  $0 deploy-prod --image-tag=v1.2.3 --wait
  $0 validate
  $0 status --namespace=stratmaster-prod

EOF
}

# Parse command line arguments
COMMAND=""
ENVIRONMENT=""
NAMESPACE=""
CHART_VERSION=""
IMAGE_TAG=""
VALUES_FILE=""
DRY_RUN=false
WAIT=false
TIMEOUT="300s"

while [[ $# -gt 0 ]]; do
    case $1 in
        deploy-dev|deploy-staging|deploy-prod|install-argocd|setup-project|validate|rollback|status|logs|help)
            COMMAND="$1"
            case $1 in
                deploy-dev) ENVIRONMENT="development" ;;
                deploy-staging) ENVIRONMENT="staging" ;;
                deploy-prod) ENVIRONMENT="production" ;;
            esac
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --chart-version)
            CHART_VERSION="$2"
            shift 2
            ;;
        --image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --values-file)
            VALUES_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --wait)
            WAIT=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set default namespace if not provided
if [[ -z "$NAMESPACE" && -n "$ENVIRONMENT" ]]; then
    if [[ "$ENVIRONMENT" == "development" ]]; then
        NAMESPACE="${NAMESPACE_PREFIX}-dev"
    else
        NAMESPACE="${NAMESPACE_PREFIX}-${ENVIRONMENT}"
    fi
fi

# Validation functions
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if helm is available
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed or not in PATH"
        exit 1
    fi
    
    # Check Helm version (should be 3.x)
    HELM_VERSION=$(helm version --short | grep -o "v3\." || true)
    if [[ -z "$HELM_VERSION" ]]; then
        log_error "Helm 3.x is required"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Unable to connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Validation function for Helm charts
validate_charts() {
    log_info "Validating Helm charts..."
    
    # Validate main chart
    if ! helm lint "${CHART_PATH}"; then
        log_error "Main chart validation failed"
        return 1
    fi
    
    # Validate individual service charts
    for chart in "${CHART_PATH}"/{stratmaster-api,research-mcp}; do
        if [[ -d "$chart" ]]; then
            log_info "Validating chart: $(basename "$chart")"
            if ! helm lint "$chart"; then
                log_error "Chart validation failed: $(basename "$chart")"
                return 1
            fi
        fi
    done
    
    log_success "All Helm charts validated successfully"
}

# Install ArgoCD
install_argocd() {
    log_info "Installing ArgoCD..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$ARGOCD_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Install ArgoCD
    kubectl apply -n "$ARGOCD_NAMESPACE" -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # Wait for ArgoCD to be ready
    log_info "Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n "$ARGOCD_NAMESPACE"
    
    # Get initial admin password
    ADMIN_PASSWORD=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    
    log_success "ArgoCD installed successfully"
    log_info "Admin password: $ADMIN_PASSWORD"
    log_info "Access ArgoCD UI: kubectl port-forward svc/argocd-server -n argocd 8080:443"
}

# Setup ArgoCD project and applications
setup_argocd_project() {
    log_info "Setting up ArgoCD project and applications..."
    
    # Apply project configuration
    kubectl apply -f "${PROJECT_ROOT}/argocd/projects/stratmaster.yaml"
    
    # Apply application configurations
    for app in "${PROJECT_ROOT}/argocd/applications"/*.yaml; do
        log_info "Applying application: $(basename "$app")"
        kubectl apply -f "$app"
    done
    
    log_success "ArgoCD project and applications configured"
}

# Deploy function
deploy_environment() {
    local env="$1"
    local namespace="$2"
    
    log_info "Deploying StratMaster to $env environment (namespace: $namespace)..."
    
    # Prepare Helm command
    local helm_cmd="helm upgrade --install stratmaster-${env} ${CHART_PATH}"
    helm_cmd="${helm_cmd} --namespace ${namespace}"
    helm_cmd="${helm_cmd} --create-namespace"
    helm_cmd="${helm_cmd} --values ${CHART_PATH}/values-${env}.yaml"
    
    # Add additional values file if specified
    if [[ -n "$VALUES_FILE" ]]; then
        helm_cmd="${helm_cmd} --values ${VALUES_FILE}"
    fi
    
    # Add chart version if specified
    if [[ -n "$CHART_VERSION" ]]; then
        helm_cmd="${helm_cmd} --version ${CHART_VERSION}"
    fi
    
    # Add image tag override if specified
    if [[ -n "$IMAGE_TAG" ]]; then
        helm_cmd="${helm_cmd} --set image.tag=${IMAGE_TAG}"
    fi
    
    # Add environment-specific settings
    helm_cmd="${helm_cmd} --set global.environment=${env}"
    
    # Add wait flag if requested
    if [[ "$WAIT" == "true" ]]; then
        helm_cmd="${helm_cmd} --wait --timeout=${TIMEOUT}"
    fi
    
    # Add dry-run flag if requested
    if [[ "$DRY_RUN" == "true" ]]; then
        helm_cmd="${helm_cmd} --dry-run"
        log_info "Performing dry run deployment..."
    fi
    
    # Execute Helm command
    log_info "Executing: $helm_cmd"
    if eval "$helm_cmd"; then
        log_success "Deployment to $env completed successfully"
        
        if [[ "$DRY_RUN" == "false" ]]; then
            # Show deployment status
            kubectl get pods -n "$namespace" -l "app.kubernetes.io/instance=stratmaster-${env}"
        fi
    else
        log_error "Deployment to $env failed"
        exit 1
    fi
}

# Check deployment status
check_status() {
    local namespace="$1"
    
    log_info "Checking deployment status for namespace: $namespace"
    
    # Check if namespace exists
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        log_error "Namespace '$namespace' does not exist"
        exit 1
    fi
    
    # Get deployment status
    echo
    echo "=== Deployments ==="
    kubectl get deployments -n "$namespace" -o wide
    
    echo
    echo "=== Pods ==="
    kubectl get pods -n "$namespace" -o wide
    
    echo  
    echo "=== Services ==="
    kubectl get services -n "$namespace" -o wide
    
    # Check ingress if it exists
    if kubectl get ingress -n "$namespace" &> /dev/null; then
        echo
        echo "=== Ingress ==="
        kubectl get ingress -n "$namespace" -o wide
    fi
    
    # Check if pods are ready
    local not_ready_pods=$(kubectl get pods -n "$namespace" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    if [[ "$not_ready_pods" -eq 0 ]]; then
        log_success "All pods are running and ready"
    else
        log_warning "$not_ready_pods pods are not ready"
    fi
}

# Show application logs
show_logs() {
    local namespace="$1"
    
    log_info "Showing logs for namespace: $namespace"
    
    # Get all pods in namespace
    local pods=$(kubectl get pods -n "$namespace" -o name)
    
    if [[ -z "$pods" ]]; then
        log_warning "No pods found in namespace: $namespace"
        return
    fi
    
    echo "Available pods:"
    echo "$pods"
    echo
    
    # Show logs for the first API pod found
    local api_pod=$(kubectl get pods -n "$namespace" -l "app.kubernetes.io/name=stratmaster-api" -o name | head -n 1)
    
    if [[ -n "$api_pod" ]]; then
        log_info "Showing logs for: $api_pod"
        kubectl logs -n "$namespace" "$api_pod" --tail=100 -f
    else
        log_warning "No API pods found. Use 'kubectl logs' manually to view logs."
    fi
}

# Rollback function
rollback_deployment() {
    local namespace="$1"
    
    log_info "Rolling back deployment in namespace: $namespace"
    
    # Get release name based on environment
    local release_name=""
    case "$namespace" in
        *-dev) release_name="stratmaster-development" ;;
        *-staging) release_name="stratmaster-staging" ;;
        *-prod) release_name="stratmaster-production" ;;
        *) release_name="stratmaster" ;;
    esac
    
    # Show rollback history
    log_info "Rollback history for release: $release_name"
    helm history "$release_name" -n "$namespace"
    
    # Rollback to previous version
    if helm rollback "$release_name" -n "$namespace"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback failed"
        exit 1
    fi
}

# Main execution logic
main() {
    case "$COMMAND" in
        help|"")
            show_help
            ;;
        validate)
            check_prerequisites
            validate_charts
            ;;
        install-argocd)
            check_prerequisites
            install_argocd
            ;;
        setup-project)
            check_prerequisites
            setup_argocd_project
            ;;
        deploy-dev|deploy-staging|deploy-prod)
            check_prerequisites
            validate_charts
            deploy_environment "$ENVIRONMENT" "$NAMESPACE"
            ;;
        status)
            check_prerequisites
            check_status "$NAMESPACE"
            ;;
        logs)
            check_prerequisites
            show_logs "$NAMESPACE"
            ;;
        rollback)
            check_prerequisites
            rollback_deployment "$NAMESPACE"
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main