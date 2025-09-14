"""
Database Viewer Tab - Data Verification and Column Reference Tool
Allows users to browse database tables, verify data imports, and explore column relationships.
"""

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import inspect, text, func, create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime
import mysql.connector

from ..models.db_models import (
    db, ItemMaster, Transaction, RFIDTag, SeedRentalClass, InventoryHealthAlert,
    RentalClassMapping, HandCountedItems, RefreshState, InventoryConfig
)
from ..models.pos_models import POSEquipment, POSTransaction, POSRFIDCorrelation
from ..models.financial_models import PayrollTrendsData, ScorecardTrendsData
from ..models.db_models import PLData
# Removed unused import: from ..utils.filters import apply_global_filters

# Configure logging
logger = logging.getLogger(__name__)

database_viewer_bp = Blueprint('database_viewer', __name__)

# Database connections - RFID Project databases only
AVAILABLE_DATABASES = {
    'rfid_inventory': {
        'name': 'RFID Inventory (Primary)',
        'description': 'Main RFID Dashboard Project database with live data',
        'connection_params': {
            'host': 'localhost',
            'user': 'root',
            'password': 'Broadway8101',
            'database': 'rfid_inventory'
        }
    },
    'rfidpro': {
        'name': 'RFID Pro (Scanner Fallback)',
        'description': 'Fallback database for RFID scanner operations',
        'connection_params': {
            'host': 'localhost',
            'user': 'root',
            'password': 'Broadway8101',
            'database': 'rfidpro'
        }
    }
}

# Available tables for viewing (RFID databases)
AVAILABLE_TABLES = {
    'item_master': {
        'model': ItemMaster,
        'display_name': 'Item Master',
        'description': 'Main inventory items table with specifications and status',
        'key_columns': ['tag_id', 'common_name', 'category', 'subcategory', 'current_store', 'status']
    },
    'transactions': {
        'model': Transaction,
        'display_name': 'Transactions',
        'description': 'RFID scan transactions and item movements',
        'key_columns': ['tag_id', 'scan_date', 'location', 'user_name', 'transaction_type']
    },
    'rfid_tags': {
        'model': RFIDTag,
        'display_name': 'RFID Tags',
        'description': 'RFID tag information and metadata',
        'key_columns': ['tag_id', 'common_name', 'category', 'subcategory']
    },
    'seed_rental_class': {
        'model': SeedRentalClass,
        'display_name': 'Seed Rental Classes',
        'description': 'Rental classification seed data',
        'key_columns': ['rental_class_num', 'description']
    },
    'rental_class_mapping': {
        'model': RentalClassMapping,
        'display_name': 'Rental Class Mapping',
        'description': 'Mapping between rental classes and items',
        'key_columns': ['tag_id', 'rental_class_num']
    },
    'hand_counted_items': {
        'model': HandCountedItems,
        'display_name': 'Hand Counted Items',
        'description': 'Manually counted inventory items',
        'key_columns': ['tag_id', 'count_date', 'counted_by']
    },
    'inventory_health_alerts': {
        'model': InventoryHealthAlert,
        'display_name': 'Health Alerts',
        'description': 'Inventory health monitoring alerts and notifications',
        'key_columns': ['tag_id', 'alert_type', 'severity', 'status', 'created_at']
    },
    'refresh_state': {
        'model': RefreshState,
        'display_name': 'Refresh State',
        'description': 'Data refresh and synchronization state tracking',
        'key_columns': ['refresh_type', 'last_refresh', 'status']
    },
    'inventory_config': {
        'model': InventoryConfig,
        'display_name': 'Inventory Configuration',
        'description': 'System configuration settings for inventory management',
        'key_columns': ['config_key', 'config_value', 'updated_at']
    },
    # POS System Tables
    'pos_equipment': {
        'model': POSEquipment,
        'display_name': 'POS Equipment',
        'description': 'Point-of-sale equipment and inventory data',
        'key_columns': ['item_num', 'name', 'part_no', 'serial_no', 'current_cost', 'status']
    },
    'pos_transactions': {
        'model': POSTransaction,
        'display_name': 'POS Transactions',
        'description': 'Point-of-sale transaction records',
        'key_columns': ['transaction_num', 'invoice_num', 'customer_id', 'transaction_date', 'total_amount']
    },
    'pos_rfid_correlation': {
        'model': POSRFIDCorrelation,
        'display_name': 'POS-RFID Correlation',
        'description': 'Correlation between POS items and RFID tags',
        'key_columns': ['pos_item_num', 'rfid_tag_id', 'correlation_confidence', 'created_at']
    },
    # Financial Data Tables
    'pl_data': {
        'model': PLData,
        'display_name': 'P&L Data',
        'description': 'Profit & Loss financial data by account and period',
        'key_columns': ['account_code', 'account_name', 'period_month', 'period_year', 'amount', 'category']
    },
    'payroll_trends_data': {
        'model': PayrollTrendsData,
        'display_name': 'Payroll Trends',
        'description': 'Weekly payroll trends by location',
        'key_columns': ['week_ending', 'location_code', 'rental_revenue', 'payroll_amount', 'wage_hours']
    },
    'scorecard_trends_data': {
        'model': ScorecardTrendsData,
        'display_name': 'Scorecard Trends',
        'description': 'Weekly business scorecard metrics and KPIs',
        'key_columns': ['week_ending', 'total_weekly_revenue', 'revenue_3607', 'revenue_6800', 'revenue_8101', 'total_discount']
    }
}

