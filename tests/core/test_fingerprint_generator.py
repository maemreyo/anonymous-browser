import pytest
from src.config.settings import SCREEN_CONFIG
from browserforge.fingerprints import ScreenFingerprint, NavigatorFingerprint

class TestAnonymousFingerprint:
    def test_fingerprint_generation(self, fingerprint_generator):
        """Test basic fingerprint generation"""
        result = fingerprint_generator.generate()
        
        assert "fingerprint" in result
        assert "headers" in result
        
        # Verify fingerprint structure
        fingerprint = result["fingerprint"]
        assert isinstance(fingerprint.screen, ScreenFingerprint)
        assert isinstance(fingerprint.navigator, NavigatorFingerprint)

    def test_screen_constraints(self, fingerprint_generator):
        """Test screen resolution constraints"""
        result = fingerprint_generator.generate()
        screen = result["fingerprint"].screen
        
        # Test width constraints with some tolerance for device pixel ratio
        effective_width = screen.width * screen.devicePixelRatio
        effective_min_width = SCREEN_CONFIG["min_width"] / max(SCREEN_CONFIG["pixel_ratio"])
        effective_max_width = SCREEN_CONFIG["max_width"] * max(SCREEN_CONFIG["pixel_ratio"])
        
        assert effective_min_width <= effective_width <= effective_max_width

        # Test height constraints
        effective_height = screen.height * screen.devicePixelRatio
        effective_min_height = SCREEN_CONFIG["min_height"] / max(SCREEN_CONFIG["pixel_ratio"])
        effective_max_height = SCREEN_CONFIG["max_height"] * max(SCREEN_CONFIG["pixel_ratio"])
        
        assert effective_min_height <= effective_height <= effective_max_height

    @pytest.mark.asyncio
    async def test_multiple_fingerprints_uniqueness(self, fingerprint_generator):
        """Test uniqueness of generated fingerprints"""
        fingerprints = [fingerprint_generator.generate() for _ in range(10)]
        
        def get_fingerprint_signature(fp):
            """Create a unique signature for a fingerprint that can be hashed"""
            screen = fp["fingerprint"].screen
            nav = fp["fingerprint"].navigator
            
            # Create tuples of key attributes that should make fingerprint unique
            screen_sig = (
                screen.width,
                screen.height,
                screen.devicePixelRatio,
                screen.colorDepth
            )
            
            nav_sig = (
                nav.userAgent,
                nav.platform,
                nav.language,
                # Convert lists to tuples and sort them
                tuple(sorted(nav.languages)) if hasattr(nav, 'languages') else (),
                tuple(sorted(str(x) for x in nav.plugins)) if hasattr(nav, 'plugins') else (),
                tuple(sorted(str(x) for x in nav.mimeTypes)) if hasattr(nav, 'mimeTypes') else ()
            )
            
            return (screen_sig, nav_sig)
        
        # Get unique signatures
        fingerprint_signatures = [get_fingerprint_signature(fp) for fp in fingerprints]
        unique_signatures = set(fingerprint_signatures)
        
        # Verify uniqueness
        assert len(unique_signatures) == len(fingerprints), \
            f"Expected {len(fingerprints)} unique fingerprints, got {len(unique_signatures)}"
        
        # Additional verification of key attributes
        for i, fp1 in enumerate(fingerprints):
            for j, fp2 in enumerate(fingerprints):
                if i != j:
                    sig1 = get_fingerprint_signature(fp1)
                    sig2 = get_fingerprint_signature(fp2)
                    assert sig1 != sig2, \
                        f"Fingerprints at positions {i} and {j} are identical" 