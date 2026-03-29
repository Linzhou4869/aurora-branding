#!/bin/bash
# Priority Customs Review Status Check
# Targets containers flagged for priority customs review
# Runs every 6 hours starting at midnight ICT

MANIFEST_FILE="/mnt/afs_toolcall/zhoulin3/.openclaw/workspaces/gendata-worker-6/q3_textile_manifest.csv"
LOG_FILE="/mnt/afs_toolcall/zhoulin3/.openclaw/workspaces/gendata-worker-6/logs/priority_customs_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

echo "=== Priority Customs Status Check ===" >> "$LOG_FILE"
echo "Timestamp: $TIMESTAMP" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Extract priority containers (skip header, filter by Status column)
echo "Containers requiring priority customs review:" >> "$LOG_FILE"
grep "PRIORITY_CUSTOMS_REVIEW" "$MANIFEST_FILE" | while IFS=',' read -r id weight material status; do
    echo "  - $id: $weight kg ($material)" >> "$LOG_FILE"
done

echo "" >> "$LOG_FILE"
echo "Check completed." >> "$LOG_FILE"
echo "-----------------------------------" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Output summary to stdout as well
echo "Priority customs check completed at $TIMESTAMP"
echo "Flagged containers: $(grep -c 'PRIORITY_CUSTOMS_REVIEW' "$MANIFEST_FILE")"
