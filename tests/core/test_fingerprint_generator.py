import pytest

from src.config.settings import SCREEN_CONFIG

class TestAnonymousFingerprint:
    def test_fingerprint_generation(self, fingerprint_generator):
        """Test basic fingerprint generation"""
        result = fingerprint_generator.generate()
        
        assert "fingerprint" in result
        assert "headers" in result
        
        # Verify fingerprint structure
        fingerprint = result["fingerprint"]
        assert hasattr(fingerprint, "screen")
        assert hasattr(fingerprint, "navigator")

    def test_screen_constraints(self, fingerprint_generator):
        """Test screen resolution constraints"""
        result = fingerprint_generator.generate()
        screen = result["fingerprint"].screen
        
        assert SCREEN_CONFIG["min_width"] <= screen.width <= SCREEN_CONFIG["max_width"]
        assert SCREEN_CONFIG["min_height"] <= screen.height <= SCREEN_CONFIG["max_height"]

    @pytest.mark.asyncio
    async def test_multiple_fingerprints_uniqueness(self, fingerprint_generator):
        """Test uniqueness of generated fingerprints"""
        fingerprints = [fingerprint_generator.generate() for _ in range(10)]
        
        # Convert fingerprints to comparable format
        fingerprint_dicts = [
            {
                "screen": fp["fingerprint"].screen.__dict__,
                "navigator": fp["fingerprint"].navigator.__dict__
            } for fp in fingerprints
        ]
        
        # Verify all fingerprints are unique
        unique_fingerprints = {
            frozenset(fp.items()) for fp in fingerprint_dicts
        }
        assert len(unique_fingerprints) == len(fingerprints) 