"""
Diagnostic script to understand field path mismatches between ground truth and extraction.
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env')
sys.path.insert(0, str(Path(__file__).parent))

from gracian_pipeline.core.docling_adapter_ultra_v2 import RobustUltraComprehensiveExtractor


def flatten_dict(d, parent_key='', sep='.'):
    """Simple flatten without special logic"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict) and not ('value' in v and len(v) <= 3):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))

    return dict(items)


print("\n" + "="*80)
print("FIELD PATH DIAGNOSTIC")
print("="*80)

# Load ground truth
print("\n📋 Loading ground truth...")
with open("ground_truth/brf_198532_comprehensive_ground_truth.json", 'r') as f:
    gt = json.load(f)

# Run extraction
print("📄 Running extraction...")
extractor = RobustUltraComprehensiveExtractor()
result = extractor.extract_brf_document("SRS/brf_198532.pdf", mode="fast")

# Flatten both
print("\n🔍 Flattening structures...")
gt_flat = flatten_dict(gt)
result_flat = flatten_dict(result)

# Filter out metadata fields
gt_flat = {k: v for k, v in gt_flat.items() if not k.startswith('_')}
result_flat = {k: v for k, v in result_flat.items() if not k.startswith('_')}

print(f"\nGround Truth: {len(gt_flat)} fields")
print(f"Extraction: {len(result_flat)} fields")

# Show samples
print("\n" + "="*80)
print("SAMPLE GROUND TRUTH PATHS (first 30):")
print("="*80)
for i, (path, value) in enumerate(list(gt_flat.items())[:30]):
    print(f"{i+1:3d}. {path:60s} = {str(value)[:40]}")

print("\n" + "="*80)
print("SAMPLE EXTRACTION PATHS (first 30):")
print("="*80)
for i, (path, value) in enumerate(list(result_flat.items())[:30]):
    # Handle ExtractionField wrapper
    display_value = value.get('value', value) if isinstance(value, dict) else value
    print(f"{i+1:3d}. {path:60s} = {str(display_value)[:40]}")

# Find exact matches
print("\n" + "="*80)
print("EXACT PATH MATCHES:")
print("="*80)
exact_matches = set(gt_flat.keys()) & set(result_flat.keys())
print(f"\nFound {len(exact_matches)} exact matches:")
for i, path in enumerate(list(exact_matches)[:20]):
    print(f"{i+1:3d}. {path}")

# Find partial matches (same field name, different path)
print("\n" + "="*80)
print("FIELD NAME ANALYSIS (why aren't they matching?):")
print("="*80)

# Extract just field names from paths
gt_field_names = {path.split('.')[-1]: path for path in gt_flat.keys()}
result_field_names = {path.split('.')[-1]: path for path in result_flat.keys()}

# Show examples where field name exists in both but path is different
print("\nSame field name, different paths:")
for field_name in list(gt_field_names.keys())[:15]:
    if field_name in result_field_names:
        gt_path = gt_field_names[field_name]
        result_path = result_field_names[field_name]
        if gt_path != result_path:
            print(f"\nField: {field_name}")
            print(f"  GT path:     {gt_path}")
            print(f"  Result path: {result_path}")

print("\n" + "="*80)
