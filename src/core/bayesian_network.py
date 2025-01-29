from typing import Dict, Any, Optional
import numpy as np
from scipy.stats import norm, beta
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class BayesianFingerprintGenerator:
    """
    Generate realistic browser fingerprints using Bayesian network modeling
    """
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or Path(__file__).parent / "data/fingerprint_distributions.json"
        self.distributions = self._load_distributions()
        self.correlation_matrix = self._build_correlation_matrix()
        
    def _load_distributions(self) -> Dict[str, Any]:
        """Load learned distribution parameters from JSON"""
        try:
            with open(self.data_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Distribution data not found, using defaults")
            return self._get_default_distributions()
    
    def _get_default_distributions(self) -> Dict[str, Any]:
        """Default distribution parameters based on common browser statistics"""
        return {
            "screen": {
                "width": {"mean": 1920, "std": 400},
                "height": {"mean": 1080, "std": 200},
                "pixel_ratio": {"a": 2, "b": 3}  # Beta distribution parameters
            },
            "navigator": {
                "memory": {"mean": 8, "std": 2},
                "cores": {"mean": 4, "std": 2},
                "touch_points": {"a": 1, "b": 5}
            },
            "webgl": {
                "vendor_length": {"mean": 20, "std": 5},
                "renderer_length": {"mean": 30, "std": 8}
            }
        }
    
    def _build_correlation_matrix(self) -> np.ndarray:
        """Build correlation matrix for fingerprint properties"""
        # Example correlation matrix (simplified)
        return np.array([
            [1.0, 0.8, 0.3, 0.1],  # screen width
            [0.8, 1.0, 0.3, 0.1],  # screen height
            [0.3, 0.3, 1.0, 0.5],  # memory
            [0.1, 0.1, 0.5, 1.0]   # cores
        ])
    
    def generate_correlated_values(self) -> Dict[str, Any]:
        """Generate correlated fingerprint values using multivariate normal distribution"""
        # Generate base values
        base_values = np.random.multivariate_normal(
            mean=[
                self.distributions["screen"]["width"]["mean"],
                self.distributions["screen"]["height"]["mean"],
                self.distributions["navigator"]["memory"]["mean"],
                self.distributions["navigator"]["cores"]["mean"]
            ],
            cov=self._adjust_covariance_matrix(),
            size=1
        )[0]
        
        # Apply constraints and rounding
        return {
            "screen": {
                "width": int(max(1024, min(3840, base_values[0]))),
                "height": int(max(768, min(2160, base_values[1]))),
                "pixel_ratio": float(beta.rvs(
                    self.distributions["screen"]["pixel_ratio"]["a"],
                    self.distributions["screen"]["pixel_ratio"]["b"]
                ))
            },
            "navigator": {
                "memory": int(max(2, min(32, base_values[2]))),
                "cores": int(max(1, min(16, base_values[3]))),
                "touch_points": int(beta.rvs(
                    self.distributions["navigator"]["touch_points"]["a"],
                    self.distributions["navigator"]["touch_points"]["b"]
                ) * 10)
            }
        }
    
    def _adjust_covariance_matrix(self) -> np.ndarray:
        """Adjust covariance matrix based on current browser trends"""
        # Apply scaling factors based on browser market share
        scale_factor = self._get_market_share_scale()
        return self.correlation_matrix * scale_factor
    
    def _get_market_share_scale(self) -> float:
        """Get scaling factor based on browser market share"""
        # This could be updated regularly from external data
        return 1.2  # Example: slight increase in variance
    
    def generate(self) -> Dict[str, Any]:
        """Generate a complete fingerprint using Bayesian network"""
        try:
            base_values = self.generate_correlated_values()
            
            # Add noise to make values more realistic
            fingerprint = self._add_realistic_noise(base_values)
            
            # Validate consistency
            if self._validate_fingerprint(fingerprint):
                return fingerprint
            
            # Retry if validation fails
            return self.generate()
            
        except Exception as e:
            logger.error(f"Error generating fingerprint: {str(e)}")
            raise
    
    def _add_realistic_noise(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Add realistic noise to generated values"""
        noisy_values = values.copy()
        
        # Add small random variations
        for category in noisy_values:
            for key, value in noisy_values[category].items():
                if isinstance(value, (int, float)):
                    noise = np.random.normal(0, value * 0.01)  # 1% noise
                    if isinstance(value, int):
                        noisy_values[category][key] = int(value + noise)
                    else:
                        noisy_values[category][key] = value + noise
        
        return noisy_values
    
    def _validate_fingerprint(self, fingerprint: Dict[str, Any]) -> bool:
        """Validate fingerprint consistency"""
        try:
            # Screen aspect ratio check
            aspect_ratio = fingerprint["screen"]["width"] / fingerprint["screen"]["height"]
            if not (1.0 <= aspect_ratio <= 2.5):
                return False
            
            # Memory/cores correlation check
            memory_core_ratio = fingerprint["navigator"]["memory"] / fingerprint["navigator"]["cores"]
            if not (1.0 <= memory_core_ratio <= 8.0):
                return False
            
            # Touch points validation
            if fingerprint["navigator"]["touch_points"] > 0 and fingerprint["screen"]["width"] > 2000:
                # Large screens typically don't have touch
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False 