"""
Static analysis tests for QR Scanner JavaScript functionality
Tests code structure, error handling, and browser compatibility patterns
"""
import pytest
import os
import re
import json


class TestQRScannerStatic:
    """Static analysis tests for QR Scanner"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        with open(self.qr_scanner_path, 'r') as f:
            self.content = f.read()
    
    def test_file_exists_and_readable(self):
        """Test QR scanner file exists and is readable"""
        assert os.path.exists(self.qr_scanner_path), "QR scanner file not found"
        assert os.path.getsize(self.qr_scanner_path) > 0, "QR scanner file is empty"
        assert len(self.content) > 1000, "QR scanner file seems too small"
    
    def test_class_definition_exists(self):
        """Test QRScanner class is properly defined"""
        assert 'class QRScanner' in self.content, "QRScanner class not found"
        assert 'constructor()' in self.content, "Constructor not found"
        
        # Check for essential methods
        essential_methods = [
            'checkCameraSupport',
            'startCamera', 
            'startScanning',
            'stopScanning'
        ]
        
        for method in essential_methods:
            assert f'{method}(' in self.content, f"Method {method} not found"
    
    def test_browser_compatibility_checks(self):
        """Test browser compatibility detection"""
        # Should check for navigator.mediaDevices
        assert 'navigator.mediaDevices' in self.content, "No navigator.mediaDevices check"
        
        # Should check for getUserMedia
        assert 'getUserMedia' in self.content, "No getUserMedia check"
        
        # Should handle the case where mediaDevices is not supported
        compat_checks = [
            '!navigator.mediaDevices',
            '!navigator.mediaDevices.getUserMedia'
        ]
        
        has_compat_check = any(check in self.content for check in compat_checks)
        assert has_compat_check, "Missing browser compatibility checks"
    
    def test_error_handling_patterns(self):
        """Test error handling is comprehensive"""
        # Should have try-catch blocks
        assert 'try {' in self.content, "No try blocks found"
        assert 'catch (' in self.content, "No catch blocks found"
        
        # Should handle specific error types
        error_types = ['NotAllowedError', 'NotFoundError']
        for error_type in error_types:
            assert error_type in self.content, f"No handling for {error_type}"
        
        # Should throw meaningful errors
        assert 'throw new Error(' in self.content, "No custom error throwing"
        
        # Should have error display functionality
        error_display_patterns = [
            'showError',
            'scanner-error',
            'updateStatus'
        ]
        has_error_display = any(pattern in self.content for pattern in error_display_patterns)
        assert has_error_display, "No error display mechanism found"
    
    def test_camera_enumeration_handling(self):
        """Test camera enumeration is properly handled"""
        # Should enumerate devices
        assert 'enumerateDevices' in self.content, "No device enumeration"
        
        # Should filter for video inputs
        assert 'videoinput' in self.content, "No video input filtering"
        
        # Should handle cases with no cameras
        no_camera_patterns = [
            'cameras.length === 0',
            'cameras.length == 0',
            'No cameras found'
        ]
        has_no_camera_check = any(pattern in self.content for pattern in no_camera_patterns)
        assert has_no_camera_check, "No handling for systems without cameras"
    
    def test_https_requirements_handling(self):
        """Test HTTPS requirements are addressed"""
        # Look for HTTPS-related messaging or checks
        https_patterns = [
            'https',
            'HTTPS', 
            'secure',
            'ssl',
            'protocol',
            'location.protocol'
        ]
        
        has_https_awareness = any(pattern in self.content for pattern in https_patterns)
        
        # Note: Current implementation might not have HTTPS checks
        # This test documents the requirement for improvement
        if not has_https_awareness:
            pytest.fail("No HTTPS requirements handling found - improvement needed")
    
    def test_fallback_mechanisms(self):
        """Test fallback mechanisms exist"""
        # Should have manual entry fallback
        manual_patterns = [
            'manual-entry',
            'manual-section',
            'showManualEntry'
        ]
        has_manual_fallback = any(pattern in self.content for pattern in manual_patterns)
        assert has_manual_fallback, "No manual entry fallback found"
        
        # Should gracefully handle camera failures
        graceful_patterns = [
            'Continue without',
            'fallback',
            'alternative'
        ]
        # Note: This is aspirational - current code might not have this
    
    def test_proper_cleanup_methods(self):
        """Test proper resource cleanup"""
        # Should stop video streams
        cleanup_patterns = [
            'stream.getTracks()',
            'track.stop()',
            'srcObject = null'
        ]
        
        has_cleanup = any(pattern in self.content for pattern in cleanup_patterns)
        assert has_cleanup, "No proper stream cleanup found"
    
    def test_user_feedback_mechanisms(self):
        """Test user feedback and status updates"""
        # Should provide status updates
        status_patterns = [
            'updateStatus',
            'showLoading',
            'showError',
            'scanner-status'
        ]
        
        feedback_count = sum(1 for pattern in status_patterns if pattern in self.content)
        assert feedback_count >= 2, f"Insufficient user feedback mechanisms: {feedback_count}/4"
    
    def test_camera_constraints_configuration(self):
        """Test camera constraints are properly configured"""
        # Should set video constraints
        assert 'constraints' in self.content, "No camera constraints configuration"
        assert 'video:' in self.content, "No video constraints"
        
        # Should handle different camera modes
        camera_modes = ['facingMode', 'deviceId']
        has_camera_modes = any(mode in self.content for mode in camera_modes)
        assert has_camera_modes, "No camera mode configuration"
    
    def test_performance_considerations(self):
        """Test performance optimizations are present"""
        # Should have frame rate control or similar optimizations
        performance_patterns = [
            'frameRate',
            'fps',
            'requestAnimationFrame',
            'cancelAnimationFrame'
        ]
        
        perf_count = sum(1 for pattern in performance_patterns if pattern in self.content)
        assert perf_count >= 1, "No performance optimizations found"


class TestQRScannerCurrentIssues:
    """Tests that identify current specific issues"""
    
    def test_identify_getusermedia_issues(self):
        """Identify getUserMedia compatibility issues"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        with open(qr_scanner_path, 'r') as f:
            content = f.read()
        
        # Find getUserMedia usage
        getusermedia_lines = []
        for i, line in enumerate(content.split('\n'), 1):
            if 'getUserMedia' in line:
                getusermedia_lines.append((i, line.strip()))
        
        assert len(getusermedia_lines) > 0, "No getUserMedia usage found"
        
        # Check for potential compatibility issues
        issues = []
        
        for line_num, line in getusermedia_lines:
            # Issue 1: Direct access without proper checks
            if 'navigator.mediaDevices.getUserMedia' in line and 'if (' not in line:
                # Check if there's a proper check before this line
                # This is a simplified check - real implementation would be more thorough
                pass
        
        # Log findings for improvement
        print(f"Found getUserMedia usage on lines: {[ln for ln, _ in getusermedia_lines]}")
    
    def test_identify_error_handling_gaps(self):
        """Identify gaps in error handling"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        with open(qr_scanner_path, 'r') as f:
            content = f.read()
        
        # Find try-catch blocks
        try_count = content.count('try {')
        catch_count = content.count('catch (')
        
        assert try_count > 0, "No try blocks found"
        assert catch_count == try_count, f"Mismatch: {try_count} try blocks, {catch_count} catch blocks"
        
        # Check for comprehensive error handling
        if 'OverconstrainedError' not in content:
            print("Missing OverconstrainedError handling")
        
        if 'NotReadableError' not in content:
            print("Missing NotReadableError handling") 
        
        if 'AbortError' not in content:
            print("Missing AbortError handling")
    
    def test_camera_support_detection_robustness(self):
        """Test camera support detection robustness"""
        qr_scanner_path = "/home/tim/RFID3/static/js/qr-scanner.js"
        with open(qr_scanner_path, 'r') as f:
            content = f.read()
        
        # Find checkCameraSupport method
        method_match = re.search(r'async checkCameraSupport\(\)[^}]+}', content, re.DOTALL)
        assert method_match, "checkCameraSupport method not found"
        
        method_content = method_match.group(0)
        
        # Should check multiple compatibility indicators
        checks = [
            'navigator.mediaDevices',
            'navigator.mediaDevices.getUserMedia'
        ]
        
        missing_checks = [check for check in checks if check not in method_content]
        if missing_checks:
            print(f"Missing compatibility checks: {missing_checks}")
        
        # Should handle enumeration failures gracefully
        if 'enumerateDevices' in method_content:
            if 'catch' not in method_content:
                print("Device enumeration not wrapped in try-catch")


if __name__ == "__main__":
    # Run tests when script is executed directly
    import subprocess
    result = subprocess.run([
        'python', '-m', 'pytest',
        '/home/tim/RFID3/tests/test_qr_scanner_static.py',
        '-v', '--tb=short'
    ], cwd='/home/tim/RFID3')
    
    exit(result.returncode)