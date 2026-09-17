import json
import os

class BaselineLoader:
    def __init__(self, baseline_path=None):
        if baseline_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            baseline_path = os.path.join(base_dir, 'models', 'model2_baseline_v1.json')
            
        with open(baseline_path, 'r') as f:
            self.baseline_data = json.load(f)
            
        self.stats = self.baseline_data.get('baseline_statistics', {})
        self.features = self.baseline_data.get('selected_features', [])
        
    def get_baseline_for(self, phe_id, process_step):
        """
        Returns the baseline statistics for a given equipment and step.
        If the exact match doesn't exist, it returns None.
        """
        key = f"{phe_id}_{process_step}"
        return self.stats.get(key)
    
    def get_feature_weights(self):
        return self.baseline_data.get('feature_weights', {})
        
    def get_thresholds(self):
        return self.baseline_data.get('health_thresholds', {})
