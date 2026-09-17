import json
import os
import sys
import time
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from model2.deviation_engine import DeviationEngine

def run_checks():
    print("--- STARTING CHECKS ---")
    engine = DeviationEngine()
    
    stats = engine.loader.get_baseline_for('PHE01', 'CAUSTIC')
    
    # 5. Z-SCORE SANITY CHECK
    print("\n[Z-SCORE SANITY]")
    mean_val = stats['temp_in']['mean']
    std_val = stats['temp_in']['std']
    
    obs = {
        'phe_id': 'PHE01', 'process_step': 'CAUSTIC',
        'temp_in': mean_val
    }
    res = engine.evaluate(obs)
    print(f"x = mean => z = {res['raw_deviations'].get('temp_in')}")
    
    obs['temp_in'] = mean_val + std_val
    res = engine.evaluate(obs)
    print(f"x = mean + 1 std => z = {res['raw_deviations'].get('temp_in')}")
    
    obs['temp_in'] = mean_val - std_val
    res = engine.evaluate(obs)
    print(f"x = mean - 1 std => z = {res['raw_deviations'].get('temp_in')}")

    # 6. HEALTH SCORE SANITY
    print("\n[HEALTH SCORE SANITY]")
    obs_normal = {
        'phe_id': 'PHE01', 'process_step': 'CAUSTIC',
        'flow_lph': stats['flow_lph']['mean'],
        'temp_in': stats['temp_in']['mean']
    }
    print(f"Baseline: {engine.evaluate(obs_normal)['health_score']}")
    
    obs_small = obs_normal.copy()
    obs_small['temp_in'] = stats['temp_in']['mean'] + (stats['temp_in']['std'] * 1.5)
    print(f"Small dev (1.5s): {engine.evaluate(obs_small)['health_score']}")
    
    obs_large = obs_normal.copy()
    obs_large['temp_in'] = stats['temp_in']['mean'] + (stats['temp_in']['std'] * 5.0)
    print(f"Large dev (5.0s): {engine.evaluate(obs_large)['health_score']}")

    obs_combined = obs_large.copy()
    obs_combined['flow_lph'] = stats['flow_lph']['mean'] - (stats['flow_lph']['std'] * 3.0)
    print(f"Combined dev (5.0s temp + 3.0s flow): {engine.evaluate(obs_combined)['health_score']}")

    # 14. PERFORMANCE BENCHMARK
    print("\n[PERFORMANCE]")
    df = pd.read_csv(os.path.join(base_dir, 'data', 'processed', 'model2_clean_timeseries_segmented.csv'))
    
    start_time = time.time()
    
    # Run subset if dataset is too huge for python pure loop, but 47k is fine
    valid_obs = 0
    scored_obs = 0
    for idx, row in df.iterrows():
        o = row.to_dict()
        # Some rows might not have baseline if sample count was < 10
        r = engine.evaluate(o)
        if r['status'] == 'success':
            scored_obs += 1
        valid_obs += 1
            
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / valid_obs if valid_obs > 0 else 0
    
    print(f"Number of observations: {valid_obs}")
    print(f"Successfully Scored observations (has baseline): {scored_obs}")
    print(f"Processing time: {total_time:.4f} seconds")
    print(f"Average time per observation: {avg_time:.6f} seconds")

if __name__ == "__main__":
    run_checks()
