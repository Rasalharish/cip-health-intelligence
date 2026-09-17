import pandas as pd
import os

def engineer_features(df):
    # Sort just in case
    df = df.sort_values(by=['phe_id', 'timestamp'])
    
    # 1. Target deviation
    if 'temp_in' in df.columns and 'sterilization_sp' in df.columns:
        df['temp_error'] = df['temp_in'] - df['sterilization_sp']
        
    # 2. Step duration (time elapsed since step start)
    # We use segment_id from previous step to group
    if 'segment_id' in df.columns:
        df['step_duration_s'] = df.groupby('segment_id')['timestamp'].transform(lambda x: x - x.min())
        
    # 3. Rolling statistics (window of 5 periods as an example)
    # Group by segment to not mix rolling stats across different steps
    if 'flow_lph' in df.columns:
        df['flow_rolling_mean'] = df.groupby('segment_id')['flow_lph'].transform(lambda x: x.rolling(window=5, min_periods=1).mean())
        df['flow_rolling_std'] = df.groupby('segment_id')['flow_lph'].transform(lambda x: x.rolling(window=5, min_periods=1).std().fillna(0))
        
    if 'temp_in' in df.columns:
        df['temp_in_rolling_mean'] = df.groupby('segment_id')['temp_in'].transform(lambda x: x.rolling(window=5, min_periods=1).mean())
    
    if 'conductivity' in df.columns:
        df['cond_rolling_mean'] = df.groupby('segment_id')['conductivity'].transform(lambda x: x.rolling(window=5, min_periods=1).mean())

    # 4. Trend (Rate of change)
    if 'temp_in' in df.columns:
        df['temp_in_roc'] = df.groupby('segment_id')['temp_in'].diff() / df.groupby('segment_id')['timestamp'].diff()
        df['temp_in_roc'] = df['temp_in_roc'].fillna(0)
        
    return df

def select_features(df):
    # Selecting core features for Model 2 based on provided guidelines
    # We include available variables from the dataset.
    core_features = [
        'timestamp',
        'phe_id',
        'cip_run_id',
        'process_step',
        'segment_id',
        'step_duration_s',
        'flow_lph',
        'temp_in',
        'sterilization_sp',
        'temp_error',
        'conductivity',
        'steam_pressure',
        'flow_rolling_mean',
        'flow_rolling_std',
        'temp_in_rolling_mean',
        'cond_rolling_mean',
        'temp_in_roc'
    ]
    
    # Filter to only columns that actually exist in the dataframe
    selected_cols = [col for col in core_features if col in df.columns]
    return df[selected_cols]

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    segmented_path = os.path.join(base_dir, 'data', 'processed', 'model2_clean_timeseries_segmented.csv')
    df = pd.read_csv(segmented_path)
    
    df_features = engineer_features(df)
    df_selected = select_features(df_features)
    
    features_path = os.path.join(base_dir, 'data', 'processed', 'model2_features.csv')
    df_selected.to_csv(features_path, index=False)
    
    # Document selected features
    report = {
        "selected_features": df_selected.columns.tolist(),
        "reasoning": "Selected core features matching guidelines: flow, temperature, conductivity, pressure, and engineered features (error, duration, rolling stats, ROC). Avoided operator metadata and duplicate/broken signals."
    }
    
    report_path = os.path.join(base_dir, 'data', 'reports', 'feature_selection_report.json')
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)
        
    print("Feature engineering step complete")
