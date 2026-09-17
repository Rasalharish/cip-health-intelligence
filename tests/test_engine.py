import json
import os
import sys

# Ensure we can import model2
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from model2.deviation_engine import DeviationEngine

def run_tests():
    engine = DeviationEngine()
    
    # Let's get the baseline for PHE01 CAUSTIC to see what a normal observation looks like
    stats = engine.loader.get_baseline_for('PHE01', 'CAUSTIC')
    
    if not stats:
        print("Error: Could not load baseline for PHE01 CAUSTIC")
        return
        
    print("--- SCENARIO 1: NORMAL OBSERVATION ---")
    normal_obs = {
        'phe_id': 'PHE01',
        'process_step': 'CAUSTIC',
        'flow_lph': stats['flow_lph']['mean'],
        'temp_in': stats['temp_in']['mean'],
        'conductivity': stats['conductivity']['mean']
    }
    
    res1 = engine.evaluate(normal_obs)
    print(json.dumps(res1, indent=2))
    
    print("\n--- SCENARIO 2: HIGH TEMPERATURE ANOMALY ---")
    # Increase temp_in by 4 standard deviations
    high_temp_obs = normal_obs.copy()
    high_temp_obs['temp_in'] += (stats['temp_in']['std'] * 4)
    
    res2 = engine.evaluate(high_temp_obs)
    print(json.dumps(res2, indent=2))
    
    print("\n--- SCENARIO 3: UNKNOWN STEP ---")
    unknown_obs = {
        'phe_id': 'PHE01',
        'process_step': 'MAGIC_STEP',
        'flow_lph': 10000
    }
    res3 = engine.evaluate(unknown_obs)
    print(json.dumps(res3, indent=2))

if __name__ == "__main__":
    run_tests()
