import requests
import time
import json
import sys

print('=== 1. Environment & API Test ===')
try:
    r = requests.get('http://127.0.0.1:5000/health')
    print('/health ->', r.status_code, r.json())
except Exception as e:
    print('Error:', e)
    sys.exit(1)

print('\n=== 2. Dataset Load & Info Test ===')
t0 = time.time()
r = requests.get('http://127.0.0.1:5000/model2/dataset/info')
load_time = time.time() - t0
info = r.json()
print(f'Dataset info loaded in {load_time:.4f}s')
print(f'Rows: {info.get("total_rows")}')
print(f'Missing: {info.get("missing_values")}')
print(f'PHE List: {info.get("phe_list")[:3]}...')
print(f'Steps: {info.get("step_list")[:3]}...')
print(f'Range: {info.get("date_range")}')

print('\n=== 3. Observation Selector ===')
r = requests.get('http://127.0.0.1:5000/model2/dataset/observations?limit=5')
obs_list = r.json().get('observations', [])
print(f'Fetched {len(obs_list)} observations.')
obs0 = {k: (None if (isinstance(v, float) and v != v) else v) for k, v in obs_list[0].items()}
print('Observation 0:', obs0['phe_id'], obs0['process_step'], 'flow=', obs0['flow_lph'])

print('\n=== 4 & 5. Real Observation Analysis ===')
t0 = time.time()
r = requests.post('http://127.0.0.1:5000/model2/score', json=obs0)
score_time = time.time() - t0
res = r.json()
print(f'Score generated in {score_time:.4f}s')
print('Score:', res.get('health_score'), 'Grade:', res.get('grade'))
print('Top dev:', str(res.get('top_deviations')).encode('ascii', 'ignore').decode())
print('Baseline mean for flow:', res['baseline_stats'].get('flow_lph', {}).get('mean'))
print('Dev for flow:', res['raw_deviations'].get('flow_lph'))

print('\n=== 13. Batch Analysis Test ===')
t0 = time.time()
r = requests.post('http://127.0.0.1:5000/model2/batch_dataset')
batch_time = time.time() - t0
batch = r.json()
print(f'Batch processed in {batch_time:.4f}s')
print(f'Batch results count: {len(batch.get("results", []))}')

print('\n=== 16. Unknown Step ===')
bad_obs = obs0.copy()
bad_obs['process_step'] = 'INVALID_STEP'
r = requests.post('http://127.0.0.1:5000/model2/score', json=bad_obs)
print('Unknown step response:', r.json().get('status'), r.json().get('message'))

with open('api_test_results.json', 'w') as f:
    json.dump({
        'load_time': load_time,
        'score_time': score_time,
        'batch_time': batch_time,
        'rows': info.get('total_rows'),
        'batch_results': len(batch.get('results', []))
    }, f)
