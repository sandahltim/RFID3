# app/routes/config_management.py
"""
Editable Configuration Management Routes
Provides web interface for managing store configurations and settings
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import json
from app import db
from app.config.stores import STORES, STORE_MANAGERS, get_store_name, get_all_store_codes
from app.models.config_models import UserConfiguration, set_user_config, get_user_config

config_bp = Blueprint('config', __name__, url_prefix='/config')

@config_bp.route('/')
def config_home():
    """Configuration management home page"""
    return render_template('config/config_home.html', 
                         title='Configuration Management',
                         stores=STORES,
                         managers=STORE_MANAGERS)

@config_bp.route('/stores')
def store_config():
    """Store configuration management interface"""
    stores_data = []
    for store_code, info in STORES.items():
        stores_data.append({
            'store_code': store_code,
            'name': info.name,
            'location': info.location,
            'pos_code': info.pos_code,
            'manager': info.manager,
            'business_type': info.business_type,
            'opened_date': info.opened_date,
            'emoji': info.emoji,
            'approximate_items': info.approximate_items,
            'active': info.active,
            'editable': store_code != '000'  # Legacy store not editable
        })
    
    return render_template('config/store_management.html',
                         title='Store Configuration',
                         stores=stores_data)

@config_bp.route('/stores/<store_code>')
def edit_store(store_code):
    """Edit individual store configuration"""
    if store_code not in STORES:
        flash(f'Store {store_code} not found', 'error')
        return redirect(url_for('config.store_config'))
    
    store_info = STORES[store_code]
    return render_template('config/edit_store.html',
                         title=f'Edit {store_info.name} Configuration',
                         store_code=store_code,
                         store_info=store_info)

@config_bp.route('/api/stores/<store_code>', methods=['PUT'])
def update_store_config(store_code):
    """API endpoint to update store configuration"""
    try:
        if store_code not in STORES:
            return jsonify({'success': False, 'error': 'Store not found'}), 404
            
        if store_code == '000':
            return jsonify({'success': False, 'error': 'Legacy store not editable'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'location', 'manager', 'business_type']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Prepare updated configuration
        updated_config = {
            'store_code': store_code,
            'name': data['name'].strip(),
            'location': data['location'].strip(),
            'pos_code': STORES[store_code].pos_code,  # POS code not editable
            'manager': data['manager'].strip().upper(),
            'business_type': data['business_type'].strip(),
            'emoji': data.get('emoji', STORES[store_code].emoji),
            'approximate_items': data.get('approximate_items', STORES[store_code].approximate_items),
            'opened_date': STORES[store_code].opened_date,  # Opening date not editable
            'active': data.get('active', True),
            'updated_at': datetime.now().isoformat(),
            'updated_by': 'config_management'
        }
        
        # Save to database configuration
        set_user_config('default_user', 'store_config', store_code, updated_config)
        
        # Log the change
        audit_entry = {
            'action': 'store_config_update',
            'store_code': store_code,
            'changes': data,
            'timestamp': datetime.now().isoformat(),
            'user': 'config_management'
        }
        
        # Save audit trail
        set_user_config('default_user', 'audit', f'store_update_{store_code}_{datetime.now().strftime("%Y%m%d_%H%M%S")}', audit_entry)
        
        return jsonify({
            'success': True,
            'message': f'Store {store_code} configuration updated successfully',
            'store_name': updated_config['name']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/managers')
def manager_config():
    """Manager assignment configuration"""
    manager_data = []
    
    for store_code, info in STORES.items():
        if info.active:  # Only show active stores
            manager_data.append({
                'store_code': store_code,
                'store_name': info.name,
                'location': info.location,
                'current_manager': info.manager,
                'business_type': info.business_type,
                'pos_code': info.pos_code,
                'opened_date': info.opened_date
            })
    
    # Get historical manager changes if any
    manager_history = get_user_config('default_user', 'manager_history', 'all') or {}
    
    return render_template('config/manager_assignments.html',
                         title='Manager Assignments',
                         managers=manager_data,
                         history=manager_history)

@config_bp.route('/api/managers/<store_code>', methods=['PUT'])
def update_manager_assignment(store_code):
    """API endpoint to update manager assignment"""
    try:
        if store_code not in STORES:
            return jsonify({'success': False, 'error': 'Store not found'}), 404
        
        data = request.get_json()
        new_manager = data.get('manager', '').strip().upper()
        
        if not new_manager:
            return jsonify({'success': False, 'error': 'Manager name is required'}), 400
        
        old_manager = STORES[store_code].manager
        
        # Create manager change record
        change_record = {
            'store_code': store_code,
            'store_name': STORES[store_code].name,
            'old_manager': old_manager,
            'new_manager': new_manager,
            'changed_at': datetime.now().isoformat(),
            'changed_by': 'config_management'
        }
        
        # Save the change
        set_user_config('default_user', 'manager_assignment', store_code, {
            'manager': new_manager,
            'previous_manager': old_manager,
            'updated_at': datetime.now().isoformat()
        })
        
        # Update manager history
        manager_history = get_user_config('default_user', 'manager_history', 'all') or {}
        if store_code not in manager_history:
            manager_history[store_code] = []
        
        manager_history[store_code].append(change_record)
        set_user_config('default_user', 'manager_history', 'all', manager_history)
        
        return jsonify({
            'success': True,
            'message': f'Manager for {STORES[store_code].name} changed from {old_manager} to {new_manager}',
            'store_name': STORES[store_code].name,
            'old_manager': old_manager,
            'new_manager': new_manager
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/api/stores')
def get_stores_api():
    """API endpoint to get all store configurations"""
    try:
        stores_data = []
        
        for store_code, info in STORES.items():
            # Check for any database overrides
            db_config = get_user_config('default_user', 'store_config', store_code)
            manager_config = get_user_config('default_user', 'manager_assignment', store_code)
            
            store_data = {
                'store_code': store_code,
                'name': db_config['name'] if db_config else info.name,
                'location': db_config['location'] if db_config else info.location,
                'pos_code': info.pos_code,
                'manager': manager_config['manager'] if manager_config else info.manager,
                'business_type': db_config['business_type'] if db_config else info.business_type,
                'opened_date': info.opened_date,
                'emoji': info.emoji,
                'approximate_items': info.approximate_items,
                'active': db_config['active'] if db_config else info.active,
                'has_overrides': bool(db_config or manager_config)
            }
            stores_data.append(store_data)
        
        return jsonify({'success': True, 'stores': stores_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/api/managers')
def get_managers_api():
    """API endpoint to get all manager assignments"""
    try:
        managers_data = {}
        
        for store_code, info in STORES.items():
            if info.active:
                # Check for database override
                manager_config = get_user_config('default_user', 'manager_assignment', store_code)
                current_manager = manager_config['manager'] if manager_config else info.manager
                
                managers_data[store_code] = {
                    'store_name': info.name,
                    'current_manager': current_manager,
                    'default_manager': info.manager,
                    'has_override': bool(manager_config)
                }
        
        return jsonify({'success': True, 'managers': managers_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@config_bp.route('/reset/<config_type>/<store_code>', methods=['POST'])
def reset_store_config(config_type, store_code):
    """Reset store configuration to default"""
    try:
        if store_code not in STORES:
            return jsonify({'success': False, 'error': 'Store not found'}), 404
        
        valid_types = ['store_config', 'manager_assignment', 'all']
        if config_type not in valid_types:
            return jsonify({'success': False, 'error': 'Invalid config type'}), 400
        
        # Remove database overrides
        if config_type in ['store_config', 'all']:
            # Remove store config override
            config = UserConfiguration.query.filter_by(
                user_id='default_user',
                config_type='store_config',
                config_name=store_code
            ).first()
            if config:
                db.session.delete(config)
        
        if config_type in ['manager_assignment', 'all']:
            # Remove manager assignment override
            config = UserConfiguration.query.filter_by(
                user_id='default_user',
                config_type='manager_assignment',
                config_name=store_code
            ).first()
            if config:
                db.session.delete(config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Configuration reset to default for store {store_code}',
            'store_name': STORES[store_code].name
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500