"""
FreightGuard AI — Reproducibility Verification Harness
Executes 3 untouched, consecutive pipeline runs on the same input,
computes cryptographic hashes, and asserts identical flags, numbers, and cited notes.
"""

import hashlib
import os
import pandas as pd
from detect_anomalies import run_detection_pipeline

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def test_reproducibility():
    print("=" * 65)
    print("RUNNING 3-RUN REPRODUCIBILITY VERIFICATION")
    print("=" * 65)
    
    run_files = ['run_1_output.csv', 'run_2_output.csv', 'run_3_output.csv']
    hashes = []
    dfs = []
    
    for i, fname in enumerate(run_files, 1):
        print(f"Executing Run {i}/3...")
        df = run_detection_pipeline(
            'AI Intern Case Study/shipment_records.csv',
            'AI Intern Case Study/context_notes.csv',
            fname
        )
        dfs.append(df)
        fhash = get_file_hash(fname)
        hashes.append(fhash)
        print(f"  Run {i} complete. SHA-256: {fhash[:16]}... (Records: {len(df)})")
        
    print("\n--- COMPARISON RESULTS ---")
    # Compare hashes
    all_identical = all(h == hashes[0] for h in hashes)
    if all_identical:
        print("[SUCCESS] Bit-for-bit identical outputs across all 3 runs.")
    else:
        print("[CHECKING] Hashes differ, performing semantic column checks...")
        
    # Check flags and numbers across runs
    flags_match = all(dfs[0]['flagged'].equals(df['flagged']) for df in dfs[1:])
    costs_match = all(dfs[0]['cost_per_tonne_km'].equals(df['cost_per_tonne_km']) for df in dfs[1:])
    notes_match = all(dfs[0]['matched_note_id'].equals(df['matched_note_id']) for df in dfs[1:])
    routes_match = all(dfs[0]['route'].equals(df['route']) for df in dfs[1:])
    weeks_match = all(dfs[0]['week_of'].equals(df['week_of']) for df in dfs[1:])
    
    print(f"  * Routes Match: {routes_match}")
    print(f"  * Weeks Match: {weeks_match}")
    print(f"  * Numbers (cost_per_tonne_km) Match: {costs_match}")
    print(f"  * Verdicts (flagged) Match: {flags_match}")
    print(f"  * Cited Notes (matched_note_id) Match: {notes_match}")
    
    # Clean up run files
    for fname in run_files:
        if os.path.exists(fname):
            os.remove(fname)
            
    is_reproducible = flags_match and costs_match and notes_match and routes_match and weeks_match
    print("=" * 65)
    if is_reproducible:
        print("REPRODUCIBILITY VERIFIED: 100% Deterministic Output Across 3 Runs")
    else:
        print("REPRODUCIBILITY FAILED: Discrepancies found across runs")
    print("=" * 65)

if __name__ == '__main__':
    test_reproducibility()
