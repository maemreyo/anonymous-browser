import pytest
from src.core.fingerprint_generator import AnonymousFingerprint
from src.config.settings import BROWSER_CONFIG, SCREEN_CONFIG

class TestAnonymousFingerprint:
    @pytest.fixture
    def fingerprint_generator(self):
        return AnonymousFingerprint()

    def test_fingerprint_generation(self, fingerprint_generator):
        """Test basic fingerprint generation"""
        result = fingerprint_generator.generate()
        
        assert "fingerprint" in result
        assert "headers" in result
        
        # Verify fingerprint structure
        fingerprint = result["fingerprint"]
        assert isinstance(fingerprint, dict)
        
        # Verify headers structure
        headers = result["headers"]
        assert isinstance(headers, dict)
        assert "User-Agent" in headers

    def test_screen_constraints(self, fingerprint_generator):
        """Test screen resolution constraints"""
        result = fingerprint_generator.generate()
        screen = result["fingerprint"].get("screen", {})
        
        assert SCREEN_CONFIG["min_width"] <= screen.get("width", 0) <= SCREEN_CONFIG["max_width"]
        assert SCREEN_CONFIG["min_height"] <= screen.get("height", 0) <= SCREEN_CONFIG["max_height"]

    @pytest.mark.asyncio
    async def test_multiple_fingerprints_uniqueness(self, fingerprint_generator):
        """Test uniqueness of generated fingerprints"""
        fingerprints = [fingerprint_generator.generate() for _ in range(10)]
        
        # Convert fingerprints to frozenset for comparison
        fingerprint_sets = [
            frozenset(fp["fingerprint"].items()) for fp in fingerprints
        ]
        
        # Verify all fingerprints are unique
        assert len(set(fingerprint_sets)) == len(fingerprints) 