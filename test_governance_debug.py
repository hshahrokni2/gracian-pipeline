#!/usr/bin/env python3
"""Test governance agent extraction with debug logging."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from gracian_pipeline.core.parallel_orchestrator import extract_all_agents_parallel

# Load environment variables
load_dotenv()

pdf_path = 'data/raw_pdfs/Hjorthagen/brf_81563.pdf'

print('Testing parallel orchestrator with debug logging...')
print(f'PDF: {pdf_path}')
print()

# Test on just governance agents with verbose=True
result = extract_all_agents_parallel(
    pdf_path,
    max_workers=1,  # Sequential for cleaner logs
    enable_retry=False,
    verbose=True
)

print()
print('=== RESULTS ===')

# Check governance agents
governance_agents = ['chairman_agent', 'board_members_agent', 'auditor_agent']
for agent_id in governance_agents:
    agent_result = result.get(agent_id, {})
    print(f'\n{agent_id}:')
    print(f'  Data extracted: {bool(agent_result)}')
    if agent_result:
        print(f'  Raw result: {agent_result}')
    else:
        print('  ❌ NO DATA EXTRACTED')
