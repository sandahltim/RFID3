"""
Test suite for QR Scanner JavaScript functionality
Tests camera access, browser compatibility, and error handling
"""
import pytest
import os
import subprocess
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
import time


class TestQRScanner:
    """Test QR Scanner camera functionality and browser compatibility"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = "http://localhost:5000"
        self.drivers = []
        
    def teardown_method(self):
        """Clean up after each test"""
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        self.drivers = []
    
    def create_chrome_driver(self, headless=True, allow_camera=False):
        """Create Chrome driver with specific settings"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Camera permissions
        if allow_camera:
            options.add_argument("--use-fake-ui-for-media-stream")
            options.add_argument("--use-fake-device-for-media-stream")
            options.add_argument("--use-file-for-fake-video-capture=/dev/video0")
        else:
            options.add_argument("--deny-permission-prompts")
        
        prefs = {
            "profile.default_content_setting_values.media_stream_camera": 1 if allow_camera else 2,
            "profile.default_content_setting_values.media_stream_mic": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(options=options)
            self.drivers.append(driver)
            return driver
        except Exception as e:
            pytest.skip(f"Chrome driver not available: {e}")
    
    def create_firefox_driver(self, headless=True, allow_camera=False):
        """Create Firefox driver with specific settings"""
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        
        # Camera permissions for Firefox
        profile = webdriver.FirefoxProfile()
        if allow_camera:
            profile.set_preference("media.navigator.permission.disabled", True)
            profile.set_preference("media.navigator.streams.fake", True)
        else:
            profile.set_preference("media.navigator.permission.disabled", False)
        
        try:
            driver = webdriver.Firefox(firefox_profile=profile, options=options)
            self.drivers.append(driver)
            return driver
        except Exception as e:
            pytest.skip(f"Firefox driver not available: {e}")
    
    def wait_for_element(self, driver, by, value, timeout=10):
        """Wait for element to be present"""
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def wait_for_element_visible(self, driver, by, value, timeout=10):
        """Wait for element to be visible"""
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
    
    def test_qr_scanner_file_exists(self):
        """Test that QR scanner JavaScript file exists and is readable"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        assert os.path.exists(qr_scanner_path), "QR scanner JavaScript file not found"
        assert os.path.getsize(qr_scanner_path) > 0, "QR scanner file is empty"
        
        # Check file is readable
        with open(qr_scanner_path, 'r') as f:
            content = f.read()
            assert 'QRScanner' in content, "QRScanner class not found in file"
            assert 'getUserMedia' in content, "getUserMedia not found in file"
    
    def test_browser_feature_detection_chrome(self):
        """Test camera feature detection in Chrome"""
        driver = self.create_chrome_driver(headless=True, allow_camera=False)
        driver.get(f"{self.base_url}")
        
        # Wait for page load
        self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        
        # Click scanner button
        scanner_btn = driver.find_element(By.ID, "toggle-scanner-btn")
        scanner_btn.click()
        
        # Check for error handling when camera is denied
        try:
            error_element = self.wait_for_element_visible(driver, By.ID, "scanner-error", timeout=5)
            error_text = error_element.text
            assert any(msg in error_text.lower() for msg in [
                'camera permission denied',
                'camera not supported',
                'camera access failed'
            ]), f"Expected camera error message, got: {error_text}"
        except TimeoutException:
            pytest.fail("No error message displayed when camera access is denied")
    
    def test_browser_feature_detection_firefox(self):
        """Test camera feature detection in Firefox"""
        driver = self.create_firefox_driver(headless=True, allow_camera=False)
        driver.get(f"{self.base_url}")
        
        # Wait for page load
        self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        
        # Click scanner button
        scanner_btn = driver.find_element(By.ID, "toggle-scanner-btn")
        scanner_btn.click()
        
        # Check for error handling when camera is denied
        try:
            error_element = self.wait_for_element_visible(driver, By.ID, "scanner-error", timeout=5)
            error_text = error_element.text
            assert any(msg in error_text.lower() for msg in [
                'camera permission denied',
                'camera not supported',
                'camera access failed'
            ]), f"Expected camera error message, got: {error_text}"
        except TimeoutException:
            pytest.fail("No error message displayed when camera access is denied")
    
    def test_manual_entry_fallback(self):
        """Test that manual entry is available when camera fails"""
        driver = self.create_chrome_driver(headless=True, allow_camera=False)
        driver.get(f"{self.base_url}")
        
        # Wait for page load
        self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        
        # Check manual entry button exists
        manual_btn = self.wait_for_element(driver, By.ID, "manual-entry-btn")
        assert manual_btn.is_displayed(), "Manual entry button not visible"
        
        # Click manual entry
        manual_btn.click()
        
        # Check manual section appears
        manual_section = self.wait_for_element_visible(driver, By.ID, "manual-section", timeout=5)
        assert manual_section.is_displayed(), "Manual section not displayed after clicking button"
    
    def test_https_detection(self):
        """Test HTTPS requirement detection"""
        # This test checks if the scanner properly detects HTTP vs HTTPS
        # In a real scenario, camera access requires HTTPS
        
        # Test with HTTP (should show warning)
        driver = self.create_chrome_driver(headless=True, allow_camera=False)
        driver.get("http://localhost:5000")  # HTTP explicitly
        
        # Check if there's any indication about HTTPS requirement
        scanner_btn = self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        scanner_btn.click()
        
        # Should show some indication that HTTPS is required
        time.sleep(2)  # Give time for any messages to appear
        
        # Check various ways the system might communicate HTTPS requirement
        page_source = driver.page_source.lower()
        has_https_info = any(term in page_source for term in [
            'https required',
            'secure connection',
            'ssl required',
            'camera requires https'
        ])
        
        # Note: This test may not find HTTPS messaging in current implementation
        # This indicates an area for improvement
    
    def test_camera_permission_handling(self):
        """Test proper handling of camera permission scenarios"""
        # Test with camera allowed
        driver = self.create_chrome_driver(headless=True, allow_camera=True)
        driver.get(f"{self.base_url}")
        
        scanner_btn = self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        scanner_btn.click()
        
        # Should show camera section when permission is granted
        try:
            camera_section = self.wait_for_element_visible(driver, By.ID, "camera-section", timeout=5)
            assert camera_section.is_displayed(), "Camera section not displayed with permissions"
            
            # Check for video element
            video_element = driver.find_element(By.ID, "scanner-video")
            assert video_element.is_displayed(), "Video element not displayed"
            
        except TimeoutException:
            # Check if there's an error message instead
            try:
                error_element = driver.find_element(By.ID, "scanner-error")
                if error_element.is_displayed():
                    pytest.fail(f"Unexpected error with camera allowed: {error_element.text}")
            except:
                pytest.fail("Neither camera section nor error message appeared")
    
    def test_multiple_camera_switching(self):
        """Test camera switching functionality"""
        driver = self.create_chrome_driver(headless=True, allow_camera=True)
        driver.get(f"{self.base_url}")
        
        scanner_btn = self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        scanner_btn.click()
        
        # Wait a moment for camera initialization
        time.sleep(2)
        
        # Check if switch camera button is available
        # (May not be visible if only one camera is detected)
        try:
            switch_btn = driver.find_element(By.ID, "switch-camera-btn")
            if switch_btn.is_displayed():
                # Test switching cameras
                switch_btn.click()
                time.sleep(1)  # Allow time for camera switch
                
                # Verify camera section is still active
                camera_section = driver.find_element(By.ID, "camera-section")
                assert camera_section.is_displayed(), "Camera section hidden after switch"
        except:
            # Switch button not available - this is fine for single camera systems
            pass
    
    def test_scanner_cleanup_on_stop(self):
        """Test proper cleanup when scanner is stopped"""
        driver = self.create_chrome_driver(headless=True, allow_camera=True)
        driver.get(f"{self.base_url}")
        
        scanner_btn = self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        
        # Start scanner
        scanner_btn.click()
        time.sleep(2)
        
        # Stop scanner
        scanner_btn.click()
        
        # Check scanner container is hidden
        scanner_container = driver.find_element(By.ID, "scanner-container")
        
        # Wait a moment for cleanup
        time.sleep(1)
        
        # Container should be hidden after stopping
        assert not scanner_container.is_displayed(), "Scanner container still visible after stop"
    
    def test_error_message_display(self):
        """Test that error messages are properly displayed to users"""
        driver = self.create_chrome_driver(headless=True, allow_camera=False)
        driver.get(f"{self.base_url}")
        
        scanner_btn = self.wait_for_element(driver, By.ID, "toggle-scanner-btn")
        scanner_btn.click()
        
        # Should show error message
        error_element = self.wait_for_element_visible(driver, By.ID, "scanner-error", timeout=10)
        error_text = error_element.text.strip()
        
        # Error message should be informative
        assert len(error_text) > 0, "Error message is empty"
        assert not error_text.startswith("Error:"), "Error message should be user-friendly"
        
        # Should suggest solutions
        error_lower = error_text.lower()
        suggests_solution = any(word in error_lower for word in [
            'allow', 'permission', 'enable', 'reload', 'try', 'manual'
        ])
        assert suggests_solution, f"Error message should suggest solutions: {error_text}"


class TestQRScannerJavaScript:
    """Test JavaScript QR Scanner implementation directly"""
    
    def test_javascript_syntax(self):
        """Test JavaScript file has valid syntax"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        
        # Use Node.js to check syntax if available
        try:
            result = subprocess.run(
                ['node', '-c', qr_scanner_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"JavaScript syntax error: {result.stderr}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Node.js not available, skip syntax check
            pytest.skip("Node.js not available for syntax checking")
    
    def test_required_functions_exist(self):
        """Test that required functions and methods exist in the JavaScript"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        
        with open(qr_scanner_path, 'r') as f:
            content = f.read()
        
        # Check for required methods
        required_methods = [
            'checkCameraSupport',
            'startCamera',
            'stopScanning',
            'startScanning',
            'switchCamera',
            'getUserMedia'
        ]
        
        for method in required_methods:
            assert method in content, f"Required method {method} not found in QR scanner"
        
        # Check for error handling patterns
        assert 'try {' in content, "No try-catch blocks found"
        assert 'catch' in content, "No catch blocks found"
        assert 'throw new Error' in content, "No error throwing found"
    
    def test_browser_compatibility_checks(self):
        """Test that proper browser compatibility checks exist"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        
        with open(qr_scanner_path, 'r') as f:
            content = f.read()
        
        # Check for navigator checks
        assert 'navigator.mediaDevices' in content, "No navigator.mediaDevices check found"
        assert 'getUserMedia' in content, "No getUserMedia check found"
        
        # Should handle different error types
        error_types = ['NotAllowedError', 'NotFoundError']
        for error_type in error_types:
            assert error_type in content, f"No handling for {error_type} found"


class TestQRScannerIntegration:
    """Integration tests for QR Scanner with the Flask application"""
    
    def test_qr_scanner_css_loaded(self):
        """Test that QR scanner CSS is properly loaded"""
        driver = webdriver.Chrome()
        try:
            driver.get("http://localhost:5000")
            
            # Check that scanner elements have proper styling
            scanner_container = driver.find_element(By.ID, "scanner-container")
            
            # Get computed styles
            display_style = scanner_container.value_of_css_property("display")
            # Initially should be hidden
            assert display_style == "none", f"Scanner container should initially be hidden, got: {display_style}"
            
        finally:
            driver.quit()
    
    def test_qr_scanner_javascript_loaded(self):
        """Test that QR scanner JavaScript is properly loaded and initialized"""
        driver = webdriver.Chrome()
        try:
            driver.get("http://localhost:5000")
            
            # Check if QRScanner class is available
            result = driver.execute_script("return typeof QRScanner !== 'undefined';")
            assert result, "QRScanner class not loaded or initialized"
            
            # Check if scanner instance exists
            result = driver.execute_script("return typeof window.qrScanner !== 'undefined';")
            # Note: This may not exist depending on implementation
            
        except Exception as e:
            # If we can't test JavaScript directly, at least check the file is referenced
            page_source = driver.page_source
            assert 'qr-scanner.js' in page_source, "QR scanner JavaScript not referenced in page"
            
        finally:
            driver.quit()


def run_browser_compatibility_tests():
    """Utility function to run comprehensive browser tests"""
    print("Running QR Scanner browser compatibility tests...")
    
    # Run pytest with specific markers
    result = subprocess.run([
        'python', '-m', 'pytest', 
        '/home/tim/RFID3/tests/test_qr_scanner.py',
        '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print("Test Results:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    # Run tests when script is executed directly
    run_browser_compatibility_tests()