#!/bin/bash
#
# Atomic Rollback Script - Day 5 Pre-Flight Tool #3
#
# Enables <5 minute recovery vs 60-90 minutes of unstructured debugging.
#
# Usage:
#   ./scripts/rollback_optimization.sh              # Rollback last commit
#   ./scripts/rollback_optimization.sh <commit>     # Rollback to specific commit
#   ./scripts/rollback_optimization.sh --test       # Dry run (no changes)
#
# Safety:
#   - Creates backup branch before rollback
#   - Runs validation after rollback
#   - Atomic operation (all or nothing)

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_BRANCH_PREFIX="backup-$(date +%Y%m%d-%H%M%S)"
VALIDATION_PDF="../../SRS/brf_198532.pdf"
MIN_COVERAGE=0.784  # Day 4 baseline (78.4%)

# Parse arguments
DRY_RUN=false
TARGET_COMMIT="HEAD"

while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--test] [<commit>]"
            echo ""
            echo "Options:"
            echo "  --test         Dry run (no changes)"
            echo "  <commit>       Rollback to specific commit (default: HEAD~1)"
            echo ""
            exit 0
            ;;
        *)
            TARGET_COMMIT="$1"
            shift
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Verify we're in a git repository
log_info "Step 1: Verifying git repository..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Not a git repository. Exiting."
    exit 1
fi
log_success "Git repository verified"

# Step 2: Check for uncommitted changes
log_info "Step 2: Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    log_warning "Uncommitted changes detected"
    if [ "$DRY_RUN" = false ]; then
        read -p "Stash changes before rollback? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash push -m "Auto-stash before rollback at $(date)"
            log_success "Changes stashed"
        else
            log_error "Cannot rollback with uncommitted changes. Exiting."
            exit 1
        fi
    fi
else
    log_success "Working directory clean"
fi

# Step 3: Get current commit info
CURRENT_BRANCH=$(git branch --show-current)
CURRENT_COMMIT=$(git rev-parse HEAD)
CURRENT_MESSAGE=$(git log -1 --pretty=%B HEAD | head -n 1)

log_info "Current state:"
echo "   Branch: $CURRENT_BRANCH"
echo "   Commit: ${CURRENT_COMMIT:0:7}"
echo "   Message: $CURRENT_MESSAGE"
echo ""

# Step 4: Determine rollback target
if [ "$TARGET_COMMIT" = "HEAD" ]; then
    TARGET_COMMIT="HEAD~1"
fi

ROLLBACK_COMMIT=$(git rev-parse "$TARGET_COMMIT")
ROLLBACK_MESSAGE=$(git log -1 --pretty=%B "$ROLLBACK_COMMIT" | head -n 1)

log_info "Rollback target:"
echo "   Commit: ${ROLLBACK_COMMIT:0:7}"
echo "   Message: $ROLLBACK_MESSAGE"
echo ""

# Step 5: Create backup branch
BACKUP_BRANCH="${BACKUP_BRANCH_PREFIX}-${CURRENT_BRANCH}"
log_info "Step 5: Creating backup branch: $BACKUP_BRANCH"

if [ "$DRY_RUN" = false ]; then
    git branch "$BACKUP_BRANCH"
    log_success "Backup branch created: $BACKUP_BRANCH"
else
    log_info "[DRY RUN] Would create backup branch: $BACKUP_BRANCH"
fi

# Step 6: Perform rollback
log_info "Step 6: Rolling back to ${ROLLBACK_COMMIT:0:7}..."

if [ "$DRY_RUN" = false ]; then
    git reset --hard "$ROLLBACK_COMMIT"
    log_success "Rollback complete"
else
    log_info "[DRY RUN] Would rollback to ${ROLLBACK_COMMIT:0:7}"
fi

# Step 7: Verify rollback
log_info "Step 7: Verifying rollback..."
if [ "$DRY_RUN" = false ]; then
    NEW_COMMIT=$(git rev-parse HEAD)
    if [ "$NEW_COMMIT" = "$ROLLBACK_COMMIT" ]; then
        log_success "Rollback verified: HEAD is now at ${NEW_COMMIT:0:7}"
    else
        log_error "Rollback verification failed! HEAD is at ${NEW_COMMIT:0:7}, expected ${ROLLBACK_COMMIT:0:7}"
        exit 1
    fi
fi

# Step 8: Run validation to verify system still works
log_info "Step 8: Running validation on baseline PDF..."

if [ "$DRY_RUN" = false ]; then
    if [ -f "$VALIDATION_PDF" ]; then
        # Run validation with timeout
        VALIDATION_OUTPUT=$(timeout 300 python code/validate_enhanced.py "$VALIDATION_PDF" 2>&1 || true)

        # Check if validation passed
        if echo "$VALIDATION_OUTPUT" | grep -q "VALIDATION PASSED"; then
            log_success "Validation passed - rollback successful!"

            # Extract coverage from output
            COVERAGE=$(echo "$VALIDATION_OUTPUT" | grep -oP 'Coverage \K[0-9.]+%' | head -n 1 || echo "N/A")
            log_info "Coverage after rollback: $COVERAGE"

        else
            log_warning "Validation did not pass after rollback"
            echo "$VALIDATION_OUTPUT" | tail -n 20

            # Ask if user wants to keep rollback or restore
            read -p "Keep rollback anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Restoring from backup branch..."
                git reset --hard "$BACKUP_BRANCH"
                log_success "Restored to previous state"
                exit 1
            fi
        fi
    else
        log_warning "Validation PDF not found: $VALIDATION_PDF"
        log_info "Skipping validation check"
    fi
else
    log_info "[DRY RUN] Would run validation on $VALIDATION_PDF"
fi

# Step 9: Cleanup and summary
echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "ROLLBACK SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "Before rollback:"
echo "   Commit: ${CURRENT_COMMIT:0:7}"
echo "   Message: $CURRENT_MESSAGE"
echo ""
echo "After rollback:"
echo "   Commit: ${ROLLBACK_COMMIT:0:7}"
echo "   Message: $ROLLBACK_MESSAGE"
echo ""
echo "Backup branch: $BACKUP_BRANCH"
echo ""

if [ "$DRY_RUN" = false ]; then
    log_success "Rollback complete! Recovery time: <5 minutes"
    echo ""
    echo "To restore previous state if needed:"
    echo "   git reset --hard $BACKUP_BRANCH"
    echo ""
    echo "To delete backup branch after confirming rollback works:"
    echo "   git branch -D $BACKUP_BRANCH"
    echo ""
else
    log_info "DRY RUN complete - no changes made"
fi

exit 0
