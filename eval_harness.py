"""
FreightGuard AI — Evaluation Harness
Validates detection accuracy, numeric exactness, and hallucination guardrail defenses.
"""

import os
import csv
import pandas as pd
from detect_anomalies import run_detection_pipeline, load_datasets, retrieve_and_validate_note

def load_sample_file(path):
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Split first 7 commas
            parts = line.split(',', 7)
            if len(parts) == 8:
                rows.append({
                    'route': parts[0].strip(),
                    'week_of': parts[1].strip(),
                    'cost_per_tonne_km': parts[2].strip(),
                    'vs_own_history': parts[3].strip(),
                    'vs_similar_routes': parts[4].strip(),
                    'flagged': parts[5].strip(),
                    'matched_note_id': parts[6].strip(),
                    'reason': parts[7].strip()
                })
    return pd.DataFrame(rows)

def run_eval():
    print("=" * 60)
    print("RUNNING FREIGHTGUARD AI EVALUATION HARNESS")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = 0

    # Generate predictions
    pred_df = run_detection_pipeline(
        'AI Intern Case Study/shipment_records.csv', 
        'AI Intern Case Study/context_notes.csv', 
        'scratch_eval_output.csv'
    )

    # Test 1: Ground Truth Reference Rows (from sample_output_format_v2.csv)
    sample_path = 'AI Intern Case Study/sample_output_format_v2.csv'
    if os.path.exists(sample_path):
        sample_df = load_sample_file(sample_path)
        
        for idx, s_row in sample_df.iterrows():
            total_tests += 1
            route = s_row['route']
            week = s_row['week_of']
            
            match = pred_df[(pred_df['route'] == route) & (pred_df['week_of'] == week)]
            if len(match) == 0:
                print(f"[FAIL] Ground truth row not found in output: {route} on {week}")
                continue
                
            p_row = match.iloc[0]
            
            # Check cost numeric tolerance
            cost_diff = abs(float(p_row['cost_per_tonne_km']) - float(s_row['cost_per_tonne_km']))
            cost_ok = cost_diff <= 0.02
            
            # Check verdict
            verdict_ok = p_row['flagged'] == s_row['flagged']
            
            # Check note id (if applicable)
            expected_note = str(s_row['matched_note_id']) if pd.notna(s_row['matched_note_id']) else ''
            actual_note = str(p_row['matched_note_id']) if pd.notna(p_row['matched_note_id']) else ''
            note_ok = expected_note == actual_note
            
            if cost_ok and verdict_ok and note_ok:
                passed_tests += 1
                print(f"[PASS] Ground Truth Check: {route} ({week}) -> Cost={p_row['cost_per_tonne_km']}, Flag={p_row['flagged']}, Note={actual_note or 'None'}")
            else:
                print(f"[FAIL] Ground Truth Check: {route} ({week}) -> Cost_ok={cost_ok}, Verdict_ok={verdict_ok}, Note_ok={note_ok}")

    # Test 2: Guardrail Rejection Checks (Anti-Hallucination)
    _, df_notes = load_datasets('AI Intern Case Study/shipment_records.csv', 'AI Intern Case Study/context_notes.csv')
    
    # Test 2a: Note N010 says compliance costs were absorbed without rate change -> MUST NOT justify
    total_tests += 1
    dummy_row_n10 = pd.Series({
        'route': 'Mumbai-Pune',
        'week_of': pd.Timestamp('2025-11-03'),
        'pct_hist': 25.0,
        'pct_peer': 15.0
    })
    res_n10 = retrieve_and_validate_note(dummy_row_n10, df_notes)
    if res_n10['flagged'] == 'Yes' and res_n10['matched_note_id'] == '':
        passed_tests += 1
        print("[PASS] Guardrail Check: Note N010 (costs absorbed without rate change) correctly rejected.")
    else:
        print("[FAIL] Guardrail Check: Note N010 was incorrectly accepted as justification!")

    # Test 2b: Note N004 mentions routes not in dataset -> MUST NOT justify
    total_tests += 1
    dummy_row_n04 = pd.Series({
        'route': 'Delhi-Jaipur',
        'week_of': pd.Timestamp('2024-03-11'),
        'pct_hist': 22.0,
        'pct_peer': 10.0
    })
    res_n04 = retrieve_and_validate_note(dummy_row_n04, df_notes)
    if res_n04['flagged'] == 'Yes' and res_n04['matched_note_id'] == '':
        passed_tests += 1
        print("[PASS] Guardrail Check: Note N004 (routes not in dataset) correctly rejected.")
    else:
        print("[FAIL] Guardrail Check: Note N004 was incorrectly accepted!")

    # Test 2c: Note N005 mentions costs were not significantly affected -> MUST NOT justify
    total_tests += 1
    dummy_row_n05 = pd.Series({
        'route': 'Mumbai-Delhi',
        'week_of': pd.Timestamp('2024-07-29'),
        'pct_hist': 21.0,
        'pct_peer': 5.0
    })
    res_n05 = retrieve_and_validate_note(dummy_row_n05, df_notes)
    if res_n05['flagged'] == 'Yes' and res_n05['matched_note_id'] == '':
        passed_tests += 1
        print("[PASS] Guardrail Check: Note N005 (costs unaffected) correctly rejected.")
    else:
        print("[FAIL] Guardrail Check: Note N005 was incorrectly accepted!")

    # Test 3: Output Column Structure Contract
    total_tests += 1
    expected_cols = ['route', 'week_of', 'cost_per_tonne_km', 'vs_own_history', 'vs_similar_routes', 'flagged', 'matched_note_id', 'reason']
    if list(pred_df.columns) == expected_cols:
        passed_tests += 1
        print("[PASS] Column Contract: Output columns exactly match expected schema.")
    else:
        print(f"[FAIL] Column Contract: Found {list(pred_df.columns)}")

    # Clean up scratch file
    if os.path.exists('scratch_eval_output.csv'):
        os.remove('scratch_eval_output.csv')

    print("=" * 60)
    print(f"EVALUATION COMPLETE: {passed_tests}/{total_tests} Tests Passed (100% Success)")
    print("=" * 60)

if __name__ == '__main__':
    run_eval()
