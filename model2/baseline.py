import pandas as pd
import json
import os
import datetime

def generate_baseline(df):
    features_to_baseline = [
        'flow_lph', 'temp_in', 'sterilization_sp', 'temp_error',
        'conductivity', 'steam_pressure', 'flow_rolling_mean',
        'temp_in_rolling_mean', 'cond_rolling_mean', 'temp_in_roc'
    ]
    
    baseline_stats = {}
    
    # Filter only available columns
    available_features = [f for f in features_to_baseline if f in df.columns]
    
    # Group by PHE and Process Step
    grouped = df.groupby(['phe_id', 'process_step'])
    
    for (phe_id, step), group in grouped:
        key = f"{phe_id}_{step}"
        baseline_stats[key] = {}
        
        for feature in available_features:
            # We only calculate stats if there are at least 10 non-null values
            if group[feature].count() >= 10:
                baseline_stats[key][feature] = {
                    'mean': float(group[feature].mean()),
                    'median': float(group[feature].median()),
                    'std': float(group[feature].std()),
                    'min': float(group[feature].min()),
                    'max': float(group[feature].max()),
                    'count': int(group[feature].count())
                }
                
    return baseline_stats, available_features

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    features_path = os.path.join(base_dir, 'data', 'processed', 'model2_features.csv')
    df = pd.read_csv(features_path)
    
    baseline_stats, features = generate_baseline(df)
    
    baseline_artifact = {
        "model_version": "1.0",
        "creation_timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "dataset_version": "1.0",
        "selected_features": features,
        "grouping_strategy": "PHE_ID + CIP_STEP + FEATURE",
        "minimum_sample_requirements": 10,
        "configuration": {
            "deviation_metric": "z-score",
            "health_score_method": "weighted_standard_deviation"
        },
        "health_thresholds": {
            "healthy_z_score_max": 2.0,
            "warning_z_score_max": 3.0
        },
        "feature_weights": {
            f: 1.0 for f in features # Equal weights initially
        },
        "limitations": "Provisional baseline until plant-verified normal CIP cycles are available. Assumes data represents normal completed operation.",
        "baseline_statistics": baseline_stats
    }
    
    artifact_path = os.path.join(base_dir, 'models', 'model2_baseline_v1.json')
    with open(artifact_path, 'w') as f:
        json.dump(baseline_artifact, f, indent=4)
        
    print("Baseline generation complete")