@database_viewer_bp.route('/database/viewer')
def database_viewer():
    """Main database viewer page."""
    return render_template('database_viewer.html', tables=AVAILABLE_TABLES, databases=AVAILABLE_DATABASES)

@database_viewer_bp.route('/api/database/tables')
def get_tables():
    """Get list of available database tables with metadata."""
    try:
        session = db.session
        inspector = inspect(db.engine)
        
        tables_info = {}
        for table_key, table_info in AVAILABLE_TABLES.items():
            model = table_info['model']
            
            # Get table schema information
            if hasattr(model, '__tablename__'):
                table_name = model.__tablename__
                
                # Get column information
                columns = inspector.get_columns(table_name)
                
                # Convert columns to serializable format
                serializable_columns = []
                for col in columns:
                    col_info = {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col.get('nullable', True),
                        'default': str(col.get('default')) if col.get('default') is not None else None
                    }
                    serializable_columns.append(col_info)
                
                # Get row count
                try:
                    row_count = session.query(model).count()
                except Exception as e:
                    logger.warning(f"Could not get row count for {table_name}: {e}")
                    row_count = 0
                
                # Create serializable table info (exclude model)
                serializable_table_info = {
                    'display_name': table_info['display_name'],
                    'description': table_info['description'],
                    'key_columns': table_info['key_columns']
                }
                
                tables_info[table_key] = {
                    **serializable_table_info,
                    'table_name': table_name,
                    'columns': serializable_columns,
                    'row_count': row_count
                }
        
        return jsonify({
            'status': 'success',
            'tables': tables_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting table information: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/table/<table_key>/data')
def get_table_data(table_key):
    """Get data from a specific table with pagination and filtering."""
    if table_key not in AVAILABLE_TABLES:
        return jsonify({'status': 'error', 'error': 'Table not found'}), 404
    
    try:
        session = db.session
        table_info = AVAILABLE_TABLES[table_key]
        model = table_info['model']
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 500)  # Max 500 rows
        
        # Get search/filter parameters
        search = request.args.get('search', '').strip()
        column_filter = request.args.get('column', '')
        
        # Build base query
        query = session.query(model)
        
        # Apply global store/type filters if applicable
        if hasattr(model, 'current_store') or hasattr(model, 'home_store'):
            store_filter = request.args.get('store', 'all')
            type_filter = request.args.get('type', 'all')
            
            # Apply filters manually to avoid request.args conversion issues
            if store_filter and store_filter != 'all':
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        model.home_store == store_filter,
                        model.current_store == store_filter,
                    )
                )
            if type_filter and type_filter != 'all' and hasattr(model, 'identifier_type'):
                if type_filter == 'RFID':
                    # RFID items are those with NULL identifier_type and HEX EPC format
                    from sqlalchemy import and_
                    query = query.filter(
                        and_(
                            model.identifier_type == 'None',
                            model.tag_id.op('REGEXP')('^[0-9A-Fa-f]{16,}$')
                        )
                    )
                elif type_filter == 'Serialized':
                    # Serialized items are QR + Stickers
                    query = query.filter(model.identifier_type.in_(['QR', 'Sticker']))
                else:
                    query = query.filter(model.identifier_type == type_filter)
        
        # Apply search filter
        if search and column_filter:
            # Search in specific column
            if hasattr(model, column_filter):
                column = getattr(model, column_filter)
                query = query.filter(column.ilike(f'%{search}%'))
        elif search:
            # Search across key columns
            search_conditions = []
            for col_name in table_info['key_columns']:
                if hasattr(model, col_name):
                    column = getattr(model, col_name)
                    search_conditions.append(column.ilike(f'%{search}%'))
            
            if search_conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*search_conditions))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        # Convert to dictionaries
        data = []
        for item in items:
            item_dict = {}
            for column in inspect(model).columns:
                value = getattr(item, column.name)
                # Convert datetime objects to strings
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif value is None:
                    value = None
                else:
                    # Convert other non-serializable types to string
                    try:
                        import json
                        json.dumps(value)  # Test if serializable
                    except (TypeError, ValueError):
                        value = str(value)
                item_dict[column.name] = value
            data.append(item_dict)
        
        return jsonify({
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page,
                'has_next': (page * per_page) < total_count,
                'has_prev': page > 1
            },
            'table_info': {
                'name': table_info['display_name'],
                'description': table_info['description'],
                'key_columns': table_info['key_columns']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting table data for {table_key}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/table/<table_key>/schema')
def get_table_schema(table_key):
    """Get detailed schema information for a specific table."""
    if table_key not in AVAILABLE_TABLES:
        return jsonify({'status': 'error', 'error': 'Table not found'}), 404
    
    try:
        session = db.session
        table_info = AVAILABLE_TABLES[table_key]
        model = table_info['model']
        
        if not hasattr(model, '__tablename__'):
            return jsonify({'status': 'error', 'error': 'Table not found'}), 404
        
        inspector = inspect(db.engine)
        table_name = model.__tablename__
        
        # Get detailed column information
        columns = inspector.get_columns(table_name)
        
        # Get foreign key relationships
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        # Get indexes
        indexes = inspector.get_indexes(table_name)
        
        # Get primary keys
        primary_keys = inspector.get_primary_keys(table_name)
        
        return jsonify({
            'status': 'success',
            'schema': {
                'table_name': table_name,
                'display_name': table_info['display_name'],
                'description': table_info['description'],
                'columns': columns,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'primary_keys': primary_keys,
                'key_columns': table_info['key_columns']
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting table schema for {table_key}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/table/<table_key>/stats')
def get_table_stats(table_key):
    """Get statistical information about a table's data."""
    if table_key not in AVAILABLE_TABLES:
        return jsonify({'status': 'error', 'error': 'Table not found'}), 404
    
    try:
        session = db.session
        table_info = AVAILABLE_TABLES[table_key]
        model = table_info['model']
        
        stats = {
            'total_rows': session.query(model).count()
        }
        
        # Get statistics for key columns
        column_stats = {}
        for col_name in table_info['key_columns']:
            if hasattr(model, col_name):
                column = getattr(model, col_name)
                
                # Count non-null values
                non_null_count = session.query(func.count(column)).filter(column.is_not(None)).scalar()
                
                # Get distinct count
                distinct_count = session.query(func.count(func.distinct(column))).scalar()
                
                column_stats[col_name] = {
                    'non_null_count': non_null_count,
                    'distinct_count': distinct_count,
                    'null_count': stats['total_rows'] - non_null_count
                }
                
                # For string columns, get top values
                if hasattr(column.type, 'python_type') and column.type.python_type == str:
                    try:
                        top_values = (session.query(column, func.count(column).label('count'))
                                    .filter(column.is_not(None))
                                    .group_by(column)
                                    .order_by(func.count(column).desc())
                                    .limit(10)
                                    .all())
                        column_stats[col_name]['top_values'] = [
                            {'value': value, 'count': count} for value, count in top_values
                        ]
                    except Exception as e:
                        logger.warning(f"Could not get top values for {col_name}: {e}")
        
        return jsonify({
            'status': 'success',
            'stats': stats,
            'column_stats': column_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting table stats for {table_key}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/list')
def get_databases():
    """Get list of available databases."""
    try:
        return jsonify({
            'status': 'success',
            'databases': AVAILABLE_DATABASES,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting database list: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/<db_key>/tables')
def get_database_tables(db_key):
    """Get all tables from a specific database with raw discovery."""
    if db_key not in AVAILABLE_DATABASES:
        return jsonify({'status': 'error', 'error': 'Database not found'}), 404

    try:
        db_config = AVAILABLE_DATABASES[db_key]['connection_params']

        # Create connection to the specified database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Get all tables in database
        cursor.execute("SHOW TABLES")
        raw_tables = cursor.fetchall()

        tables_info = {}
        for (table_name,) in raw_tables:
            try:
                # Get table row count
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                row_count = cursor.fetchone()[0]

                # Get table structure
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()

                # Convert column info
                serializable_columns = []
                for col in columns:
                    col_info = {
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2] == 'YES',
                        'key': col[3],
                        'default': col[4],
                        'extra': col[5]
                    }
                    serializable_columns.append(col_info)

                tables_info[table_name] = {
                    'display_name': table_name.replace('_', ' ').title(),
                    'description': f'Database table from {db_config["database"]}',
                    'table_name': table_name,
                    'columns': serializable_columns,
                    'row_count': row_count,
                    'database': db_config["database"]
                }

            except Exception as table_error:
                logger.warning(f"Could not analyze table {table_name}: {table_error}")
                tables_info[table_name] = {
                    'display_name': table_name,
                    'description': 'Could not analyze table structure',
                    'table_name': table_name,
                    'columns': [],
                    'row_count': 0,
                    'database': db_config["database"],
                    'error': str(table_error)
                }

        cursor.close()
        connection.close()

        return jsonify({
            'status': 'success',
            'database': AVAILABLE_DATABASES[db_key]['name'],
            'tables': tables_info,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting tables for database {db_key}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/<db_key>/table/<table_name>/data')
def get_raw_table_data(db_key, table_name):
    """Get data from any table in any database using raw SQL."""
    if db_key not in AVAILABLE_DATABASES:
        return jsonify({'status': 'error', 'error': 'Database not found'}), 404

    try:
        db_config = AVAILABLE_DATABASES[db_key]['connection_params']

        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 50)), 500)
        search = request.args.get('search', '').strip()
        column_filter = request.args.get('column', '')

        # Create connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Build base query
        base_query = f"SELECT * FROM `{table_name}`"
        count_query = f"SELECT COUNT(*) as total FROM `{table_name}`"

        # Build WHERE clause for search
        where_conditions = []
        params = []

        if search:
            if column_filter:
                # Search in specific column
                where_conditions.append(f"`{column_filter}` LIKE %s")
                params.append(f'%{search}%')
            else:
                # Get column names first
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = [col['Field'] for col in cursor.fetchall()]

                # Search across all text-like columns
                search_conditions = []
                for col in columns:
                    search_conditions.append(f"`{col}` LIKE %s")
                    params.append(f'%{search}%')

                if search_conditions:
                    where_conditions.append(f"({' OR '.join(search_conditions)})")

        # Apply WHERE clause if we have conditions
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)
            base_query += where_clause
            count_query += where_clause

        # Get total count
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']

        # Apply pagination
        offset = (page - 1) * per_page
        paginated_query = f"{base_query} LIMIT %s OFFSET %s"
        pagination_params = params + [per_page, offset]

        # Execute paginated query
        cursor.execute(paginated_query, pagination_params)
        data = cursor.fetchall()

        # Convert datetime objects to strings
        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.isoformat()
                elif value is None:
                    row[key] = None
                else:
                    # Ensure JSON serializable
                    try:
                        import json
                        json.dumps(value)
                    except (TypeError, ValueError):
                        row[key] = str(value)

        cursor.close()
        connection.close()

        return jsonify({
            'status': 'success',
            'data': data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page,
                'has_next': (page * per_page) < total_count,
                'has_prev': page > 1
            },
            'table_info': {
                'name': table_name.replace('_', ' ').title(),
                'description': f'Raw table data from {db_config["database"]}.{table_name}',
                'database': db_config["database"]
            },
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting table data for {db_key}.{table_name}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

logger.info(f"Deployed database_viewer.py version: 2025-09-14-v2-multi-db at {datetime.now()}")