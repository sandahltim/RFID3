"""
Equipment Categorization API Routes
Minnesota-specific equipment rental categorization endpoints
"""

from flask import Blueprint, jsonify, request
from app.services.equipment_categorization_service import EquipmentCategorizationService
from app.services.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

equipment_categorization_bp = Blueprint('equipment_categorization', __name__, url_prefix='/api/equipment-categorization')

@equipment_categorization_bp.route('/stores/profiles', methods=['GET'])
def get_all_store_profiles():
    """Get corrected store profiles for all locations"""
    try:
        categorization_service = EquipmentCategorizationService()
        
        all_profiles = {}
        store_codes = ['3607', '6800', '728', '8101']
        
        for store_code in store_codes:
            profile_result = categorization_service.get_store_profile(store_code)
            if profile_result['status'] == 'success':
                all_profiles[store_code] = profile_result['profile']
        
        return jsonify({
            'status': 'success',
            'store_profiles': all_profiles,
            'corrected_mappings': {
                '3607': 'Wayzata - A1 Rent It (90% DIY/10% Events)',
                '6800': 'Brooklyn Park - A1 Rent It (100% DIY Construction)',
                '728': 'Elk River - A1 Rent It (90% DIY/10% Events)', 
                '8101': 'Fridley - Broadway Tent & Event (100% Events)'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting store profiles: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@equipment_categorization_bp.route('/stores/<store_code>/profile', methods=['GET'])
def get_store_profile(store_code):
    """Get corrected profile for a specific store"""
    try:
        categorization_service = EquipmentCategorizationService()
        result = categorization_service.get_store_profile(store_code)
        
        if result['status'] == 'error':
            return jsonify(result), 400
        
        return jsonify({
            'status': 'success',
            'store_profile': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting store profile for {store_code}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@equipment_categorization_bp.route('/stores/<store_code>/compliance', methods=['GET'])
def analyze_store_compliance(store_code):
    """Analyze how well a store matches its expected business profile"""
    try:
        categorization_service = EquipmentCategorizationService()
        result = categorization_service.analyze_store_compliance(store_code)
        
        if result['status'] == 'error':
            return jsonify(result), 400
        
        return jsonify({
            'status': 'success',
            'compliance_analysis': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing compliance for {store_code}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@equipment_categorization_bp.route('/analyze/item', methods=['POST'])
def categorize_single_item():
    """
    Categorize a single equipment item
    
    Expected JSON:
    {
        "common_name": "Mini Excavator",
        "pos_category": "Construction",
        "pos_department": "Heavy Equipment",
        "pos_name": "Kubota Mini Excavator"
    }
    """
    try:
        data = request.get_json()
        if not data or not data.get('common_name'):
            return jsonify({
                'error': 'Missing required field: common_name',
                'status': 'error'
            }), 400
        
        categorization_service = EquipmentCategorizationService()
        
        result = categorization_service.categorize_equipment_item(
            common_name=data.get('common_name'),
            pos_category=data.get('pos_category'),
            pos_department=data.get('pos_department'),
            pos_name=data.get('pos_name')
        )
        
        return jsonify({
            'status': 'success',
            'categorization': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error categorizing single item: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@equipment_categorization_bp.route('/analyze/inventory-mix', methods=['GET'])
def analyze_inventory_mix():
    """
    Analyze the business mix (A1 Rent It vs Broadway Tent & Event)
    
    Query parameters:
    - store_code: Optional filter for specific store (3607, 6800, 728, 8101)
    """
    try:
        store_code = request.args.get('store_code')
        
        # Validate store code if provided
        valid_stores = ['3607', '6800', '728', '8101']
        if store_code and store_code not in valid_stores:
            return jsonify({
                'error': f'Invalid store_code. Must be one of: {valid_stores}',
                'status': 'error'
            }), 400
        
        categorization_service = EquipmentCategorizationService()
        result = categorization_service.analyze_inventory_mix(store_code=store_code)
        
        return jsonify({
            'status': 'success',
            'analysis': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing inventory mix: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@equipment_categorization_bp.route('/analyze/seasonal-demand', methods=['GET'])
def analyze_seasonal_demand():
    """
    Analyze seasonal equipment demand patterns for Minnesota
    
    Query parameters:
    - season: spring, summer, fall, winter, or current (default: current)
    """
    try:
        season = request.args.get('season', 'current').lower()
        valid_seasons = ['spring', 'summer', 'fall', 'winter', 'current']
        
        if season not in valid_seasons:
            return jsonify({
                'error': f'Invalid season. Must be one of: {valid_seasons}',
                'status': 'error'
            }), 400
        
        categorization_service = EquipmentCategorizationService()
        result = categorization_service.get_seasonal_equipment_demand(season=season)
        
        return jsonify({
            'status': 'success',
            'seasonal_analysis': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing seasonal demand: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@equipment_categorization_bp.route('/analyze/store-comparison', methods=['GET'])
def compare_stores():
    """
    Compare equipment categorization across all Minnesota stores
    """
    try:
        categorization_service = EquipmentCategorizationService()
        
        # Get analysis for each store
        stores = ['3607', '6800', '728', '8101']
        store_names = {
            '3607': 'Wayzata (Lake Events)',
            '6800': 'Brooklyn Park (Mixed)',
            '728': 'Fridley (Industrial)',
            '8101': 'Elk River (Rural)'
        }
        
        store_comparisons = {}
        overall_totals = {
            'total_items': 0,
            'total_construction_revenue': 0,
            'total_event_revenue': 0,
            'total_revenue': 0
        }
        
        for store_code in stores:
            analysis = categorization_service.analyze_inventory_mix(store_code=store_code)
            
            if analysis.get('status') == 'success':
                store_comparisons[store_code] = {
                    'store_name': store_names[store_code],
                    'analysis': analysis,
                    'business_focus': 'Construction' if analysis['business_mix']['actual_construction_ratio'] > 0.6 else 
                                   'Events' if analysis['business_mix']['actual_event_ratio'] > 0.4 else 'Balanced'
                }
                
                # Add to overall totals
                if analysis.get('category_breakdown'):
                    overall_totals['total_items'] += analysis['total_items_analyzed']
                    overall_totals['total_construction_revenue'] += analysis['category_breakdown']['A1_RentIt_Construction']['revenue']
                    overall_totals['total_event_revenue'] += analysis['category_breakdown']['Broadway_TentEvent']['revenue']
                    overall_totals['total_revenue'] += (
                        analysis['category_breakdown']['A1_RentIt_Construction']['revenue'] +
                        analysis['category_breakdown']['Broadway_TentEvent']['revenue'] +
                        analysis['category_breakdown']['Mixed_Category']['revenue']
                    )
        
        # Calculate company-wide ratios
        if overall_totals['total_revenue'] > 0:
            company_wide_ratios = {
                'construction_ratio': overall_totals['total_construction_revenue'] / overall_totals['total_revenue'],
                'event_ratio': overall_totals['total_event_revenue'] / overall_totals['total_revenue'],
                'target_construction': 0.70,
                'target_events': 0.30
            }
        else:
            company_wide_ratios = {
                'construction_ratio': 0,
                'event_ratio': 0,
                'target_construction': 0.70,
                'target_events': 0.30
            }
        
        # Generate strategic recommendations
        recommendations = []
        
        # Store-specific recommendations
        for store_code, store_data in store_comparisons.items():
            store_name = store_names[store_code]
            analysis = store_data['analysis']
            
            if store_code == '3607':  # Wayzata - should be event-focused
                if analysis['business_mix']['actual_event_ratio'] < 0.35:
                    recommendations.append(f"{store_name}: Increase event equipment for Lake Minnetonka market")
            elif store_code == '728':  # Fridley - should be construction-focused
                if analysis['business_mix']['actual_construction_ratio'] < 0.75:
                    recommendations.append(f"{store_name}: Optimize for construction in industrial corridor")
            elif store_code == '8101':  # Elk River - rural/agricultural focus
                if analysis['business_mix']['actual_construction_ratio'] > 0.80:
                    recommendations.append(f"{store_name}: Consider agricultural/outdoor event equipment")
        
        # Company-wide recommendations
        if company_wide_ratios['construction_ratio'] < 0.65:
            recommendations.append("Company-wide: Construction equipment below 70% target - growth opportunity")
        if company_wide_ratios['event_ratio'] < 0.25:
            recommendations.append("Company-wide: Event equipment below 30% target - expansion needed")
        
        return jsonify({
            'status': 'success',
            'store_comparisons': store_comparisons,
            'company_wide': {
                'totals': overall_totals,
                'ratios': company_wide_ratios,
                'target_vs_actual': {
                    'construction_variance': company_wide_ratios['construction_ratio'] - company_wide_ratios['target_construction'],
                    'events_variance': company_wide_ratios['event_ratio'] - company_wide_ratios['target_events']
                }
            },
            'strategic_recommendations': recommendations,
            'minnesota_context': {
                'market_factors': [
                    'Lake Minnetonka events (Wayzata focus)',
                    'Industrial corridor construction (Fridley focus)',
                    'Rural/agricultural support (Elk River focus)',
                    'Metro diversity (Brooklyn Park balanced)'
                ],
                'seasonal_considerations': [
                    'Spring construction startup (March-May)',
                    'Summer event peak (June-August)',
                    'Fall completion rush (September-November)',
                    'Winter indoor focus (December-February)'
                ]
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error comparing stores: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@equipment_categorization_bp.route('/settings/business-ratios', methods=['GET', 'POST'])
def manage_business_ratios():
    """
    Get or update target business ratios for A1 Rent It vs Broadway Tent & Event
    
    POST JSON:
    {
        "target_construction_ratio": 0.70,
        "target_events_ratio": 0.30,
        "store_specific_targets": {
            "3607": {"construction": 0.50, "events": 0.50},
            "728": {"construction": 0.80, "events": 0.20}
        }
    }
    """
    try:
        if request.method == 'GET':
            # Return current default ratios
            return jsonify({
                'status': 'success',
                'current_ratios': {
                    'target_construction_ratio': 0.70,
                    'target_events_ratio': 0.30,
                    'company_focus': 'A1 Rent It (Construction) - 70%, Broadway Tent & Event - 30%'
                },
                'store_recommendations': {
                    '3607': {'name': 'Wayzata', 'suggested_construction': 0.50, 'suggested_events': 0.50, 'rationale': 'Lake Minnetonka event market'},
                    '6800': {'name': 'Brooklyn Park', 'suggested_construction': 0.70, 'suggested_events': 0.30, 'rationale': 'Balanced metro market'},
                    '728': {'name': 'Fridley', 'suggested_construction': 0.80, 'suggested_events': 0.20, 'rationale': 'Industrial corridor construction'},
                    '8101': {'name': 'Elk River', 'suggested_construction': 0.65, 'suggested_events': 0.35, 'rationale': 'Rural events and agricultural'}
                },
                'timestamp': datetime.now().isoformat()
            })
        
        else:  # POST - update ratios
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided', 'status': 'error'}), 400
            
            # Validate ratios
            construction_ratio = data.get('target_construction_ratio', 0.70)
            events_ratio = data.get('target_events_ratio', 0.30)
            
            if abs(construction_ratio + events_ratio - 1.0) > 0.01:
                return jsonify({
                    'error': 'Construction and events ratios must sum to 1.0',
                    'status': 'error'
                }), 400
            
            # Store the updated ratios (in a real implementation, this would go to database)
            updated_settings = {
                'target_construction_ratio': construction_ratio,
                'target_events_ratio': events_ratio,
                'store_specific_targets': data.get('store_specific_targets', {}),
                'updated_at': datetime.now().isoformat(),
                'updated_by': 'system'  # In real implementation, get from auth
            }
            
            return jsonify({
                'status': 'success',
                'message': 'Business ratio targets updated successfully',
                'updated_settings': updated_settings,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error managing business ratios: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@equipment_categorization_bp.route('/export/categorization-report', methods=['GET'])
def export_categorization_report():
    """
    Export comprehensive categorization report for all equipment
    
    Query parameters:
    - format: json (default), csv
    - store_code: Optional filter for specific store
    """
    try:
        export_format = request.args.get('format', 'json').lower()
        store_code = request.args.get('store_code')
        
        categorization_service = EquipmentCategorizationService()
        
        # Get comprehensive analysis
        if store_code:
            analysis = categorization_service.analyze_inventory_mix(store_code=store_code)
        else:
            # Get all stores
            all_stores_analysis = {}
            for store in ['3607', '6800', '728', '8101']:
                all_stores_analysis[store] = categorization_service.analyze_inventory_mix(store_code=store)
            analysis = all_stores_analysis
        
        report_data = {
            'report_title': 'Equipment Categorization Analysis Report',
            'generated_at': datetime.now().isoformat(),
            'business_context': {
                'company': 'Minnesota Equipment Rental',
                'business_lines': {
                    'A1_RentIt': 'Construction equipment (Target: 70%)',
                    'Broadway_TentEvent': 'Event equipment (Target: 30%)'
                },
                'stores': {
                    '3607': 'Wayzata (Lake Minnetonka events)',
                    '6800': 'Brooklyn Park (Mixed market)',
                    '728': 'Fridley (Industrial construction)',
                    '8101': 'Elk River (Rural/agricultural)'
                }
            },
            'analysis': analysis,
            'minnesota_seasonal_factors': {
                'spring': 'Construction season startup, equipment prep',
                'summer': 'Peak event season, continued construction',
                'fall': 'Project completion rush, harvest events',
                'winter': 'Indoor focus, holiday events, maintenance'
            }
        }
        
        if export_format == 'csv':
            # For CSV, we'd need to flatten the data structure
            # For now, return JSON with CSV export instructions
            return jsonify({
                'status': 'success',
                'message': 'CSV export format not yet implemented',
                'suggestion': 'Use JSON format and convert client-side',
                'report_data': report_data
            })
        else:
            return jsonify({
                'status': 'success',
                'report': report_data,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error exporting categorization report: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@equipment_categorization_bp.route('/health', methods=['GET'])
def categorization_health_check():
    """Health check endpoint for categorization service"""
    try:
        categorization_service = EquipmentCategorizationService()
        
        # Test categorization with sample data
        test_result = categorization_service.categorize_equipment_item(
            common_name="Test Mini Excavator",
            pos_category="Construction"
        )
        
        return jsonify({
            'status': 'healthy',
            'service': 'Equipment Categorization Service',
            'test_categorization': test_result,
            'minnesota_stores': ['3607-Wayzata', '6800-Brooklyn Park', '728-Fridley', '8101-Elk River'],
            'business_lines': ['A1_RentIt_Construction', 'Broadway_TentEvent'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Categorization service health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500