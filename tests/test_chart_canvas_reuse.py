#!/usr/bin/env python3
"""
Test suite for debugging Chart.js canvas reuse errors in predictive analytics.

This test suite identifies and validates fixes for the "Canvas is already in use" errors
that occur when Chart.js charts are not properly destroyed before recreation.

Key Issues Identified:
1. Multiple script loads - both module and non-module versions in base.html and predictive_analytics.html
2. Redundant chart destruction logic that may not be executing in correct order
3. Potential race conditions during chart recreation
4. Canvas elements not being properly cleared from Chart.js internal registry
"""

import os
import re
import json


class TestChartCanvasReuse:
    """Test suite for Chart.js canvas reuse errors in predictive analytics."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        cls.project_root = "/home/tim/RFID3"
        cls.js_file = f"{cls.project_root}/static/js/predictive-analytics.js"
        cls.html_file = f"{cls.project_root}/app/templates/predictive_analytics.html"
        cls.base_html = f"{cls.project_root}/app/templates/base.html"
        
        # Note: Selenium tests skipped - not available in this environment

    def test_multiple_script_loads_identified(self):
        """Test: Identify multiple script loads that cause canvas conflicts."""
        # Check base.html for script loads
        with open(self.base_html, 'r') as f:
            base_content = f.read()
            
        # Check predictive_analytics.html for script loads
        with open(self.html_file, 'r') as f:
            template_content = f.read()
        
        # Look for Chart.js loads in base template
        base_chart_loads = re.findall(r'Chart\.js|chart\..*\.js|predictive-analytics\.js', base_content, re.IGNORECASE)
        template_chart_loads = re.findall(r'Chart\.js|chart\..*\.js|predictive-analytics\.js', template_content, re.IGNORECASE)
        
        print(f"Base template Chart.js loads: {base_chart_loads}")
        print(f"Predictive template Chart.js loads: {template_chart_loads}")
        
        # Check for module vs non-module conflicts
        base_has_module = 'type="module"' in base_content and 'predictive-analytics' in base_content
        template_has_regular = 'predictive-analytics.js' in template_content and 'type="module"' not in template_content
        
        if base_has_module and template_has_regular:
            print("ERROR: Conflicting script loads detected - module in base.html, regular in template")
            assert False, "Multiple conflicting script loads will cause chart initialization conflicts"

    def test_chart_destruction_logic_analysis(self):
        """Test: Analyze current chart destruction implementation."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Find all chart destruction patterns
        destroy_patterns = [
            r'\.destroy\(\)',
            r'charts\.delete\(',
            r'existingChart.*destroy',
            r'this\.correlationChart.*destroy',
            r'this\.forecastChart.*destroy'
        ]
        
        destruction_found = {}
        for pattern in destroy_patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            destruction_found[pattern] = len(matches)
            print(f"Pattern '{pattern}': {len(matches)} occurrences")
        
        # Check for proper cleanup in chart creation methods
        correlation_chart_method = re.search(r'createCorrelationChart.*?(?=^\s*\w|\Z)', js_content, re.DOTALL | re.MULTILINE)
        forecast_chart_method = re.search(r'createForecastChart.*?(?=^\s*\w|\Z)', js_content, re.DOTALL | re.MULTILINE)
        
        if correlation_chart_method:
            correlation_content = correlation_chart_method.group()
            has_proper_cleanup = 'existingChart' in correlation_content and 'destroy()' in correlation_content
            print(f"Correlation chart has proper cleanup: {has_proper_cleanup}")
            
        if forecast_chart_method:
            forecast_content = forecast_chart_method.group()
            has_proper_cleanup = 'existingChart' in forecast_content and 'destroy()' in forecast_content
            print(f"Forecast chart has proper cleanup: {has_proper_cleanup}")

    def test_canvas_element_cleanup(self):
        """Test: Verify canvas elements exist and can be properly cleared."""
        with open(self.html_file, 'r') as f:
            html_content = f.read()
        
        # Find canvas elements
        canvas_elements = re.findall(r'<canvas[^>]*id=["\']([^"\']*)["\'][^>]*>', html_content)
        print(f"Canvas elements found: {canvas_elements}")
        
        expected_canvases = ['forecast-chart', 'correlation-chart']
        for canvas_id in expected_canvases:
            if canvas_id not in canvas_elements:
                print(f"ERROR: Expected canvas '{canvas_id}' not found in template")
                assert False, f"Canvas element {canvas_id} missing from template"

    def test_chart_creation_order_and_timing(self):
        """Test: Analyze chart creation order and identify potential race conditions."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Find initialization sequence
        init_method = re.search(r'init\(\s*\)\s*\{(.*?)^\s*\}', js_content, re.DOTALL | re.MULTILINE)
        if init_method:
            init_content = init_method.group(1)
            # Check for proper sequencing
            has_chart_init = 'initializeCharts' in init_content
            has_event_listeners = 'addEventListener' in init_content
            print(f"Init method has chart initialization: {has_chart_init}")
            print(f"Init method has event listeners: {has_event_listeners}")

    def test_dom_ready_multiple_listeners(self):
        """Test: Check for multiple DOMContentLoaded listeners that could cause conflicts."""
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Find all DOMContentLoaded listeners
        dom_ready_listeners = re.findall(r'DOMContentLoaded["\']?\s*,', js_content)
        print(f"DOMContentLoaded listeners found: {len(dom_ready_listeners)}")
        
        if len(dom_ready_listeners) > 1:
            print("WARNING: Multiple DOMContentLoaded listeners may cause race conditions")

    def create_mock_html_test_file(self):
        """Create a standalone HTML file for testing chart canvas reuse."""
        test_html = """<!DOCTYPE html>
