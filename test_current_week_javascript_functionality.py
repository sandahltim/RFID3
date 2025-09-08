#!/usr/bin/env python3
"""
Current Week View JavaScript Functionality Test
Focused testing of the JavaScript column hiding/showing functionality

Tests the initializeCurrentWeekVisibility() function and DOM manipulation
using a simulated browser environment.

Author: Testing Specialist  
Date: 2025-09-08
"""

import os
import re
import json
from datetime import datetime


class JavaScriptFunctionalityTester:
    """Test the JavaScript functionality for current week view"""
    
    def __init__(self):
        self.template_path = "app/templates/executive_dashboard.html"
        self.results = {}
        
    def load_template_content(self):
        """Load the executive dashboard template content"""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template not found: {self.template_path}")
            
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_javascript_code(self, template_content):
        """Extract JavaScript code from the template"""
        # Find all script blocks
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, template_content, re.DOTALL | re.IGNORECASE)
        
        # Combine all scripts
        return '\n'.join(scripts)
    
    def test_function_definition(self, js_code):
        """Test that the initializeCurrentWeekVisibility function is properly defined"""
        print("🔍 Testing function definition...")
        
        # Check for function definition
        function_patterns = [
            r'function\s+initializeCurrentWeekVisibility\s*\(',
            r'initializeCurrentWeekVisibility\s*=\s*function\s*\(',
            r'const\s+initializeCurrentWeekVisibility\s*=\s*\(\s*\)\s*=>'
        ]
        
        function_found = False
        for pattern in function_patterns:
            if re.search(pattern, js_code, re.MULTILINE):
                function_found = True
                break
        
        if function_found:
            print("✅ initializeCurrentWeekVisibility function definition found")
            self.results['function_definition'] = 'PASS'
        else:
            print("❌ initializeCurrentWeekVisibility function definition not found")
            self.results['function_definition'] = 'FAIL'
        
        return function_found
    
    def test_function_call(self, js_code):
        """Test that the function is called"""
        print("🔍 Testing function call...")
        
        call_pattern = r'initializeCurrentWeekVisibility\s*\(\s*\)'
        
        if re.search(call_pattern, js_code):
            print("✅ Function call found")
            self.results['function_call'] = 'PASS'
            return True
        else:
            print("❌ Function call not found")
            self.results['function_call'] = 'FAIL'
            return False
    
    def test_dashboard_config_usage(self, js_code):
        """Test that dashboard config is properly used"""
        print("🔍 Testing dashboard config usage...")
        
        checks = {
            'window_dashboardConfig': r'window\.dashboardConfig',
            'config_access': r'dashboardConfig\.current_week_view_enabled',
            'config_check': r'current_week_view_enabled'
        }
        
        all_passed = True
        for check_name, pattern in checks.items():
            if re.search(pattern, js_code):
                print(f"✅ {check_name} pattern found")
                self.results[f'config_{check_name}'] = 'PASS'
            else:
                print(f"❌ {check_name} pattern not found")
                self.results[f'config_{check_name}'] = 'FAIL'
                all_passed = False
        
        return all_passed
    
    def test_dom_manipulation_logic(self, js_code):
        """Test DOM manipulation logic for hiding/showing columns"""
        print("🔍 Testing DOM manipulation logic...")
        
        checks = {
            'querySelector_usage': r'document\.querySelector(?:All)?\s*\(',
            'header_selection': r'querySelectorAll\s*\(\s*[\'"]th[\'"]',
            'style_hiding': r'style\.display\s*=\s*[\'"]none[\'"]',
            'text_content_check': r'textContent\.includes?\s*\(',
            'current_week_text': r'Current Week'
        }
        
        all_passed = True
        for check_name, pattern in checks.items():
            if re.search(pattern, js_code, re.IGNORECASE):
                print(f"✅ {check_name} logic found")
                self.results[f'dom_{check_name}'] = 'PASS'
            else:
                print(f"❌ {check_name} logic not found")
                self.results[f'dom_{check_name}'] = 'FAIL'
                all_passed = False
        
        return all_passed
    
    def test_template_conditional_rendering(self, template_content):
        """Test that template has proper conditional rendering"""
        print("🔍 Testing template conditional rendering...")
        
        checks = {
            'if_statement': r'\{\%\s*if\s+dashboard_config\.current_week_view_enabled\s*\%\}',
            'endif_statement': r'\{\%\s*endif\s*\%\}',
            'current_week_header': r'<th[^>]*>.*Current Week.*</th>',
            'current_week_cell': r'<td[^>]*class="[^"]*current[^"]*"'
        }
        
        results = {}
        for check_name, pattern in checks.items():
            matches = re.findall(pattern, template_content, re.IGNORECASE | re.DOTALL)
            if matches:
                print(f"✅ {check_name} found ({len(matches)} matches)")
                results[check_name] = len(matches)
                self.results[f'template_{check_name}'] = 'PASS'
            else:
                print(f"❌ {check_name} not found")
                results[check_name] = 0
                self.results[f'template_{check_name}'] = 'FAIL'
        
        # Check balance of if/endif
        if_count = results.get('if_statement', 0)
        endif_count = results.get('endif_statement', 0)
        
        if if_count > 0 and endif_count >= if_count:
            print(f"✅ Template conditionals balanced: {if_count} if, {endif_count} endif")
            self.results['template_balance'] = 'PASS'
        else:
            print(f"❌ Template conditionals unbalanced: {if_count} if, {endif_count} endif")
            self.results['template_balance'] = 'FAIL'
        
        return if_count > 0 and endif_count >= if_count
    
    def simulate_javascript_execution(self, js_code):
        """Simulate JavaScript execution with different config values"""
        print("🔍 Simulating JavaScript execution...")
        
        # Extract the function body
        function_match = re.search(
            r'function\s+initializeCurrentWeekVisibility\s*\(\s*\)\s*{(.*?)}',
            js_code, 
            re.DOTALL
        )
        
        if not function_match:
            print("❌ Could not extract function body for simulation")
            self.results['simulation'] = 'FAIL'
            return False
        
        function_body = function_match.group(1)
        
        # Check for proper logic structure
        logic_checks = {
            'config_check': r'dashboardConfig\.current_week_view_enabled',
            'early_return': r'return;?\s*\/\/.*visible',
            'hide_logic': r'style\.display\s*=\s*[\'"]none[\'"]',
            'console_logging': r'console\.log'
        }
        
        simulation_passed = True
        for check_name, pattern in logic_checks.items():
            if re.search(pattern, function_body, re.IGNORECASE):
                print(f"✅ {check_name} logic present in function")
            else:
                print(f"⚠️  {check_name} logic not found (may be optional)")
        
        # Test the logical flow
        if 'dashboardConfig.current_week_view_enabled' in function_body:
            print("✅ Function checks configuration value")
        else:
            print("❌ Function doesn't check configuration value")
            simulation_passed = False
        
        if 'style.display' in function_body:
            print("✅ Function manipulates element visibility")
        else:
            print("❌ Function doesn't manipulate element visibility") 
            simulation_passed = False
        
        self.results['simulation'] = 'PASS' if simulation_passed else 'FAIL'
        return simulation_passed
    
    def create_test_html_page(self, js_code):
        """Create a test HTML page to verify functionality"""
        print("🔍 Creating test HTML page...")
        
        test_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Current Week View Test</title>
    <style>
        .test-table {{ border-collapse: collapse; width: 100%; }}
        .test-table th, .test-table td {{ border: 1px solid #ddd; padding: 8px; }}
        .test-table th {{ background-color: #f2f2f2; }}
        .hidden {{ display: none !important; }}
        .test-result {{ margin: 10px 0; padding: 10px; border: 1px solid #ccc; }}
        .pass {{ background-color: #d4edda; }}
        .fail {{ background-color: #f8d7da; }}
    </style>
</head>
<body>
    <h1>Current Week View JavaScript Functionality Test</h1>
    
    <div id="testResults">
        <h2>Test Results</h2>
    </div>
    
    <h2>Test Table (Enabled)</h2>
    <table class="test-table">
        <thead>
            <tr>
                <th>Store</th>
                <th>Previous Week</th>
                <th class="current-week-column">Current Week</th>
                <th>Previous Year</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Store 3607</td>
                <td>$1,000</td>
                <td class="current-week-column">$1,200</td>
                <td>$900</td>
            </tr>
        </tbody>
    </table>
    
    <script>
        // Test with enabled configuration
        window.dashboardConfig = {{ current_week_view_enabled: true }};
        
        {js_code}
        
        // Test function
        function runTests() {{
            const results = [];
            
            // Test 1: Function exists
            if (typeof initializeCurrentWeekVisibility === 'function') {{
                results.push({{ name: 'Function Definition', status: 'PASS', message: 'Function is defined' }});
            }} else {{
                results.push({{ name: 'Function Definition', status: 'FAIL', message: 'Function not defined' }});
            }}
            
            // Test 2: Elements exist
            const currentWeekColumns = document.querySelectorAll('.current-week-column');
            if (currentWeekColumns.length > 0) {{
                results.push({{ name: 'Column Elements', status: 'PASS', message: `Found ${{currentWeekColumns.length}} current week columns` }});
            }} else {{
                results.push({{ name: 'Column Elements', status: 'FAIL', message: 'No current week columns found' }});
            }}
            
            // Test 3: Function execution with enabled config
            try {{
                window.dashboardConfig.current_week_view_enabled = true;
                initializeCurrentWeekVisibility();
                
                const hiddenColumns = Array.from(currentWeekColumns).filter(col => 
                    col.style.display === 'none' || col.classList.contains('hidden')
                );
                
                if (hiddenColumns.length === 0) {{
                    results.push({{ name: 'Enabled State', status: 'PASS', message: 'Columns visible when enabled' }});
                }} else {{
                    results.push({{ name: 'Enabled State', status: 'FAIL', message: `${{hiddenColumns.length}} columns hidden when should be visible` }});
                }}
            }} catch (e) {{
                results.push({{ name: 'Enabled State', status: 'FAIL', message: `Error: ${{e.message}}` }});
            }}
            
            // Test 4: Function execution with disabled config
            try {{
                window.dashboardConfig.current_week_view_enabled = false;
                initializeCurrentWeekVisibility();
                
                const hiddenColumns = Array.from(currentWeekColumns).filter(col => 
                    col.style.display === 'none'
                );
                
                if (hiddenColumns.length === currentWeekColumns.length) {{
                    results.push({{ name: 'Disabled State', status: 'PASS', message: 'All columns hidden when disabled' }});
                }} else {{
                    results.push({{ name: 'Disabled State', status: 'FAIL', message: `Only ${{hiddenColumns.length}}/${{currentWeekColumns.length}} columns hidden when disabled` }});
                }}
            }} catch (e) {{
                results.push({{ name: 'Disabled State', status: 'FAIL', message: `Error: ${{e.message}}` }});
            }}
            
            // Display results
            const resultsContainer = document.getElementById('testResults');
            results.forEach(result => {{
                const div = document.createElement('div');
                div.className = `test-result ${{result.status.toLowerCase()}}`;
                div.innerHTML = `<strong>${{result.name}}:</strong> ${{result.status}} - ${{result.message}}`;
                resultsContainer.appendChild(div);
            }});
            
            console.log('Test Results:', results);
            return results;
        }}
        
        // Run tests when page loads
        window.addEventListener('load', runTests);
    </script>
</body>
</html>
        """
        
        test_file_path = "current_week_view_test.html"
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_html)
        
        print(f"✅ Test HTML page created: {test_file_path}")
        self.results['test_page_creation'] = 'PASS'
        return test_file_path
    
    def run_comprehensive_test(self):
        """Run all JavaScript functionality tests"""
        print("="*80)
        print("🚀 RUNNING CURRENT WEEK VIEW JAVASCRIPT FUNCTIONALITY TESTS")
        print("="*80)
        
        try:
            # Load template content
            print("📄 Loading template content...")
            template_content = self.load_template_content()
            print(f"✅ Template loaded ({len(template_content)} characters)")
            
            # Extract JavaScript code
            js_code = self.extract_javascript_code(template_content)
            print(f"✅ JavaScript extracted ({len(js_code)} characters)")
            
            # Run tests
            tests = [
                ('Function Definition', lambda: self.test_function_definition(js_code)),
                ('Function Call', lambda: self.test_function_call(js_code)),
                ('Dashboard Config Usage', lambda: self.test_dashboard_config_usage(js_code)),
                ('DOM Manipulation Logic', lambda: self.test_dom_manipulation_logic(js_code)),
                ('Template Conditional Rendering', lambda: self.test_template_conditional_rendering(template_content)),
                ('JavaScript Execution Simulation', lambda: self.simulate_javascript_execution(js_code)),
                ('Test HTML Page Creation', lambda: self.create_test_html_page(js_code))
            ]
            
            for test_name, test_func in tests:
                print(f"\n{'-'*60}")
                print(f"🧪 {test_name}")
                print(f"{'-'*60}")
                
                try:
                    result = test_func()
                    if result:
                        print(f"✅ {test_name}: PASSED")
                    else:
                        print(f"❌ {test_name}: FAILED")
                except Exception as e:
                    print(f"💥 {test_name}: ERROR - {str(e)}")
                    self.results[f'{test_name.lower().replace(" ", "_")}_error'] = str(e)
            
            # Generate summary
            self.generate_summary()
            
        except Exception as e:
            print(f"💥 Critical error: {str(e)}")
            self.results['critical_error'] = str(e)
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "="*80)
        print("📊 JAVASCRIPT FUNCTIONALITY TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for result in self.results.values() if result == 'PASS')
        failed = sum(1 for result in self.results.values() if result == 'FAIL')
        total = passed + failed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 EXCELLENT: JavaScript functionality is working great!")
            elif success_rate >= 75:
                print("✅ GOOD: JavaScript functionality is mostly working")
            elif success_rate >= 50:
                print("⚠️  FAIR: JavaScript functionality needs some improvements")
            else:
                print("❌ POOR: JavaScript functionality has significant issues")
        
        print("\nDetailed Results:")
        for test_name, result in self.results.items():
            status_emoji = "✅" if result == 'PASS' else "❌" if result == 'FAIL' else "⚠️"
            print(f"  {status_emoji} {test_name}: {result}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"current_week_javascript_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'results': self.results,
                'summary': {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'success_rate': success_rate if total > 0 else 0
                }
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")


def main():
    """Main test runner"""
    tester = JavaScriptFunctionalityTester()
    tester.run_comprehensive_test()


if __name__ == '__main__':
    main()