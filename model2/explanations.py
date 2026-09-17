class ExplanationGenerator:
    def __init__(self, thresholds):
        self.healthy_max = thresholds.get("healthy_z_score_max", 2.0)
        
    def generate(self, score, grade, deviations):
        """
        Generates deterministic interpretation of the health score based on deviations.
        """
        if not deviations:
            return {
                "top_deviations": [],
                "interpretation": "Insufficient data to calculate health score."
            }
            
        # Sort deviations by absolute magnitude
        sorted_devs = sorted(deviations.items(), key=lambda item: abs(item[1]), reverse=True)
        
        # Get top 3 deviations
        top_devs = sorted_devs[:3]
        formatted_devs = [f"{feat}: {z:+.1f}\u03c3" for feat, z in top_devs]
        
        # Build interpretation
        if score >= 90:
            interp = "Current operation is closely tracking the historical baseline. No significant deviations detected."
        elif score >= 70:
            interp = "Current operation shows moderate variance from the historical baseline."
        else:
            interp = "Current operation is significantly deviating from the historical baseline."
            
        # Add specifics
        significant_devs = [f for f, z in top_devs if abs(z) > self.healthy_max]
        if significant_devs:
            interp += f" This is primarily driven by anomalies in: {', '.join(significant_devs)}."
            
        return {
            "top_deviations": formatted_devs,
            "interpretation": interp
        }
