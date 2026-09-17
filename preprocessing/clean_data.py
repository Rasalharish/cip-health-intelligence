import pandas as pd
import os

def clean_data(df):
    # Normalize column names (already fairly normal, but let's make sure)
    df.columns = df.columns.str.lower().str.strip()
    
    # Retain essential columns
    essential_columns = [
        'timestamp', 'phe_id', 'cip_run_id', 'process_step', 'step_code', 
        'status', 'flow_lph', 'temp_in', 'conductivity', 'steam_pressure',
        'sterilization_sp'
    ]
    
    # Ensure columns exist before filtering
    retained_cols = [col for col in essential_columns if col in df.columns]
    
    # We will NOT fillna(0) as per instructions. Missingness is retained.
    clean_df = df[retained_cols].copy()
    
    return clean_df

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, 'data', 'raw', 'MODEL2_CIP_HEALTH_TIMESERIES.csv')
    df = pd.read_csv(raw_path)
    
    clean_df = clean_data(df)
    
    processed_path = os.path.join(base_dir, 'data', 'processed', 'model2_clean_timeseries.csv')
    clean_df.to_csv(processed_path, index=False)
    
    print("Clean step complete")
