#!/bin/bash
# Test 10 diverse PDFs for consistency validation

PDFS=(
  "../../SRS/brf_198532.pdf"
  "../../SRS/brf_276507.pdf"
  "../../SRS/brf_43334.pdf"
  "../../data/raw_pdfs/Hjorthagen/brf_268882.pdf"
  "../../data/raw_pdfs/Hjorthagen/brf_271852.pdf"
  "../../data/raw_pdfs/Hjorthagen/brf_81563.pdf"
  "../../data/raw_pdfs/Hjorthagen/brf_46160.pdf"
  "../../SRS/brf_280938.pdf"
  "../../SRS/brf_47809.pdf"
  "../../SRS/brf_276629.pdf"
)

mkdir -p results/10pdf_test

for pdf in "${PDFS[@]}"; do
  if [ -f "$pdf" ]; then
    echo "Testing: $pdf"
    timeout 300 python code/optimal_brf_pipeline.py "$pdf" 2>&1 | tail -30
    echo "---"
  fi
done

echo "✅ Test complete! Results in results/optimal_pipeline/"
