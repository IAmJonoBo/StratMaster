#!/bin/bash

# StratMaster Database Migration Script
# Applies database schema updates for analytics, ML training, and approval workflows

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATIONS_DIR="${SCRIPT_DIR}/migrations"
DEFAULT_DB_URL="${POSTGRES_URL:-postgresql://stratmaster:stratmaster@localhost:5432/stratmaster}"

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
StratMaster Database Migration

Usage: $0 [OPTIONS]

Options:
    -u, --url DATABASE_URL      Database connection URL (default: from env POSTGRES_URL)
    -d, --dry-run              Show what would be executed without running
    -h, --help                 Show this help message
    -v, --verbose              Enable verbose output

Examples:
    $0                                                    # Use default database
    $0 -u postgresql://user:pass@localhost:5432/db      # Custom database
    $0 --dry-run                                         # Preview changes

Environment Variables:
    POSTGRES_URL    Default database connection string
EOF
}

# Parse command line arguments
DB_URL="$DEFAULT_DB_URL"
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            DB_URL="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate database URL
if [[ -z "$DB_URL" ]]; then
    log_error "Database URL is required. Set POSTGRES_URL environment variable or use -u option."
    exit 1
fi

# Check if psql is available
if ! command -v psql &> /dev/null; then
    log_error "psql is not installed or not in PATH"
    exit 1
fi

# Test database connection
log_info "Testing database connection..."
if ! psql "$DB_URL" -c '\q' 2>/dev/null; then
    log_error "Cannot connect to database: $DB_URL"
    exit 1
fi

log_success "Database connection successful"

# Create migrations tracking table if it doesn't exist
log_info "Setting up migration tracking..."
psql "$DB_URL" << 'EOF'
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64)
);
EOF

# Function to calculate file checksum
calculate_checksum() {
    local file="$1"
    sha256sum "$file" | cut -d' ' -f1
}

# Function to check if migration was already applied
is_migration_applied() {
    local migration_name="$1"
    local count
    count=$(psql "$DB_URL" -t -c "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = '$migration_name';")
    [[ "${count// /}" == "1" ]]
}

# Function to apply migration
apply_migration() {
    local migration_file="$1"
    local migration_name
    migration_name=$(basename "$migration_file" .sql)
    local checksum
    checksum=$(calculate_checksum "$migration_file")
    
    if is_migration_applied "$migration_name"; then
        log_info "Migration $migration_name already applied, skipping"
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN: Would apply migration $migration_name"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "--- Contents of $migration_file ---"
            cat "$migration_file"
            echo "--- End of $migration_file ---"
        fi
        return 0
    fi
    
    log_info "Applying migration: $migration_name"
    
    # Start transaction and apply migration
    psql "$DB_URL" << EOF
BEGIN;

-- Apply the migration
\i $migration_file

-- Record the migration
INSERT INTO schema_migrations (migration_name, checksum) 
VALUES ('$migration_name', '$checksum');

COMMIT;
EOF

    if [[ $? -eq 0 ]]; then
        log_success "Migration $migration_name applied successfully"
    else
        log_error "Failed to apply migration $migration_name"
        return 1
    fi
}

# Main migration logic
log_info "Starting database migrations..."

# Find all migration files and sort them
migration_files=()
while IFS= read -r -d '' file; do
    migration_files+=("$file")
done < <(find "$MIGRATIONS_DIR" -name "*.sql" -print0 | sort -z)

if [[ ${#migration_files[@]} -eq 0 ]]; then
    log_warning "No migration files found in $MIGRATIONS_DIR"
    exit 0
fi

# Apply each migration
for migration_file in "${migration_files[@]}"; do
    apply_migration "$migration_file"
done

log_success "All migrations completed successfully!"

# Show current schema info
if [[ "$DRY_RUN" == "false" ]]; then
    log_info "Current database schema summary:"
    psql "$DB_URL" << 'EOF'
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
    
    log_info "Applied migrations:"
    psql "$DB_URL" << 'EOF'
SELECT migration_name, applied_at 
FROM schema_migrations 
ORDER BY applied_at;
EOF
fi

log_success "Database migration script completed!"