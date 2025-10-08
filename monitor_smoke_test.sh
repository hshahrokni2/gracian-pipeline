#!/bin/bash
LOG_FILE="/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline/smoke_test_1759895568.log"

echo "============================================================"
echo "🧪 5-PDF SMOKE TEST - LIVE MONITOR"
echo "============================================================"
echo ""
echo "📊 Progress:"
grep -E "\[.*Processing.*\]|✅|❌|SUMMARY" "$LOG_FILE" 2>/dev/null | tail -20
echo ""
echo "📈 Latest Status:"
tail -5 "$LOG_FILE" 2>/dev/null
echo ""
echo "⏰ Started: $(date -r "$LOG_FILE" '+%H:%M:%S' 2>/dev/null || echo 'Unknown')"
echo "   Current: $(date '+%H:%M:%S')"
