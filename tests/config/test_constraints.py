import pytest
from src.config.constraints import (
    validate_config,
    generate_consistent_config,
    DeviceType,
    OSFamily,
    BrowserFamily,
    OS_BROWSER_CONSTRAINTS
)

class TestConstraints:
    def test_os_browser_compatibility(self):
        """Test OS-Browser compatibility constraints"""
        for os_family in OSFamily:
            compatible_browsers = OS_BROWSER_CONSTRAINTS[os_family]
            config = generate_consistent_config(DeviceType.DESKTOP, os_family)
            
            assert BrowserFamily(config["browser"]) in compatible_browsers

    def test_device_specific_constraints(self, sample_device_configs):
        """Test device-specific hardware constraints"""
        for device_name, device_config in sample_device_configs.items():
            config = generate_consistent_config(
                device_config["device_type"],
                device_config["os_family"],
                device_config["browser_family"]
            )
            
            # Verify memory constraints
            assert config["device_memory"] in device_config["expected_memory"]
            
            # Verify touch points
            assert config["max_touch_points"] in device_config["expected_touch"]
            
            # Verify screen dimensions
            min_width, max_width = device_config["screen_width_range"]
            assert min_width <= config["screen"]["width"] <= max_width

    @pytest.mark.parametrize("invalid_combo", [
        (OSFamily.WINDOWS, BrowserFamily.SAFARI),
        (OSFamily.IOS, BrowserFamily.CHROME),
        (OSFamily.ANDROID, BrowserFamily.EDGE)
    ])
    def test_invalid_os_browser_combinations(self, invalid_combo, mock_fingerprint_config):
        """Test detection of invalid OS-Browser combinations"""
        os_family, browser_family = invalid_combo
        
        config = mock_fingerprint_config.copy()
        config["os"] = os_family.value
        config["browser"] = browser_family.value
        
        errors = validate_config(config)
        assert any("not supported" in error for error in errors) 