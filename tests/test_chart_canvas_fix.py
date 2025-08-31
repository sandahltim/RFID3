#!/usr/bin/env python3
"""
Test suite for validating the Chart.js canvas reuse fix.

This test validates that the implemented solution properly handles:
1. Singleton pattern to prevent multiple dashboard instances
2. Comprehensive chart destruction using Chart.js registry
3. Canvas element replacement when needed
4. Proper script loading without conflicts
5. Robust error handling and logging
"""

import os
import re


class TestChartCanvasFix:
    """Test suite for validating the Chart.js canvas reuse fix."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.project_root = "/home/tim/RFID3"
        cls.js_file = f"{cls.project_root}/static/js/predictive-analytics.js"
        cls.html_file = f"{cls.project_root}/app/templates/predictive_analytics.html"
        cls.base_html = f"{cls.project_root}/app/templates/base.html"

    def test_singleton_pattern_implemented(self):
        """Test: Verify singleton pattern prevents multiple instances."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for singleton implementation
        has_singleton_check = 'PredictiveAnalyticsDashboard.instance' in js_content
        has_instance_return = 'return PredictiveAnalyticsDashboard.instance' in js_content
        has_instance_assignment = 'PredictiveAnalyticsDashboard.instance = this' in js_content
        
        print(f"Singleton instance check: {has_singleton_check}")
        print(f"Instance return on duplicate: {has_instance_return}")
        print(f"Instance assignment: {has_instance_assignment}")
        
        assert has_singleton_check and has_instance_return and has_instance_assignment, \
            "Singleton pattern not properly implemented"

    def test_chart_registry_management(self):
        """Test: Verify Chart.js registry is properly managed."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for Chart.getChart() usage
        has_chart_getchart = 'Chart.getChart(' in js_content
        has_registry_destroy = 'Chart.getChart(canvasId)' in js_content
        
        print(f"Uses Chart.getChart() for registry lookup: {has_chart_getchart}")
        print(f"Destroys from registry: {has_registry_destroy}")
        
        assert has_chart_getchart and has_registry_destroy, \
            "Chart.js registry not properly managed"

    def test_comprehensive_destruction_method(self):
        """Test: Verify comprehensive chart destruction method exists."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for destroyChartCompletely method
        has_destroy_completely = 'destroyChartCompletely(' in js_content
        has_multiple_destroy_methods = js_content.count('destroy()') >= 4  # Registry, tracked, instance vars
        has_canvas_replacement = 'replaceCanvasElement(' in js_content
        
        print(f"Has destroyChartCompletely method: {has_destroy_completely}")
        print(f"Multiple destruction methods: {has_multiple_destroy_methods}")
        print(f"Canvas element replacement: {has_canvas_replacement}")
        
        assert has_destroy_completely and has_multiple_destroy_methods and has_canvas_replacement, \
            "Comprehensive chart destruction not implemented"

    def test_canvas_element_replacement(self):
        """Test: Verify canvas element replacement functionality."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for canvas replacement logic
        has_clone_node = 'cloneNode(' in js_content
        has_replace_child = 'replaceChild(' in js_content
        has_class_preservation = 'newCanvas.className = oldCanvas.className' in js_content
        has_style_preservation = 'newCanvas.style.cssText = oldCanvas.style.cssText' in js_content
        
        print(f"Canvas cloning: {has_clone_node}")
        print(f"Element replacement: {has_replace_child}")
        print(f"Class preservation: {has_class_preservation}")
        print(f"Style preservation: {has_style_preservation}")
        
        assert has_clone_node and has_replace_child and has_class_preservation and has_style_preservation, \
            "Canvas element replacement not properly implemented"

    def test_duplicate_script_load_removed(self):
        """Test: Verify duplicate script loads have been removed."""
        with open(self.base_html, 'r') as f:
            base_content = f.read()
            
        with open(self.html_file, 'r') as f:
            template_content = f.read()
        
        # Check that base.html no longer loads predictive-analytics.js as module
        base_has_predictive_module = 'type="module"' in base_content and 'predictive-analytics.js' in base_content
        template_has_predictive_regular = 'predictive-analytics.js' in template_content and 'type="module"' not in template_content
        
        print(f"Base has module load: {base_has_predictive_module}")
        print(f"Template has regular load: {template_has_predictive_regular}")
        
        # Should only have one script load method now
        assert not base_has_predictive_module or not template_has_predictive_regular, \
            "Duplicate script loads still present"

    def test_initialization_guard(self):
        """Test: Verify initialization guard prevents multiple runs."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for initialization guard
        has_init_flag = 'dashboardInitialized' in js_content
        has_init_check = 'if (dashboardInitialized)' in js_content
        has_init_function = 'function initializeDashboard()' in js_content
        has_readystate_check = 'document.readyState === \'loading\'' in js_content
        
        print(f"Initialization flag: {has_init_flag}")
        print(f"Initialization check: {has_init_check}")
        print(f"Dedicated init function: {has_init_function}")
        print(f"Ready state check: {has_readystate_check}")
        
        assert has_init_flag and has_init_check and has_init_function and has_readystate_check, \
            "Initialization guard not properly implemented"

    def test_error_handling_and_logging(self):
        """Test: Verify comprehensive error handling and logging."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Count logging statements
        console_log_count = js_content.count('console.log')
        console_warn_count = js_content.count('console.warn')
        console_error_count = js_content.count('console.error')
        try_catch_blocks = js_content.count('try {')
        
        print(f"Console.log statements: {console_log_count}")
        print(f"Console.warn statements: {console_warn_count}")
        print(f"Console.error statements: {console_error_count}")
        print(f"Try-catch blocks: {try_catch_blocks}")
        
        # Should have comprehensive logging and error handling
        assert console_log_count >= 5, "Insufficient logging for debugging"
        assert console_warn_count >= 1, "No warning messages for edge cases"
        assert try_catch_blocks >= 3, "Insufficient error handling"

    def test_chart_creation_logging(self):
        """Test: Verify chart creation includes proper logging."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for chart creation success logging
        has_correlation_success_log = 'Correlation chart created successfully' in js_content
        has_forecast_success_log = 'Forecast chart created successfully' in js_content
        has_chart_id_logging = 'this.correlationChart.id' in js_content or 'this.forecastChart.id' in js_content
        
        print(f"Correlation chart success logging: {has_correlation_success_log}")
        print(f"Forecast chart success logging: {has_forecast_success_log}")
        print(f"Chart ID logging: {has_chart_id_logging}")
        
        assert has_correlation_success_log and has_forecast_success_log and has_chart_id_logging, \
            "Chart creation logging not properly implemented"

    def test_cleanup_on_unload(self):
        """Test: Verify proper cleanup on page unload."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for beforeunload event listener
        has_beforeunload = 'beforeunload' in js_content
        has_cleanup_call = 'predictiveAnalytics.cleanup()' in js_content
        has_init_flag_reset = 'dashboardInitialized = false' in js_content
        has_instance_clear = 'PredictiveAnalyticsDashboard.instance = null' in js_content
        
        print(f"Beforeunload listener: {has_beforeunload}")
        print(f"Cleanup call: {has_cleanup_call}")
        print(f"Init flag reset: {has_init_flag_reset}")
        print(f"Instance clear: {has_instance_clear}")
        
        assert has_beforeunload and has_cleanup_call and has_init_flag_reset and has_instance_clear, \
            "Proper cleanup on unload not implemented"

    def test_global_debug_access(self):
        """Test: Verify global debug access is available."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Check for global debug access
        has_global_access = 'window.PredictiveAnalyticsDashboard' in js_content
        
        print(f"Global debug access: {has_global_access}")
        
        assert has_global_access, "Global debug access not available"