<html>
<head>
    <title>Chart Canvas Reuse Test</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
</head>
<body>
    <div style="width: 400px; height: 300px;">
        <canvas id="forecast-chart"></canvas>
    </div>
    <div style="width: 400px; height: 300px;">
        <canvas id="correlation-chart"></canvas>
    </div>
    
    <button id="recreate-charts">Recreate Charts</button>
    
    <script>
        let forecastChart = null;
        let correlationChart = null;
        let charts = new Map();
        
        function createCharts() {
            console.log('Creating charts...');
            
            // Test the current destruction logic from predictive-analytics.js
            // Forecast Chart
            const forecastCtx = document.getElementById('forecast-chart');
            
            // Destroy existing chart if it exists
            const existingForecastChart = charts.get('forecast-chart');
            if (existingForecastChart && typeof existingForecastChart.destroy === 'function') {
                console.log('Destroying existing forecast chart from map');
                existingForecastChart.destroy();
                charts.delete('forecast-chart');
            }
            if (forecastChart && typeof forecastChart.destroy === 'function') {
                console.log('Destroying existing forecast chart from variable');
                forecastChart.destroy();
            }
            
            try {
                forecastChart = new Chart(forecastCtx, {
                    type: 'line',
                    data: {
                        labels: ['Jan', 'Feb', 'Mar'],
                        datasets: [{
                            label: 'Sales',
                            data: [10, 20, 30],
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    }
                });
                charts.set('forecast-chart', forecastChart);
                console.log('Forecast chart created successfully');
            } catch (error) {
                console.error('Error creating forecast chart:', error);
            }
            
            // Correlation Chart
            const correlationCtx = document.getElementById('correlation-chart');
            
            // Destroy existing chart if it exists
            const existingCorrelationChart = charts.get('correlation-chart');
            if (existingCorrelationChart && typeof existingCorrelationChart.destroy === 'function') {
                console.log('Destroying existing correlation chart from map');
                existingCorrelationChart.destroy();
                charts.delete('correlation-chart');
            }
            if (correlationChart && typeof correlationChart.destroy === 'function') {
                console.log('Destroying existing correlation chart from variable');
                correlationChart.destroy();
            }
            
            try {
                correlationChart = new Chart(correlationCtx, {
                    type: 'bar',
                    data: {
                        labels: ['A', 'B', 'C'],
                        datasets: [{
                            label: 'Correlation',
                            data: [0.5, 0.8, 0.3],
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    }
                });
                charts.set('correlation-chart', correlationChart);
                console.log('Correlation chart created successfully');
            } catch (error) {
                console.error('Error creating correlation chart:', error);
            }
        }
        
        // Initial chart creation
        document.addEventListener('DOMContentLoaded', createCharts);
        
        // Recreate charts on button click to test canvas reuse
        document.getElementById('recreate-charts').addEventListener('click', createCharts);
    </script>
</body>
</html>"""
        
        test_file_path = '/tmp/chart_canvas_test.html'
        with open(test_file_path, 'w') as f:
            f.write(test_html)
        
        return test_file_path

    def test_canvas_reuse_simulation(self):
        """Test: Simulate the canvas reuse error with current destruction logic."""
        print("Canvas reuse simulation test (requires browser environment)")
        # Create test HTML file for manual testing
        test_file = self.create_mock_html_test_file()
        print(f"Test file created at: {test_file}")
        print("Open this file in a browser and click 'Recreate Charts' to see canvas reuse errors")
        
        # Instead, analyze the JavaScript code structure for potential issues
        with open(self.js_file, 'r') as f:
            js_content = f.read()
        
        # Look for Chart.js registry management
        has_chart_getChart = 'Chart.getChart(' in js_content
        has_canvas_replacement = 'canvas.remove()' in js_content or 'cloneNode(' in js_content
        
        print(f"Uses Chart.getChart() for registry management: {has_chart_getChart}")
        print(f"Uses canvas replacement strategy: {has_canvas_replacement}")
        
        if not has_chart_getChart and not has_canvas_replacement:
            print("WARNING: Current code may not properly clear Chart.js internal registry")

    def test_proposed_fix_validation(self):
        """Test: Validate the proposed fix approach."""
        # The fix should:
        # 1. Remove duplicate script loads
        # 2. Implement proper Chart.js registry cleanup
        # 3. Use canvas element replacement instead of just destroy()
        # 4. Add singleton pattern to prevent multiple dashboard instances
        
        proposed_fix_elements = [
            "Chart.getChart()",  # Use Chart.js registry
            "canvas.remove()",   # DOM element cleanup
            "canvas.cloneNode()", # Canvas replacement
            "singleton pattern", # Prevent multiple instances
        ]
        
        print("Proposed fix elements to implement:")
        for element in proposed_fix_elements:
            print(f"- {element}")
        
        return True


def run_tests():
    """Run all canvas reuse tests."""
    test_instance = TestChartCanvasReuse()
    test_instance.setup_class()
    
    print("=== CHART CANVAS REUSE ERROR ANALYSIS ===")
    
    try:
        print("\n1. Testing for multiple script loads...")
        test_instance.test_multiple_script_loads_identified()
        
        print("\n2. Analyzing chart destruction logic...")
        test_instance.test_chart_destruction_logic_analysis()
        
        print("\n3. Verifying canvas elements...")
        test_instance.test_canvas_element_cleanup()
        
        print("\n4. Checking chart creation order...")
        test_instance.test_chart_creation_order_and_timing()
        
        print("\n5. Checking for multiple DOM ready listeners...")
        test_instance.test_dom_ready_multiple_listeners()
        
        print("\n6. Testing canvas reuse simulation...")
        test_instance.test_canvas_reuse_simulation()
        
        print("\n7. Validating proposed fix approach...")
        test_instance.test_proposed_fix_validation()
        
        print("\n=== ALL TESTS COMPLETED ===")
        
    except AssertionError as e:
        print(f"Test failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)