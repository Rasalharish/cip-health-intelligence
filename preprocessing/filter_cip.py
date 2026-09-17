import pandas as pd
import json
import os

def audit_and_filter(df):
    report = {}
    report['row_count'] = len(df)
    report['columns'] = df.columns.tolist()
    report['data_types'] = {k: str(v) for k, v in df.dtypes.items()}
    
    # Missing values
    missing = df.isnull().sum()
    report['missing_values'] = missing[missing > 0].to_dict()
    
    # Constant columns
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    report['constant_columns'] = constant_cols
    
    # Sampling interval
    if 'sample_interval_s' in df.columns:
        report['median_sampling_interval'] = df['sample_interval_s'].median()
        
    # CIP states/steps
    if 'process_step' in df.columns:
        cip_states = df['process_step'].unique().tolist()
        report['cip_states'] = cip_states
        
    if 'phe_id' in df.columns:
        report['equipment_ids'] = df['phe_id'].unique().tolist()
        
    # Suspicious values
    suspicious = []
    
    if 'flow_lph' in df.columns:
        neg_flow = df[df['flow_lph'] < 0]
        for idx, row in neg_flow.iterrows():
            suspicious.append({
                'timestamp': row['timestamp'],
                'feature': 'flow_lph',
                'value': row['flow_lph'],
                'reason_flagged': 'Negative flow'
            })
            
    if 'temp_in' in df.columns:
        impossible_temp = df[(df['temp_in'] < 0) | (df['temp_in'] > 150)]
        for idx, row in impossible_temp.iterrows():
            suspicious.append({
                'timestamp': row['timestamp'],
                'feature': 'temp_in',
                'value': row['temp_in'],
                'reason_flagged': 'Impossible temperature NEEDS FACTORY TAG VALIDATION'
            })
            
    if 'conductivity' in df.columns:
        impossible_cond = df[(df['conductivity'] < 0)]
        for idx, row in impossible_cond.iterrows():
            suspicious.append({
                'timestamp': row['timestamp'],
                'feature': 'conductivity',
                'value': row['conductivity'],
                'reason_flagged': 'Negative conductivity NEEDS FACTORY TAG VALIDATION'
            })

    suspicious_df = pd.DataFrame(suspicious)
    
    return report, suspicious_df

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_path = os.path.join(base_dir, 'data', 'raw', 'MODEL2_CIP_HEALTH_TIMESERIES.csv')
    df = pd.read_csv(raw_path)
    report, suspicious_df = audit_and_filter(df)
    
    report_path = os.path.join(base_dir, 'data', 'reports', 'data_audit_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=4)
        
    if not suspicious_df.empty:
        susp_path = os.path.join(base_dir, 'data', 'reports', 'suspicious_values.csv')
        suspicious_df.to_csv(susp_path, index=False)
    
    print("Filter step complete")
