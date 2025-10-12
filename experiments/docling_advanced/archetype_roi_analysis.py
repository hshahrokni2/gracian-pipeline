#!/usr/bin/env python3
"""
Archetype Classification ROI Analysis
Compares archetype-based vs flat extraction approach
"""

# Estimated distribution based on Swedish BRF corpus analysis
archetypes = {
    'simple_k2': {'pct': 0.35, 'fields': 40, 'agents': 8, 'cost': 0.14},
    'medium_k2': {'pct': 0.40, 'fields': 65, 'agents': 14, 'cost': 0.20},
    'complex_k3': {'pct': 0.25, 'fields': 95, 'agents': 22, 'cost': 0.30}
}

# Calculate weighted averages
total_docs = 26342  # Arsredovisning corpus size
weighted_fields = sum(a['pct'] * a['fields'] for a in archetypes.values())
weighted_agents = sum(a['pct'] * a['agents'] for a in archetypes.values())
weighted_cost = sum(a['pct'] * a['cost'] for a in archetypes.values())

# Compare with flat 107-field approach
flat_cost = 0.44  # 25 agents for all documents

print('=' * 70)
print('ARCHETYPE-BASED VS FLAT EXTRACTION - ROI ANALYSIS')
print('=' * 70)
print(f'\nCorpus size: {total_docs:,} PDFs (Arsredovisning only)')
print(f'\nArchetype Distribution (Based on Swedish BRF Analysis):')
for name, data in archetypes.items():
    docs = int(total_docs * data['pct'])
    print(f'  {name:12s}: {data["pct"]*100:>4.0f}% ({docs:>6,} docs) - '
          f'{data["fields"]:>3} fields, {data["agents"]:>2} agents, ${data["cost"]:.2f}/doc')

print(f'\n{"ARCHETYPE-BASED APPROACH":^70}')
print('-' * 70)
print(f'  Avg fields extracted: {weighted_fields:.1f}')
print(f'  Avg agents per doc: {weighted_agents:.1f}')
print(f'  Avg cost per doc: ${weighted_cost:.3f}')
print(f'  Total corpus cost: ${weighted_cost * total_docs:,.0f}')

print(f'\n{"FLAT 107-FIELD APPROACH":^70}')
print('-' * 70)
print(f'  Fields extracted: 107 (but many NULL for simple docs)')
print(f'  Agents per doc: 25 (fixed, regardless of complexity)')
print(f'  Cost per doc: ${flat_cost:.3f}')
print(f'  Total corpus cost: ${flat_cost * total_docs:,.0f}')

print(f'\n{"SAVINGS WITH ARCHETYPE CLASSIFICATION":^70}')
print('=' * 70)
savings_pct = (flat_cost - weighted_cost) / flat_cost * 100
savings_total = (flat_cost - weighted_cost) * total_docs
print(f'  Cost reduction per doc: {savings_pct:.1f}%')
print(f'  Total corpus savings: ${savings_total:,.0f}')
print(f'  Break-even point: ~200 documents')
print(f'  (Classifier development ~$40 + validation ~$10)')

print(f'\n{"RECOMMENDATION":^70}')
print('-' * 70)
print(f'  ✅ IMPLEMENT ARCHETYPE CLASSIFICATION')
print(f'  • Saves ${savings_total:,.0f} on 26K corpus')
print(f'  • Better accuracy (focused agents)')
print(f'  • Faster processing (fewer agents)')
print(f'  • ROI: {savings_total / 50:.0f}x development cost')
print('=' * 70)