def create_test_html_file():
    """Create a test HTML file to manually verify the fix."""
    test_html = """<!DOCTYPE html>
<html>
<head>
    <title>Chart Canvas Reuse Fix Test</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .chart-container { width: 400px; height: 300px; margin: 20px 0; border: 1px solid #ccc; }
        button { padding: 10px 20px; margin: 10px; font-size: 16px; }
        .logs { background: #f0f0f0; padding: 10px; margin: 20px 0; height: 200px; overflow-y: scroll; }
    </style>
</head>
<body>
    <h1>Chart.js Canvas Reuse Fix Test</h1>
    
    <div class="chart-container">
        <canvas id="forecast-chart"></canvas>
    </div>
    <div class="chart-container">
        <canvas id="correlation-chart"></canvas>
    </div>
    
    <button onclick="recreateChartsBasic()">Recreate Charts (Basic Method)</button>
    <button onclick="recreateChartsFixed()">Recreate Charts (Fixed Method)</button>
    <button onclick="clearLogs()">Clear Logs</button>
    
    <div class="logs" id="logs"></div>
    
    <script>
        let forecastChart = null;
        let correlationChart = null;
        let charts = new Map();
        
        // Logging function
        function log(message) {
            const logsDiv = document.getElementById('logs');
            const timestamp = new Date().toLocaleTimeString();
            logsDiv.innerHTML += `[${timestamp}] ${message}<br>`;
            logsDiv.scrollTop = logsDiv.scrollHeight;
            console.log(message);
        }
        
        function clearLogs() {
            document.getElementById('logs').innerHTML = '';
        }
        
        // Basic recreation method (old way - will cause errors)
        function recreateChartsBasic() {
            log('=== BASIC RECREATION (OLD METHOD) ===');
            
            try {
                const forecastCtx = document.getElementById('forecast-chart');
                const correlationCtx = document.getElementById('correlation-chart');
                
                // Old way - just destroy without registry cleanup
                if (forecastChart) {
                    log('Destroying forecast chart (basic method)');
                    forecastChart.destroy();
                }
                if (correlationChart) {
                    log('Destroying correlation chart (basic method)');
                    correlationChart.destroy();
                }
                
                // Recreate charts
                forecastChart = new Chart(forecastCtx, {
                    type: 'line',
                    data: {
                        labels: ['Jan', 'Feb', 'Mar', 'Apr'],
                        datasets: [{
                            label: 'Sales Forecast',
                            data: [10, 20, 30, 25],
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    }
                });
                
                correlationChart = new Chart(correlationCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Weather', 'Events', 'Seasonality'],
                        datasets: [{
                            label: 'Correlation Strength',
                            data: [0.7, 0.5, 0.9],
                            backgroundColor: ['rgba(255, 99, 132, 0.2)', 'rgba(54, 162, 235, 0.2)', 'rgba(255, 205, 86, 0.2)']
                        }]
                    }
                });
                
                log('Charts recreated successfully (basic method)');
                
            } catch (error) {
                log(`ERROR with basic method: ${error.message}`);
            }
        }
        
        // Fixed recreation method (new way - should work without errors)
        function recreateChartsFixed() {
            log('=== FIXED RECREATION (NEW METHOD) ===');
            
            try {
                // Fixed way - comprehensive destruction
                destroyChartCompletely('forecast-chart');
                destroyChartCompletely('correlation-chart');
                
                const forecastCtx = document.getElementById('forecast-chart');
                const correlationCtx = document.getElementById('correlation-chart');
                
                // Recreate charts
                forecastChart = new Chart(forecastCtx, {
                    type: 'line',
                    data: {
                        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                        datasets: [{
                            label: 'Revenue Forecast',
                            data: [100, 150, 180, 200],
                            borderColor: 'rgb(255, 99, 132)',
                            tension: 0.1
                        }]
                    }
                });
                
                correlationChart = new Chart(correlationCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Marketing', 'Pricing', 'Competition'],
                        datasets: [{
                            label: 'Impact Factor',
                            data: [0.8, 0.6, 0.4],
                            backgroundColor: ['rgba(75, 192, 192, 0.2)', 'rgba(153, 102, 255, 0.2)', 'rgba(255, 159, 64, 0.2)']
                        }]
                    }
                });
                
                charts.set('forecast-chart', forecastChart);
                charts.set('correlation-chart', correlationChart);
                
                log(`Forecast chart created with ID: ${forecastChart.id}`);
                log(`Correlation chart created with ID: ${correlationChart.id}`);
                log('Charts recreated successfully (fixed method)');
                
            } catch (error) {
                log(`ERROR with fixed method: ${error.message}`);
            }
        }
        
        // Comprehensive chart destruction (the fix)
        function destroyChartCompletely(canvasId) {
            try {
                // Method 1: Destroy from Chart.js registry
                const registryChart = Chart.getChart(canvasId);
                if (registryChart) {
                    log(`Destroying chart from registry: ${canvasId} (ID: ${registryChart.id})`);
                    registryChart.destroy();
                }
                
                // Method 2: Destroy from our tracking Map
                const trackedChart = charts.get(canvasId);
                if (trackedChart && typeof trackedChart.destroy === 'function') {
                    log(`Destroying tracked chart: ${canvasId}`);
                    trackedChart.destroy();
                    charts.delete(canvasId);
                }
                
                // Method 3: Destroy from instance variables
                if (canvasId === 'correlation-chart' && correlationChart) {
                    log('Destroying correlationChart instance');
                    correlationChart.destroy();
                    correlationChart = null;
                }
                if (canvasId === 'forecast-chart' && forecastChart) {
                    log('Destroying forecastChart instance');
                    forecastChart.destroy();
                    forecastChart = null;
                }
                
                // Method 4: Clean canvas element
                const canvas = document.getElementById(canvasId);
                if (canvas && canvas.getContext) {
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        log(`Canvas cleared: ${canvasId}`);
                    }
                }
                
            } catch (error) {
                log(`Error during chart destruction for ${canvasId}: ${error.message}`);
                // If all else fails, replace the canvas element
                replaceCanvasElement(canvasId);
            }
        }
        
        // Canvas element replacement
        function replaceCanvasElement(canvasId) {
            const oldCanvas = document.getElementById(canvasId);
            if (oldCanvas) {
                log(`Replacing canvas element: ${canvasId}`);
                const newCanvas = oldCanvas.cloneNode(false);
                newCanvas.className = oldCanvas.className;
                newCanvas.style.cssText = oldCanvas.style.cssText;
                oldCanvas.parentNode.replaceChild(newCanvas, oldCanvas);
            }
        }
        
        // Initial chart creation
        document.addEventListener('DOMContentLoaded', function() {
            log('DOM loaded, creating initial charts...');
            recreateChartsFixed();
        });
        
        log('Test page loaded. Try both recreation methods to see the difference.');
    </script>
</body>
</html>"""
    
    test_file_path = '/tmp/chart_canvas_fix_test.html'
    with open(test_file_path, 'w') as f:
        f.write(test_html)
    
    return test_file_path


