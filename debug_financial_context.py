#!/usr/bin/env python3
"""
Debug Financial Context Routing - Root Cause 1 Investigation
=============================================================

Investigates why brf_83301.pdf has 8 financial sections detected
but 0/6 financial fields extracted.

Tests:
1. What context do financial agents receive?
2. Can LLM extract data with direct context from pages 3, 8-10?
3. Is the issue context routing or agent prompts?
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import fitz
import json

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.parallel_orchestrator import build_agent_context_map
from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor

# Test PDF
TEST_PDF = "SRS/brf_83301.pdf"
FINANCIAL_PAGES = [3, 8, 9, 10]  # Pages with financial data (from ultrathinking)

print("=" * 80)
print("FINANCIAL CONTEXT DEBUGGING - brf_83301.pdf")
print("=" * 80)
print()

pdf_path = Path(__file__).parent / TEST_PDF

if not pdf_path.exists():
    print(f"❌ ERROR: PDF not found at {TEST_PDF}")
    sys.exit(1)

print(f"📄 PDF: {pdf_path.name}")
print(f"📍 Expected financial pages: {FINANCIAL_PAGES}")
print()

# Step 1: Extract Docling structure
print("=" * 80)
print("STEP 1: DOCLING STRUCTURE EXTRACTION")
print("=" * 80)
print()

extractor = RobustUltraComprehensiveExtractor()
base_result = extractor.extract_brf_document(str(pdf_path), mode="fast")

markdown = base_result.get('_docling_markdown', '')
tables = base_result.get('_docling_tables', [])

print(f"📊 Markdown length: {len(markdown):,} chars")
print(f"📊 Tables detected: {len(tables)}")
print()

# Count financial sections
financial_keywords = ['Resultaträkning', 'Balansräkning', 'Kassaflödesanalys']
financial_sections = []
for line in markdown.split('\n'):
    if line.startswith('##'):
        for keyword in financial_keywords:
            if keyword in line:
                financial_sections.append(line.strip())
                break

print(f"📊 Financial sections detected: {len(financial_sections)}")
for i, section in enumerate(financial_sections, 1):
    print(f"   {i}. {section}")
print()

# Step 2: Build agent context map
print("=" * 80)
print("STEP 2: AGENT CONTEXT MAP BUILDING")
print("=" * 80)
print()

context_map = build_agent_context_map(
    str(pdf_path),
    markdown,
    tables
)

# Check financial agents
financial_agents = ['revenue_agent', 'expenses_agent', 'balance_sheet_agent']

print("📋 Financial Agent Contexts:")
print()

for agent_name in financial_agents:
    if agent_name not in context_map:
        print(f"   ❌ {agent_name}: NOT IN CONTEXT MAP")
        continue

    agent_context = context_map[agent_name]
    context_preview = agent_context['context'][:500]
    pages_used = agent_context.get('pages_used', [])

    print(f"   📌 {agent_name}:")
    print(f"      Pages used: {pages_used}")
    print(f"      Context length: {len(agent_context['context']):,} chars")
    print(f"      Context preview (first 500 chars):")
    print(f"         {context_preview[:200]}...")
    print()

    # Check if expected pages are included
    expected_in_context = all(page in pages_used for page in FINANCIAL_PAGES)
    if expected_in_context:
        print(f"      ✅ All expected pages {FINANCIAL_PAGES} in context")
    else:
        missing = [p for p in FINANCIAL_PAGES if p not in pages_used]
        print(f"      ❌ Missing pages: {missing}")
    print()

# Step 3: Extract text from expected pages
print("=" * 80)
print("STEP 3: DIRECT PAGE TEXT EXTRACTION")
print("=" * 80)
print()

doc = fitz.open(pdf_path)

print("📖 Extracting text from expected financial pages:")
print()

for page_num in FINANCIAL_PAGES:
    page = doc[page_num - 1]  # 0-indexed
    text = page.get_text()

    print(f"   📄 Page {page_num} ({len(text):,} chars):")

    # Check for financial keywords
    keywords_found = []
    for keyword in financial_keywords:
        if keyword in text:
            keywords_found.append(keyword)

    if keywords_found:
        print(f"      ✅ Financial keywords: {', '.join(keywords_found)}")
    else:
        print(f"      ⚠️ No financial keywords found")

    # Check for numbers (financial data)
    import re
    numbers = re.findall(r'\d{1,3}(?:\s?\d{3})*(?:[.,]\d+)?', text)
    if len(numbers) >= 10:
        print(f"      ✅ Contains numbers: {len(numbers)} numeric values found")
        print(f"         Sample: {numbers[:5]}")
    else:
        print(f"      ⚠️ Few numbers: {len(numbers)} numeric values")

    # Preview first 300 chars
    print(f"      Preview:")
    print(f"         {text[:300]}...")
    print()

doc.close()

# Step 4: Test manual extraction with OpenAI
print("=" * 80)
print("STEP 4: MANUAL EXTRACTION TEST (Direct LLM Call)")
print("=" * 80)
print()

print("🧪 Testing if LLM can extract from pages 3, 8-10 with direct context...")
print()

# Get text from pages 3, 8-10
doc = fitz.open(pdf_path)
combined_text = ""
for page_num in FINANCIAL_PAGES:
    page = doc[page_num - 1]
    combined_text += f"\n\n--- PAGE {page_num} ---\n\n"
    combined_text += page.get_text()
doc.close()

# Create simple extraction prompt
from openai import OpenAI
client = OpenAI()

prompt = f"""Extract financial data from this Swedish BRF annual report excerpt.

