import pytest
import os
import sys
import json
from io import BytesIO

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from api.app import app, engine, lab_df

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    assert b'Model 2 Deviation Engine API is running' in rv.data

def test_model_info_endpoint(client):
    rv = client.get('/model2/info')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'success'
    assert 'baseline' in data
    assert 'method' in data

def test_dataset_info_endpoint(client):
    rv = client.get('/model2/dataset/info')
    if lab_df is not None:
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'success'
        assert 'total_rows' in data
    else:
        assert rv.status_code == 404

def test_score_single_endpoint(client):
    # Fetch stats for PHE01 CAUSTIC
    stats = engine.loader.get_baseline_for('PHE01', 'CAUSTIC')
    if not stats:
        pytest.skip("No baseline found for PHE01 CAUSTIC")
        
    obs = {
        'phe_id': 'PHE01',
        'process_step': 'CAUSTIC',
        'flow_lph': stats['flow_lph']['mean'],
        'temp_in': stats['temp_in']['mean'],
        'conductivity': stats['conductivity']['mean']
    }
    
    rv = client.post('/model2/score', json=obs)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'success'
    assert data['health_score'] >= 90
    assert 'baseline_stats' in data

def test_batch_upload_endpoint(client):
    # Create a small CSV string
    csv_data = "phe_id,process_step,flow_lph,temp_in,conductivity\nPHE01,CAUSTIC,30000,90,140\n"
    data = {
        'file': (BytesIO(csv_data.encode('utf-8')), 'test.csv')
    }
    
    rv = client.post('/model2/batch', data=data, content_type='multipart/form-data')
    assert rv.status_code == 200
    resp = json.loads(rv.data)
    assert resp['status'] == 'success'
    assert len(resp['results']) == 1
    assert resp['results'][0]['status'] == 'success'

def test_batch_dataset_endpoint(client):
    rv = client.post('/model2/batch_dataset')
    if lab_df is not None:
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['status'] == 'success'
        assert len(data['results']) > 0
    else:
        assert rv.status_code == 404

def test_unknown_step_endpoint(client):
    obs = {
        'phe_id': 'PHE01',
        'process_step': 'UNKNOWN_STEP',
        'flow_lph': 10000
    }
    
    rv = client.post('/model2/score', json=obs)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'error'
    assert 'No baseline data' in data['message']
