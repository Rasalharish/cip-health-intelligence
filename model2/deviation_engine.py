from .baseline_loader import BaselineLoader
from .deviation_scorer import DeviationScorer
from .health_score import HealthCalculator
from .explanations import ExplanationGenerator

class DeviationEngine:
    def __init__(self, baseline_path=None):
        self.loader = BaselineLoader(baseline_path)
        self.scorer = DeviationScorer()
        
        self.feature_weights = self.loader.get_feature_weights()
        self.thresholds = self.loader.get_thresholds()
        
        self.health_calc = HealthCalculator(self.thresholds, self.feature_weights)
        self.explainer = ExplanationGenerator(self.thresholds)
        
    def evaluate(self, observation):
        """
        Evaluates a single observation dict.
        Must contain 'phe_id' and 'process_step' keys.
        """
        phe_id = observation.get('phe_id')
        step = observation.get('process_step')
        
        if not phe_id or not step:
            return self._error_response("Missing phe_id or process_step in observation.")
            
        baseline_stats = self.loader.get_baseline_for(phe_id, step)
        if not baseline_stats:
            return self._error_response(f"No baseline data for {phe_id} at {step}.")
            
        # 1. Calculate Standardized Deviations
        deviations, coverage = self.scorer.calculate_deviations(observation, baseline_stats)
        
        # 2. Calculate Health Score and Grade
        score, grade = self.health_calc.calculate_health(deviations)
        
        # 3. Generate Explanation
        explanation = self.explainer.generate(score, grade, deviations)
        
        return {
            "status": "success",
            "context": {
                "equipment": phe_id,
                "step": step
            },
            "health_score": score,
            "grade": grade,
            "data_coverage": f"{int(coverage * len(baseline_stats))} / {len(baseline_stats)} features",
            "top_deviations": explanation['top_deviations'],
            "interpretation": explanation['interpretation'],
            "raw_deviations": deviations,
            "baseline_stats": baseline_stats
        }

    def _error_response(self, message):
        return {
            "status": "error",
            "message": message,
            "health_score": None,
            "grade": None,
            "data_coverage": "0 / 0 features",
            "top_deviations": [],
            "interpretation": "Cannot calculate score due to error.",
            "raw_deviations": {},
            "baseline_stats": {}
        }
