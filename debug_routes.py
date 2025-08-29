#!/usr/bin/env python3
"""
Debug script to check registered Flask routes
"""

from app import create_app

def list_routes():
    """List all registered routes in the Flask application"""
    app = create_app()
    
    print("=" * 80)
    print("FLASK APPLICATION REGISTERED ROUTES")
    print("=" * 80)
    
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.rule, methods, rule.endpoint))
    
    # Sort routes by URL
    routes.sort()
    
    predictive_routes = []
    analytics_routes = []
    other_routes = []
    
    for rule, methods, endpoint in routes:
        if '/api/predictive' in rule:
            predictive_routes.append((rule, methods, endpoint))
        elif '/api/enhanced' in rule or '/api/analytics' in rule or '/bi/api' in rule:
            analytics_routes.append((rule, methods, endpoint))
        else:
            other_routes.append((rule, methods, endpoint))
    
    print(f"Total routes: {len(routes)}")
    print()
    
    if predictive_routes:
        print("PREDICTIVE ANALYTICS ROUTES:")
        print("-" * 40)
        for rule, methods, endpoint in predictive_routes:
            print(f"{methods:8} {rule:50} -> {endpoint}")
        print()
    else:
        print("❌ NO PREDICTIVE ANALYTICS ROUTES FOUND")
        print()
    
    if analytics_routes:
        print("ANALYTICS ROUTES:")
        print("-" * 40)
        for rule, methods, endpoint in analytics_routes:
            print(f"{methods:8} {rule:50} -> {endpoint}")
        print()
    
    if not predictive_routes and not analytics_routes:
        print("❌ NO API ROUTES FOUND - CHECKING ALL ROUTES:")
        print("-" * 40)
        for rule, methods, endpoint in routes[:20]:  # Show first 20 routes
            print(f"{methods:8} {rule:50} -> {endpoint}")
        if len(routes) > 20:
            print(f"... and {len(routes) - 20} more routes")
    
    # Check for blueprint errors
    print("\nBLUEPRINT ANALYSIS:")
    print("-" * 40)
    
    blueprint_routes = {}
    for rule, methods, endpoint in routes:
        blueprint_name = endpoint.split('.')[0] if '.' in endpoint else 'main'
        if blueprint_name not in blueprint_routes:
            blueprint_routes[blueprint_name] = 0
        blueprint_routes[blueprint_name] += 1
    
    for blueprint, count in sorted(blueprint_routes.items()):
        print(f"{blueprint:30} {count:3} routes")
    
    if 'predictive_analytics' not in blueprint_routes:
        print("❌ predictive_analytics blueprint not found in registered routes!")
    else:
        print(f"✅ predictive_analytics blueprint found with {blueprint_routes['predictive_analytics']} routes")

if __name__ == "__main__":
    list_routes()