#!/usr/bin/env python3
"""
QR Scanner Diagnostics Test Suite
Tests the QR scanner functionality to identify button click and initialization issues.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import subprocess
import threading
import signal
import sys

class QRScannerDiagnostics:
    def __init__(self):
        self.driver = None
        self.flask_process = None
        self.base_url = "http://localhost:5000"
        
    def setup_method(self):
        """Setup test environment"""
        # Start Flask app
        self.start_flask_app()
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.notifications": 1
        })
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1200, 800)
        
        # Wait for Flask to start
        time.sleep(3)
        
    def teardown_method(self):
        """Cleanup test environment"""
        if self.driver:
            self.driver.quit()
        if self.flask_process:
            self.flask_process.terminate()
            self.flask_process.wait()
            
    def start_flask_app(self):
        """Start Flask application"""
        try:
            self.flask_process = subprocess.Popen(
                ['python', '-m', 'flask', 'run', '--host=0.0.0.0', '--port=5000'],
                cwd='/home/tim/RFID3',
                env={'FLASK_APP': 'app', 'FLASK_ENV': 'development'}
            )
        except Exception as e:
            print(f"Failed to start Flask app: {e}")
            
    def test_page_loads(self):
        """Test 1: Basic page load"""
        print("\n=== Test 1: Page Load ===")
        try:
            self.driver.get(f"{self.base_url}/")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            title = self.driver.title
            print(f"✅ Page loaded successfully")
            print(f"   Title: {title}")
            return True
        except Exception as e:
            print(f"❌ Page failed to load: {e}")
            return False
            
    def test_qr_scanner_elements_present(self):
        """Test 2: QR Scanner DOM elements exist"""
        print("\n=== Test 2: DOM Elements ===")
        
        required_elements = [
            ("toggle-scanner-btn", "Start Scanner button"),
            ("manual-entry-btn", "Manual Entry button"),
            ("scanner-container", "Scanner container"),
            ("manual-section", "Manual section"),
            ("scanner-video", "Video element"),
            ("scanner-canvas", "Canvas element"),
            ("manual-qr-input", "Manual input field"),
            ("manual-lookup-btn", "Manual lookup button"),
            ("scanner-error", "Error container"),
            ("scan-results", "Results container")
        ]
        
        all_present = True
        
        for element_id, description in required_elements:
            try:
                element = self.driver.find_element(By.ID, element_id)
                print(f"✅ {description} found (ID: {element_id})")
                
                # Check if element is visible
                if element.is_displayed():
                    print(f"   → Visible")
                else:
                    print(f"   → Hidden (display: {element.value_of_css_property('display')})")
                    
            except NoSuchElementException:
                print(f"❌ {description} NOT FOUND (ID: {element_id})")
                all_present = False
                
        return all_present
        
    def test_javascript_loaded(self):
        """Test 3: JavaScript files loaded"""
        print("\n=== Test 3: JavaScript Loading ===")
        
        # Check for JavaScript errors
        logs = self.driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if js_errors:
            print("❌ JavaScript errors found:")
            for error in js_errors:
                print(f"   {error['message']}")
        else:
            print("✅ No severe JavaScript errors")
            
        # Check if QR Scanner class is loaded
        qr_scanner_loaded = self.driver.execute_script("""
            return typeof QRScanner !== 'undefined';
        """)
        
        if qr_scanner_loaded:
            print("✅ QRScanner class is available")
        else:
            print("❌ QRScanner class NOT available")
            
        # Check if jsQR library is loaded
        jsqr_loaded = self.driver.execute_script("""
            return typeof jsQR !== 'undefined';
        """)
        
        if jsqr_loaded:
            print("✅ jsQR library is available")
        else:
            print("❌ jsQR library NOT available")
            
        return len(js_errors) == 0 and qr_scanner_loaded and jsqr_loaded
        
    def test_button_click_handlers(self):
        """Test 4: Button click handlers"""
        print("\n=== Test 4: Button Click Handlers ===")
        
        try:
            # Test Start Scanner button
            start_btn = self.driver.find_element(By.ID, "toggle-scanner-btn")
            print(f"✅ Start Scanner button found")
            
            # Check if button is clickable
            if start_btn.is_enabled():
                print("✅ Start Scanner button is enabled")
                
                # Try clicking the button
                self.driver.execute_script("arguments[0].click();", start_btn)
                print("✅ Start Scanner button clicked successfully")
                
                time.sleep(2)  # Wait for any responses
                
                # Check if scanner container becomes visible
                scanner_container = self.driver.find_element(By.ID, "scanner-container")
                if scanner_container.is_displayed():
                    print("✅ Scanner container became visible after click")
                else:
                    print("❌ Scanner container did not become visible")
                    
            else:
                print("❌ Start Scanner button is disabled")
                
            # Test Manual Entry button
            manual_btn = self.driver.find_element(By.ID, "manual-entry-btn")
            print(f"✅ Manual Entry button found")
            
            if manual_btn.is_enabled():
                print("✅ Manual Entry button is enabled")
                
                # Try clicking the button
                self.driver.execute_script("arguments[0].click();", manual_btn)
                print("✅ Manual Entry button clicked successfully")
                
                time.sleep(2)  # Wait for any responses
                
                # Check if manual section becomes visible
                manual_section = self.driver.find_element(By.ID, "manual-section")
                if manual_section.is_displayed():
                    print("✅ Manual section became visible after click")
                else:
                    print("❌ Manual section did not become visible")
                    
            else:
                print("❌ Manual Entry button is disabled")
                
            return True
                
        except Exception as e:
            print(f"❌ Button test failed: {e}")
            return False
            
    def test_qr_scanner_initialization(self):
        """Test 5: QR Scanner initialization"""
        print("\n=== Test 5: QR Scanner Initialization ===")
        
        try:
            # Check if QR Scanner instance exists
            scanner_exists = self.driver.execute_script("""
                return window.qrScanner !== undefined;
            """)
            
            if scanner_exists:
                print("✅ QR Scanner instance exists")
                
                # Check scanner properties
                scanner_info = self.driver.execute_script("""
                    if (window.qrScanner) {
                        return {
                            scanning: window.qrScanner.scanning,
                            cameraSupported: window.qrScanner.cameraSupported,
                            hasElements: Object.keys(window.qrScanner.elements).length > 0
                        };
                    }
                    return null;
                """)
                
                if scanner_info:
                    print(f"   → Scanning: {scanner_info['scanning']}")
                    print(f"   → Camera Supported: {scanner_info['cameraSupported']}")
                    print(f"   → Has Elements: {scanner_info['hasElements']}")
                else:
                    print("❌ Could not get scanner info")
                    
            else:
                print("❌ QR Scanner instance does not exist")
                
            return scanner_exists
            
        except Exception as e:
            print(f"❌ Scanner initialization test failed: {e}")
            return False
            
    def test_console_logs(self):
        """Test 6: Console logs analysis"""
        print("\n=== Test 6: Console Logs Analysis ===")
        
        logs = self.driver.get_log('browser')
        
        qr_logs = [log for log in logs if 'qr' in log['message'].lower() or 'scanner' in log['message'].lower()]
        
        if qr_logs:
            print("📋 QR Scanner related console logs:")
            for log in qr_logs:
                level_icon = "🔴" if log['level'] == 'SEVERE' else "🟡" if log['level'] == 'WARNING' else "ℹ️"
                print(f"   {level_icon} [{log['level']}] {log['message']}")
        else:
            print("📋 No QR Scanner related console logs found")
            
        return True
        
    def run_all_tests(self):
        """Run complete diagnostic suite"""
        print("🔍 QR Scanner Diagnostic Test Suite")
        print("=" * 50)
        
        self.setup_method()
        
        try:
            tests = [
                self.test_page_loads,
                self.test_qr_scanner_elements_present,
                self.test_javascript_loaded,
                self.test_button_click_handlers,
                self.test_qr_scanner_initialization,
                self.test_console_logs
            ]
            
            results = []
            for test in tests:
                try:
                    result = test()
                    results.append(result)
                except Exception as e:
                    print(f"❌ Test failed with exception: {e}")
                    results.append(False)
                    
            print("\n" + "=" * 50)
            print("📊 TEST SUMMARY")
            print("=" * 50)
            
            passed = sum(1 for r in results if r)
            total = len(results)
            
            print(f"Tests Passed: {passed}/{total}")
            
            if passed == total:
                print("🎉 All tests passed!")
            else:
                print("⚠️  Some tests failed - issues detected")
                
        finally:
            self.teardown_method()

if __name__ == "__main__":
    diagnostics = QRScannerDiagnostics()
    diagnostics.run_all_tests()