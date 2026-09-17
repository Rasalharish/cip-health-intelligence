class HealthCalculator:
    def __init__(self, thresholds, feature_weights):
        self.thresholds = thresholds
        self.weights = feature_weights
        
    def calculate_health(self, deviations):
        """
        Calculates a 0-100 health score based on feature deviations (z-scores).
        Also determines a grade (A-F).
        """
        if not deviations:
            return 0.0, "UNKNOWN"
            
        total_weight = 0.0
        weighted_penalty = 0.0
        
        healthy_max = self.thresholds.get("healthy_z_score_max", 2.0)
        
        for feature, z in deviations.items():
            w = self.weights.get(feature, 1.0)
            abs_z = abs(z)
            
            # Non-linear penalty: deviations < healthy_max incur little penalty.
            # Deviations > healthy_max incur heavy penalty.
            if abs_z <= healthy_max:
                penalty = (abs_z / healthy_max) * 5  # Max 5 points penalty per feature in healthy range
            else:
                # Exponential/linear steep penalty
                penalty = 5 + ((abs_z - healthy_max) * 15) 
                
            weighted_penalty += (penalty * w)
            total_weight += w
            
        if total_weight == 0:
            return 0.0, "UNKNOWN"
            
        avg_penalty = weighted_penalty / total_weight
        
        # Base score is 100
        score = max(0.0, 100.0 - avg_penalty)
        score = min(100.0, score)
        
        grade = self._assign_grade(score)
        
        return round(score, 1), grade
        
    def _assign_grade(self, score):
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
            
    # MULTIVARIATE EXTENSION STUB
    def calculate_mspc_health(self, observation, pca_model):
        """
        Placeholder for future Hotelling T^2 / SPE anomaly scoring.
        Not implemented yet to maintain simple, explainable baseline.
        """
        raise NotImplementedError("MSPC Extension not implemented in v1")
