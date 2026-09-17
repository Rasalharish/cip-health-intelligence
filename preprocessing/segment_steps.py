import pandas as pd
import os

def segment_steps(df):
    # Sort by timestamp
    df = df.sort_values(by=['phe_id', 'timestamp'])
    
    segments = []
    
    # We will segment by continuous blocks of the same cip_run_id and process_step
    # Note: Using `shift()` to identify changes
    df['step_change'] = (
        (df['process_step'] != df['process_step'].shift(1)) |
        (df['cip_run_id'] != df['cip_run_id'].shift(1)) |
        (df['phe_id'] != df['phe_id'].shift(1))
    ).astype(int)
    
    df['segment_id'] = df['step_change'].cumsum()
    
    for seg_id, group in df.groupby('segment_id'):
        start_time = group['timestamp'].min()
        end_time = group['timestamp'].max()
        duration = end_time - start_time
        num_obs = len(group)
        state = group['process_step'].iloc[0]
        phe = group['phe_id'].iloc[0]
        run_id = group['cip_run_id'].iloc[0]
        
        segments.append({
            'cip_run_id': run_id,
            'segment_id': seg_id,
            'phe_id': phe,
            'cip_state': state,
            'start_time': start_time,
            'end_time': end_time,
            'duration_s': duration,
            'num_observations': num_obs
        })
        
    segments_df = pd.DataFrame(segments)
    return segments_df, df

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clean_path = os.path.join(base_dir, 'data', 'processed', 'model2_clean_timeseries.csv')
    df = pd.read_csv(clean_path)
    
    segments_df, df_with_segs = segment_steps(df)
    
    segments_path = os.path.join(base_dir, 'data', 'processed', 'model2_step_segments.csv')
    segments_df.to_csv(segments_path, index=False)
    
    # Save the dataframe with segment IDs for feature engineering
    df_with_segs_path = os.path.join(base_dir, 'data', 'processed', 'model2_clean_timeseries_segmented.csv')
    df_with_segs.to_csv(df_with_segs_path, index=False)
    
    print("Segmentation step complete")
