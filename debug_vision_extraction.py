#!/usr/bin/env python3
"""
Debug Vision Extraction - Save Images and Inspect API Response
===============================================================

Renders pages as images, saves them for manual inspection,
and shows the raw vision API response to diagnose quality issues.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os
import fitz
from PIL import Image
from io import BytesIO
import base64
import json

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add gracian_pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI

PDF_PATH = "SRS/brf_76536.pdf"
IMAGE_PAGES = [9, 10, 11, 12]
OUTPUT_DIR = Path(__file__).parent / "data" / "anomaly_investigation" / "vision_debug"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("VISION EXTRACTION DEBUG: brf_76536.pdf")
print("=" * 80)
print()

pdf_path = Path(__file__).parent / PDF_PATH

if not pdf_path.exists():
    print(f"❌ ERROR: PDF not found at {PDF_PATH}")
    sys.exit(1)

print(f"📄 PDF: {pdf_path.name}")
print(f"📸 Pages to extract: {IMAGE_PAGES}")
print(f"💾 Saving images to: {OUTPUT_DIR}")
print()

# Render pages as images at 3x zoom
print("🖼️  Rendering pages as images (3x zoom = 216 DPI)...")
doc = fitz.open(pdf_path)
images_base64 = []
image_paths = []

for page_num in IMAGE_PAGES:
    if page_num < 1 or page_num > len(doc):
        continue

    page = doc[page_num - 1]

    # Render at 3x zoom (216 DPI)
    mat = fitz.Matrix(3.0, 3.0)
    pix = page.get_pixmap(matrix=mat)

    # Convert to PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Save image for manual inspection
    img_path = OUTPUT_DIR / f"page_{page_num:02d}.png"
    img.save(img_path)
    image_paths.append(img_path)

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    images_base64.append(img_base64)

    print(f"   ✓ Page {page_num}: {pix.width}x{pix.height} px, {len(img_base64)} bytes → {img_path.name}")

doc.close()
print()

# Build vision prompt
prompt = """You are analyzing financial statement pages from a Swedish BRF (Bostadsrättsförening) annual report.

The images show financial statements that may include:
- Resultaträkning (Income Statement)
- Balansräkning (Balance Sheet)
- Kassaflödesanalys (Cash Flow Statement)

Extract ALL financial data you can find. Pay special attention to:

1. Income Statement (Resultaträkning):
   - Intäkter (Revenue) - total and itemized
   - Kostnader (Expenses) - total and itemized
   - Årets resultat (Net income/surplus)

2. Balance Sheet (Balansräkning):
   - Tillgångar (Assets) - total and itemized
   - Skulder (Liabilities) - total and itemized
   - Eget kapital (Equity) - total and components

3. Specific Items:
   - Långfristiga skulder (Long-term debt)
   - Kortfristiga skulder (Short-term debt)
   - Likvida medel (Cash and cash equivalents)
   - Årsavgifter (Annual fees) - if mentioned

Return a JSON object with the following structure:
{
  "financial_agent": {
    "revenue_total": <number or null>,
    "expenses_total": <number or null>,
    "assets_total": <number or null>,
    "liabilities_total": <number or null>,
    "equity_total": <number or null>,
    "net_income": <number or null>,
    "cash_and_equivalents": <number or null>,
    "long_term_debt": <number or null>,
    "short_term_debt": <number or null>
  },
  "loans_agent": [
    {
      "lender": <string or null>,
      "amount": <number or null>,
      "rate": <number or null>
    }
  ],
  "fees_agent": {
    "annual_fee": <number or null>,
    "monthly_fee_range_min": <number or null>,
    "monthly_fee_range_max": <number or null>
  }
}

Important:
- Extract ALL numbers you can find
- Use null for fields not found
- Numbers should be without spaces or commas (e.g., 1500000 not 1 500 000)
- Include currency if mentioned (usually SEK/kr)
- If you see "tkr" (tusen kronor), multiply by 1000
"""

# Call GPT-4o vision
print("🤖 Calling GPT-4o Vision API...")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *[
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                        for img_base64 in images_base64
                    ]
                ]
            }
        ],
        max_tokens=4096,
        temperature=0,
    )

    content = response.choices[0].message.content

    print(f"   ✓ API call successful")
    print(f"   Model: {response.model}")
    print(f"   Tokens: {response.usage.total_tokens} total ({response.usage.prompt_tokens} prompt, {response.usage.completion_tokens} completion)")
    print()

    # Save raw response
    raw_response_path = OUTPUT_DIR / "vision_api_response_raw.txt"
    raw_response_path.write_text(content)
    print(f"💾 Raw response saved to: {raw_response_path.name}")
    print()

    # Show raw response
    print("📄 Raw API Response:")
    print("-" * 80)
    print(content)
    print("-" * 80)
    print()

    # Parse JSON
    import re

    # Try multiple extraction methods
    json_content = None

    # Method 1: Extract from markdown fences
    json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
    if json_match:
        json_content = json_match.group(1)
        print("   ✓ Extracted JSON from markdown fences")
    else:
        # Method 2: Try without DOTALL (in case it's malformed)
        json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
        if json_match:
            json_content = json_match.group(1)
            print("   ✓ Extracted JSON using [\s\S] pattern")
        else:
            # Method 3: Assume the whole content is JSON
            json_content = content
            print("   ⚠️ Using whole content as JSON (no fences detected)")

    content = json_content

    try:
        result = json.loads(content)

        # Save parsed JSON
        json_path = OUTPUT_DIR / "vision_api_response_parsed.json"
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"💾 Parsed JSON saved to: {json_path.name}")
        print()

        # Analyze results
        print("📊 Extracted Data Analysis:")
        print("-" * 80)

        if "financial_agent" in result:
            financial = result["financial_agent"]
            print(f"Financial Agent:")
            non_null_count = sum(1 for v in financial.values() if v is not None)
            print(f"   Non-null fields: {non_null_count}/{len(financial)}")
            for key, value in financial.items():
                status = "✓" if value is not None else "✗"
                print(f"   {status} {key}: {value}")

        print()

        if "loans_agent" in result:
            loans = result["loans_agent"]
            print(f"Loans Agent:")
            print(f"   Loans count: {len(loans)}")
            for i, loan in enumerate(loans, 1):
                print(f"   Loan {i}:")
                for key, value in loan.items():
                    status = "✓" if value is not None else "✗"
                    print(f"      {status} {key}: {value}")

        print()

        if "fees_agent" in result:
            fees = result["fees_agent"]
            print(f"Fees Agent:")
            non_null_count = sum(1 for v in fees.values() if v is not None)
            print(f"   Non-null fields: {non_null_count}/{len(fees)}")
            for key, value in fees.items():
                status = "✓" if value is not None else "✗"
                print(f"   {status} {key}: {value}")

        print("-" * 80)

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"   Content: {content[:500]}...")

except Exception as e:
    print(f"❌ API call failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)
print()
print("📁 Files created:")
for img_path in image_paths:
    print(f"   - {img_path}")
print(f"   - {OUTPUT_DIR / 'vision_api_response_raw.txt'}")
print(f"   - {OUTPUT_DIR / 'vision_api_response_parsed.json'}")
print()
print("🔍 Next steps:")
print("   1. Open the PNG images and verify they're readable")
print("   2. Review the raw API response to see what GPT-4o actually saw")
print("   3. Check if the prompt needs to be more specific")
