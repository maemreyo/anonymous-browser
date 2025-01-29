from typing import Optional, Dict, Any
from browserforge.fingerprints import FingerprintGenerator, Screen
from browserforge.headers import HeaderGenerator
from ..config.settings import BROWSER_CONFIG, SCREEN_CONFIG
from .bayesian_network import BayesianFingerprintGenerator

class AnonymousFingerprint:
    def __init__(self) -> None:
        self.screen = Screen(
            min_width=SCREEN_CONFIG["min_width"],
            max_width=SCREEN_CONFIG["max_width"],
            min_height=SCREEN_CONFIG["min_height"],
            max_height=SCREEN_CONFIG["max_height"]
        )
        
        self.header_generator = HeaderGenerator(
            browser=BROWSER_CONFIG["browser"],
            os=BROWSER_CONFIG["os"],
            device=BROWSER_CONFIG["device"],
            locale=BROWSER_CONFIG["locale"],
            http_version=BROWSER_CONFIG["http_version"]
        )
        
        self.fingerprint_generator = FingerprintGenerator(
            screen=self.screen,
            strict=True,
            mock_webrtc=True,
            slim=False
        )
        
        # Add Bayesian generator
        self.bayesian_generator = BayesianFingerprintGenerator()
    
    def generate(self) -> Dict[str, Any]:
        """Generate a new anonymous fingerprint configuration"""
        fingerprint = self.fingerprint_generator.generate()
        headers = self.header_generator.generate()
        
        return {
            "fingerprint": fingerprint,
            "headers": headers
        }
        
    def _merge_configurations(
        self,
        base: Dict[str, Any],
        bayesian: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge base and Bayesian configurations intelligently"""
        merged = base.copy()
        
        # Update screen properties
        merged["screen"].update(bayesian["screen"])
        
        # Update navigator properties
        merged["navigator"].update(bayesian["navigator"])
        
        return merged 