def run_fix_validation_tests():
    """Run all tests to validate the fix."""
    test_instance = TestChartCanvasFix()
    test_instance.setup_class()
    
    print("=== CHART CANVAS REUSE FIX VALIDATION ===")
    
    test_results = {}
    
    tests = [
        ('Singleton Pattern', test_instance.test_singleton_pattern_implemented),
        ('Chart Registry Management', test_instance.test_chart_registry_management),
        ('Comprehensive Destruction', test_instance.test_comprehensive_destruction_method),
        ('Canvas Element Replacement', test_instance.test_canvas_element_replacement),
        ('Duplicate Script Load Removal', test_instance.test_duplicate_script_load_removed),
        ('Initialization Guard', test_instance.test_initialization_guard),
        ('Error Handling', test_instance.test_error_handling_and_logging),
        ('Chart Creation Logging', test_instance.test_chart_creation_logging),
        ('Cleanup on Unload', test_instance.test_cleanup_on_unload),
        ('Global Debug Access', test_instance.test_global_debug_access),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n--- {test_name} ---")
            test_func()
            test_results[test_name] = 'PASSED'
            passed += 1
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            test_results[test_name] = f'FAILED: {e}'
            failed += 1
            print(f"❌ {test_name}: FAILED - {e}")
    
    print(f"\n=== TEST SUMMARY ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {len(tests)}")
    
    if failed == 0:
        print("🎉 All tests passed! The fix should resolve the canvas reuse errors.")
        
        # Create test HTML file
        test_file = create_test_html_file()
        print(f"\n📋 Manual test file created: {test_file}")
        print("Open this file in a browser to manually verify the fix works correctly.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_fix_validation_tests()
    exit(0 if success else 1)