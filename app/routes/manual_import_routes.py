# app/routes/manual_import_routes.py
"""
Manual CSV Import Routes
Provides API endpoints for triggering manual imports from shared folders
"""

import os
import glob
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from ..services.csv_import_service import CSVImportService
from ..services.pnl_import_service import PnLImportService
from ..services.scorecard_csv_import_service import ScorecardCSVImportService
from ..services.payroll_import_service import PayrollImportService
from ..services.logger import get_logger
from config import BASE_DIR
import traceback

logger = get_logger(__name__)

manual_import_bp = Blueprint('manual_import', __name__, url_prefix='/api/import')

@manual_import_bp.route('/status')
def import_status():
    """Get status of available CSV files for import"""
    try:
        shared_folder = os.path.join(BASE_DIR, 'shared', 'POR')
        
        if not os.path.exists(shared_folder):
            return jsonify({
                "success": False,
                "error": "Shared folder not found",
                "path": shared_folder
            }), 404
        
        # Scan for available CSV files
        csv_files = glob.glob(os.path.join(shared_folder, "*.csv"))
        
        file_info = []
        for csv_file in csv_files:
            stat = os.stat(csv_file)
            file_info.append({
                "filename": os.path.basename(csv_file),
                "path": csv_file,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": determine_file_type(os.path.basename(csv_file))
            })
        
        # Sort by modification time (newest first)
        file_info.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            "success": True,
            "shared_folder": shared_folder,
            "available_files": file_info,
            "file_count": len(file_info)
        })
        
    except Exception as e:
        logger.error(f"Error getting import status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def determine_file_type(filename):
    """Determine the type of CSV file based on filename patterns"""
    filename_lower = filename.lower()
    
    if 'pl8.' in filename_lower or 'pl.' in filename_lower or ('profit' in filename_lower and 'loss' in filename_lower):
        return 'pnl'
    elif 'equip' in filename_lower or ('item' in filename_lower and 'list' in filename_lower):
        return 'equipment'
    elif 'customer' in filename_lower:
        return 'customer'
    elif ('transaction' in filename_lower or 'trans' in filename_lower) and 'item' not in filename_lower:
        return 'transaction'
    elif 'transitems' in filename_lower or ('trans' in filename_lower and 'item' in filename_lower):
        return 'transaction_items'
    elif 'payroll' in filename_lower:
        return 'payroll'
    elif 'scorecard' in filename_lower:
        return 'scorecard'
    elif 'seed' in filename_lower:
        return 'seed_data'
    else:
        return 'unknown'

@manual_import_bp.route('/trigger', methods=['POST'])
def trigger_manual_import():
    """Trigger manual import of selected CSV files"""
    try:
        data = request.get_json()
        
        if not data or 'files' not in data:
            return jsonify({
                "success": False,
                "error": "No files specified for import"
            }), 400
        
        files_to_import = data['files']
        limit = data.get('limit', 25000)  # Default limit
        
        results = {
            "success": True,
            "imports": [],
            "errors": [],
            "summary": {
                "total_files": len(files_to_import),
                "successful": 0,
                "failed": 0,
                "total_records": 0
            }
        }
        
        for file_info in files_to_import:
            filename = file_info.get('filename')
            file_type = file_info.get('type', 'unknown')
            
            if not filename:
                results["errors"].append("Missing filename in request")
                continue
                
            file_path = os.path.join(BASE_DIR, 'shared', 'POR', filename)
            
            if not os.path.exists(file_path):
                results["errors"].append(f"File not found: {filename}")
                continue
            
            logger.info(f"Starting import of {filename} (type: {file_type})")
            
            try:
                import_result = None
                
                if file_type == 'pnl':
                    # Use P&L import service
                    pnl_service = PnLImportService()
                    import_result = pnl_service.import_pnl_csv_data(file_path, limit)
                    
                elif file_type == 'scorecard':
                    # Use scorecard import service
                    scorecard_service = ScorecardCSVImportService()
                    import_result = scorecard_service.import_scorecard_csv_data(file_path, limit)

                elif file_type == 'payroll':
                    # Use payroll import service
                    payroll_service = PayrollImportService()
                    import_result = payroll_service.import_payroll_csv_data(file_path, limit)

                elif file_type in ['equipment', 'customer', 'transaction']:
                    # Use standard CSV import service
                    csv_service = CSVImportService()

                    if file_type == 'equipment':
                        import_result = csv_service.import_equipment_data(file_path)
                    elif file_type == 'customer':
                        import_result = csv_service.import_customer_data(file_path, limit)
                    elif file_type == 'transaction':
                        import_result = csv_service.import_transactions_data(file_path)
                else:
                    results["errors"].append(f"Unsupported file type: {file_type} for {filename}")
                    continue
                
                if import_result and import_result.get('success'):
                    results["imports"].append({
                        "filename": filename,
                        "type": file_type,
                        "result": import_result
                    })
                    results["summary"]["successful"] += 1
                    results["summary"]["total_records"] += import_result.get('records_imported', 0)
                else:
                    error_msg = import_result.get('error', 'Unknown import error') if import_result else 'Import failed'
                    results["errors"].append(f"Import failed for {filename}: {error_msg}")
                    results["summary"]["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Import error for {filename}: {e}")
                results["errors"].append(f"Import error for {filename}: {str(e)}")
                results["summary"]["failed"] += 1
        
        # Update overall success status
        results["success"] = results["summary"]["failed"] == 0
        
        logger.info(f"Manual import completed: {results['summary']['successful']} successful, "
                   f"{results['summary']['failed']} failed, "
                   f"{results['summary']['total_records']} total records")
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in manual import trigger: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@manual_import_bp.route('/pnl/analytics')
def get_pnl_analytics():
    """Get P&L analytics data"""
    try:
        store_code = request.args.get('store_code')
        metric_type = request.args.get('metric_type')
        
        pnl_service = PnLImportService()
        analytics = pnl_service.get_pnl_analytics(store_code, metric_type)
        
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting P&L analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@manual_import_bp.route('/dashboard')
def import_dashboard():
    """Render manual import dashboard"""
    return render_template('manual_import_dashboard.html')

# Add route for quick P&L test import
@manual_import_bp.route('/pnl/quick-test', methods=['POST'])
def quick_pnl_test():
    """Quick test import of P&L data"""
    try:
        # Look for the P&L file
        shared_folder = os.path.join(BASE_DIR, 'shared', 'POR')
        pnl_files = glob.glob(os.path.join(shared_folder, "*PL*.csv"))
        
        if not pnl_files:
            return jsonify({
                "success": False,
                "error": "No P&L CSV files found in shared folder"
            }), 404
        
        # Use the most recent P&L file
        pnl_file = max(pnl_files, key=os.path.getmtime)
        
        logger.info(f"Starting quick P&L test import from: {pnl_file}")
        
        pnl_service = PnLImportService()
        result = pnl_service.import_pnl_csv_data(pnl_file, limit=5000)  # Small test limit
        
        return jsonify({
            "success": True,
            "test_file": os.path.basename(pnl_file),
            "import_result": result
        })
        
    except Exception as e:
        logger.error(f"Quick P&L test failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500