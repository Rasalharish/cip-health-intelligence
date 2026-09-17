class DeviationScorer:
    def __init__(self):
        pass
        
    def calculate_deviations(self, observation, baseline_stats):
        """
        observation: dict representing a single row of features
        baseline_stats: dict of baseline stats for the specific phe/step
        
        Returns:
        - deviations: dict of feature -> z-score
        - coverage: float (0.0 to 1.0) representing ratio of features scored
        """
        deviations = {}
        features_scored = 0
        total_baseline_features = len(baseline_stats)
        
        if total_baseline_features == 0:
            return {}, 0.0

        for feature, stats in baseline_stats.items():
            if feature in observation and observation[feature] is not None:
                val = observation[feature]
                mean = stats['mean']
                std = stats['std']
                
                # Handle zero variance in baseline
                if std == 0:
                    # If val == mean, deviation is 0. 
                    # If val != mean, we assign a fixed penalty (e.g., standardizing the absolute error)
                    # For a robust approach, we fallback to absolute difference when std=0, 
                    # but we cap it to avoid extreme scores, or just treat it as a significant deviation if non-zero.
                    if val == mean:
                        z = 0.0
                    else:
                        # Fallback: if value deviates from a constant baseline, it's highly anomalous
                        # We arbitrarily assign a high z-score relative to the difference.
                        z = (val - mean) # Unscaled deviation
                        # Cap it so it doesn't break the scoring logic entirely
                        z = max(min(z, 10.0), -10.0) 
                else:
                    z = (val - mean) / std
                    
                deviations[feature] = z
                features_scored += 1
                
        coverage = features_scored / total_baseline_features
        return deviations, coverage
