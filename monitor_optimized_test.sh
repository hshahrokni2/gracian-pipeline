#!/bin/bash
# Monitor optimized 5-PDF test progress

LOG_FILE="/Users/hosseins/Dropbox/zeldadb/zeldabot/pdf_docs/Gracian Pipeline/optimized_5pdf_test.log"
START_TIME=$(date -r "$LOG_FILE" +%s 2>/dev/null || date +%s)
CURRENT_TIME=$(date +%s)
ELAPSED=$((CURRENT_TIME - START_TIME))
ELAPSED_MIN=$((ELAPSED / 60))
ELAPSED_SEC=$((ELAPSED % 60))

echo "============================================================"
echo "📊 OPTIMIZED 5-PDF TEST MONITOR"
echo "============================================================"
echo ""
echo "⏰ Elapsed: ${ELAPSED_MIN}m ${ELAPSED_SEC}s"
echo ""
echo "📋 PDF Processing Status:"
grep -E "\[[0-9]/5\]" "$LOG_FILE" 2>/dev/null | tail -5
echo ""
echo "📈 Latest Quality Metrics:"
grep -E "Coverage:|Confidence:" "$LOG_FILE" 2>/dev/null | tail -6
echo ""
echo "🔍 Latest Activity:"
tail -15 "$LOG_FILE" | grep -E "INFO|Processing|Finished|HTTP" | tail -5
echo ""
echo "✅ Success/Failure Count:"
grep -E "✅|❌" "$LOG_FILE" 2>/dev/null | tail -5
echo ""

# Check if completed
if grep -q "SUMMARY" "$LOG_FILE" 2>/dev/null; then
    echo "🎉 TEST COMPLETE!"
    echo ""
    grep -A 20 "SUMMARY" "$LOG_FILE"
else
    echo "⏳ Test in progress..."
    echo "   Check again in 2-3 minutes"
fi

echo ""
echo "============================================================"