Return a JSON object with these fields:
{{
  "revenue": <number or null>,
  "expenses": <number or null>,
  "net_income": <number or null>,
  "assets": <number or null>,
  "liabilities": <number or null>,
  "equity": <number or null>
}}

Look for Swedish terms:
- Revenue: "Intäkter", "Nettoomsättning"
- Expenses: "Kostnader", "Rörelsekostnader"
- Net Income: "Årets resultat", "Resultat efter skatt"
- Assets: "Tillgångar", "Summa tillgångar"
- Liabilities: "Skulder", "Summa skulder"
- Equity: "Eget kapital"

Extract ONLY the total/summary values, not line items.

Document excerpt:
{combined_text[:8000]}
"""

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial data extraction expert for Swedish documents."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    print("✅ Manual Extraction Results:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    # Count extracted fields
    extracted_count = sum(1 for v in result.values() if v is not None and v != 0)
    print(f"📊 Fields extracted: {extracted_count}/6")
    print()

    if extracted_count >= 3:
        print("✅ SUCCESS: LLM CAN extract financial data from these pages!")
        print("   Root cause: Context routing or agent prompt issue, NOT data availability")
    else:
        print("❌ FAILURE: LLM cannot extract data even with direct context")
        print("   Root cause: Data may not be in extractable format (images, complex tables)")

except Exception as e:
    print(f"❌ ERROR during manual extraction: {str(e)}")

print()

# Step 5: Diagnosis Summary
print("=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)
print()

print("🔍 Key Findings:")
print()

print("1. **Docling Detection**:")
print(f"   - Financial sections detected: {len(financial_sections)}")
print(f"   - Sections: {', '.join([s.replace('## ', '') for s in financial_sections[:3]])}")
print()

print("2. **Context Routing**:")
for agent_name in financial_agents:
    if agent_name in context_map:
        pages = context_map[agent_name].get('pages_used', [])
        expected_in_context = all(page in pages for page in FINANCIAL_PAGES)
        status = "✅ CORRECT" if expected_in_context else "❌ MISSING PAGES"
        print(f"   {agent_name}: {status} (pages: {pages})")
    else:
        print(f"   {agent_name}: ❌ NOT IN MAP")
print()

print("3. **Manual Extraction**:")
print("   Check output above to see if LLM can extract with direct context")
print()

print("💡 Recommended Next Steps:")
print()
print("   If LLM CAN extract manually:")
print("      → Fix context routing in build_agent_context_map()")
print("      → Ensure pages 3, 8-10 are passed to financial agents")
print()
print("   If LLM CANNOT extract manually:")
print("      → Check if data is in images (use mixed-mode)")
print("      → Improve prompt to handle complex table structures")
print()

print("=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
