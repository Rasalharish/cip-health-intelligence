from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import sys

# Ensure model2 is in path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from model2.deviation_engine import DeviationEngine

app = Flask(__name__)
CORS(app)

# Initialize engine globally
engine = DeviationEngine()

# Load Dataset globally for lab UI
DATASET_PATH = os.path.join(base_dir, 'data', 'raw', 'MODEL2_CIP_HEALTH_TIMESERIES.csv')
lab_df = None
if os.path.exists(DATASET_PATH):
    try:
        lab_df = pd.read_csv(DATASET_PATH)
        # We need a proper timestamp for UI filtering. The raw CSV has Excel serials or string timestamps.
        # But we'll just serve it as is for now, UI can handle it or we can just return it.
    except Exception as e:
        print(f"Failed to load historical dataset: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Model 2 Deviation Engine API is running."})

@app.route('/model2/info', methods=['GET'])
def get_model_info():
    return jsonify({
        "status": "success",
        "method": "Step-aware statistical deviation scoring",
        "baseline": "model2_baseline_v1",
        "technique": "Z-score based deviation",
        "output": "0-100 health score + A-F grade"
    })

@app.route('/model2/dataset/info', methods=['GET'])
def get_dataset_info():
    if lab_df is None:
        return jsonify({"status": "error", "message": "Dataset not loaded."}), 404
        
    return jsonify({
        "status": "success",
        "total_rows": len(lab_df),
        "phe_list": lab_df['phe_id'].dropna().unique().tolist(),
        "step_list": lab_df['process_step'].dropna().unique().tolist(),
        "date_range": [lab_df['timestamp'].min(), lab_df['timestamp'].max()],
        "missing_values": int(lab_df.isnull().sum().sum()),
        "valid_observations": len(lab_df.dropna(subset=['phe_id', 'process_step', 'flow_lph', 'temp_in', 'conductivity']))
    })

@app.route('/model2/dataset/observations', methods=['GET'])
def get_dataset_observations():
    if lab_df is None:
        return jsonify({"status": "error", "message": "Dataset not loaded."}), 404
        
    phe_id = request.args.get('phe_id')
    step = request.args.get('process_step')
    limit = int(request.args.get('limit', 50))
    
    df_filtered = lab_df
    if phe_id:
        df_filtered = df_filtered[df_filtered['phe_id'] == phe_id]
    if step:
        df_filtered = df_filtered[df_filtered['process_step'] == step]
        
    # Return a sample or top limit
    sample_df = df_filtered.head(limit)
    import json
    
    return jsonify({
        "status": "success",
        "observations": json.loads(sample_df.to_json(orient='records'))
    })

@app.route('/model2/dataset/trend', methods=['GET'])
def get_dataset_trend():
    if lab_df is None:
        return jsonify({"status": "error", "message": "Dataset not loaded."}), 404
        
    phe_id = request.args.get('phe_id')
    step = request.args.get('process_step')
    
    df_filtered = lab_df
    if phe_id:
        df_filtered = df_filtered[df_filtered['phe_id'] == phe_id]
    if step:
        df_filtered = df_filtered[df_filtered['process_step'] == step]
        
    # To avoid crashing the browser with 47k points, downsample if > 1000
    if len(df_filtered) > 1000:
        # uniform sampling
        step_size = len(df_filtered) // 1000
        df_filtered = df_filtered.iloc[::step_size]
        
    results = []
    for _, row in df_filtered.iterrows():
        obs = row.to_dict()
        if pd.isna(obs.get('process_step')) or pd.isna(obs.get('phe_id')):
            continue
        res = engine.evaluate(obs)
        if res['status'] == 'success':
            results.append({
                "timestamp": obs.get('timestamp'),
                "health_score": res['health_score'],
                "grade": res['grade']
            })
            
    return jsonify({
        "status": "success",
        "trend": results
    })

@app.route('/model2/score', methods=['POST'])
def score_single():
    obs = request.json
    if not obs:
        return jsonify({"status": "error", "message": "No observation provided"}), 400
        
    result = engine.evaluate(obs)
    return jsonify(result)

@app.route('/model2/batch', methods=['POST'])
def score_batch():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400
        
    try:
        df = pd.read_csv(file)
        results = []
        for _, row in df.iterrows():
            obs = row.to_dict()
            if 'phe_id' not in obs:
                obs['phe_id'] = 'PHE01'
                
            res = engine.evaluate(obs)
            results.append(res)
            
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/model2/batch_dataset', methods=['POST'])
def score_batch_dataset():
    if lab_df is None:
        return jsonify({"status": "error", "message": "Dataset not loaded."}), 404
        
    try:
        results = []
        for _, row in lab_df.iterrows():
            obs = row.to_dict()
            if pd.isna(obs.get('process_step')) or pd.isna(obs.get('phe_id')):
                continue
                
            res = engine.evaluate(obs)
            if res['status'] == 'success':
                results.append({
                    "timestamp": obs.get('timestamp'),
                    "phe_id": obs.get('phe_id'),
                    "process_step": obs.get('process_step'),
                    "health_score": res['health_score'],
                    "grade": res['grade'],
                    "data_coverage": res['data_coverage'],
                    "status": "SUCCESS",
                    "top_deviation_feature": res['top_deviations'][0].split(':')[0] if res['top_deviations'] else "None",
                    "top_deviation_magnitude": res['top_deviations'][0].split(':')[1].strip() if res['top_deviations'] else "0"
                })
        
        # In a real app we'd save this to a file and return a link.
        # For this local lab, we can return the JSON and let the UI trigger a download.
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
@app.route('/model2/features', methods=['GET'])
def get_features():
    return jsonify({
        "status": "success",
        "features": engine.loader.features
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

