"""
Database Query Tool for Minnesota Equipment Rental AI Agent
Provides secure, read-only access to MariaDB with natural language query capabilities
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.exc import SQLAlchemyError
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import re
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Structured result from database query"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    execution_time_ms: int = 0
    query: Optional[str] = None
    error: Optional[str] = None
    columns: Optional[List[str]] = None


class DatabaseQueryInput(BaseModel):
    """Input schema for database queries"""
    query_type: str = Field(
        description="Type of query: 'natural_language', 'sql', 'predefined'"
    )
    question: Optional[str] = Field(
        description="Natural language business question"
    )
    sql_query: Optional[str] = Field(
        description="Direct SQL query (read-only operations only)"
    )
    predefined_query: Optional[str] = Field(
        description="Name of predefined query template"
    )
    parameters: Dict[str, Any] = Field(
        default={}, description="Query parameters for predefined queries"
    )
    limit: int = Field(default=100, description="Maximum number of rows to return")


class DatabaseQueryTool(BaseTool):
    """
    LangChain tool for querying the Minnesota Equipment Rental database
    Supports natural language to SQL conversion and predefined business queries
    """
    
    name = "database_query"
    description = """
    Query the equipment rental database to answer business questions.
    
    Supports:
    - Inventory status and availability
    - Financial performance analysis  
    - Equipment utilization trends
    - Customer rental patterns
    - Store performance comparisons
    - Revenue and profitability insights
    
    Use this tool for questions about:
    - "What equipment is currently on rent?"
    - "Which items generate the most revenue?"
    - "What's the utilization rate for excavators?"
    - "How many items are in each store?"
    - "What are the top renting categories?"
    """
    
    def __init__(self, connection_string: str, **kwargs):
        super().__init__(**kwargs)
        self.connection_string = connection_string
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        self.metadata = MetaData()
        self.inspector = inspect(self.engine)
        self._load_schema_info()
        self._setup_predefined_queries()
    
    def _load_schema_info(self) -> None:
        """Load database schema information for query generation"""
        try:
            self.tables = self.inspector.get_table_names()
            self.schema_info = {}
            
            # Key tables for equipment rental business
            key_tables = [
                'id_item_master',
                'pos_transactions', 
                'pos_equipment',
                'pos_rfid_correlation'
            ]
            
            for table_name in key_tables:
                if table_name in self.tables:
                    columns = self.inspector.get_columns(table_name)
                    self.schema_info[table_name] = {
                        'columns': [col['name'] for col in columns],
                        'column_info': columns
                    }
            
            logger.info(f"Loaded schema info for {len(self.schema_info)} tables")
            
        except Exception as e:
            logger.error(f"Failed to load schema info: {e}")
            self.schema_info = {}
    
    def _setup_predefined_queries(self) -> None:
        """Setup predefined business intelligence queries"""
        self.predefined_queries = {
            'inventory_summary': {
                'sql': """
                SELECT 
                    status,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                FROM id_item_master 
                GROUP BY status 
                ORDER BY count DESC
                """,
                'description': 'Overall inventory status summary'
            },
            
            'revenue_by_category': {
                'sql': """
                SELECT 
                    rental_class_num,
                    common_name,
                    COUNT(*) as item_count,
                    COALESCE(SUM(turnover_ytd), 0) as ytd_revenue,
                    COALESCE(SUM(turnover_ltd), 0) as lifetime_revenue,
                    COALESCE(AVG(sell_price), 0) as avg_sell_price
                FROM id_item_master 
                WHERE rental_class_num IS NOT NULL
                GROUP BY rental_class_num, common_name
                HAVING COUNT(*) > 1
                ORDER BY ytd_revenue DESC
                LIMIT {limit}
                """,
                'description': 'Revenue analysis by equipment category'
            },
            
            'store_performance': {
                'sql': """
                SELECT 
                    COALESCE(current_store, 'Unknown') as store,
                    COUNT(*) as total_items,
                    SUM(CASE WHEN status IN ('On Rent', 'Delivered') THEN 1 ELSE 0 END) as items_on_rent,
                    ROUND(
                        SUM(CASE WHEN status IN ('On Rent', 'Delivered') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
                    ) as utilization_rate,
                    COALESCE(SUM(turnover_ytd), 0) as ytd_revenue
                FROM id_item_master
                GROUP BY current_store
                ORDER BY ytd_revenue DESC
                """,
                'description': 'Performance comparison across stores'
            },
            
            'high_value_items': {
                'sql': """
                SELECT 
                    tag_id,
                    common_name,
                    rental_class_num,
                    status,
                    COALESCE(sell_price, 0) as sell_price,
                    COALESCE(turnover_ytd, 0) as ytd_revenue,
                    COALESCE(repair_cost_ltd, 0) as lifetime_repair_cost,
                    current_store
                FROM id_item_master
                WHERE sell_price > {min_price}
                ORDER BY sell_price DESC
                LIMIT {limit}
                """,
                'description': 'High-value equipment analysis'
            },
            
            'recent_activity': {
                'sql': """
                SELECT 
                    tag_id,
                    common_name,
                    status,
                    date_last_scanned,
                    last_contract_num,
                    client_name,
                    current_store
                FROM id_item_master
                WHERE date_last_scanned >= DATE_SUB(NOW(), INTERVAL {days} DAY)
                ORDER BY date_last_scanned DESC
                LIMIT {limit}
                """,
                'description': 'Recent equipment activity'
            },
            
            'maintenance_needed': {
                'sql': """
                SELECT 
                    tag_id,
                    common_name,
                    status,
                    quality,
                    COALESCE(repair_cost_ltd, 0) as lifetime_repair_cost,
                    date_last_scanned,
                    status_notes
                FROM id_item_master
                WHERE status IN ('Needs to be Inspected', 'Repair', 'Wet')
                ORDER BY 
                    CASE 
                        WHEN status = 'Repair' THEN 1
                        WHEN status = 'Needs to be Inspected' THEN 2
                        ELSE 3
                    END,
                    date_last_scanned ASC
                LIMIT {limit}
                """,
                'description': 'Equipment requiring maintenance attention'
            },
            
            'profitability_analysis': {
                'sql': """
                SELECT 
                    rental_class_num,
                    common_name,
                    COUNT(*) as item_count,
                    COALESCE(SUM(turnover_ytd), 0) as ytd_revenue,
                    COALESCE(SUM(repair_cost_ltd), 0) as lifetime_repair_cost,
                    COALESCE(SUM(turnover_ytd) - SUM(repair_cost_ltd), 0) as net_profit_estimate,
                    CASE 
                        WHEN SUM(repair_cost_ltd) > 0 THEN
                            ROUND((SUM(turnover_ytd) - SUM(repair_cost_ltd)) / SUM(repair_cost_ltd) * 100, 2)
                        ELSE NULL
                    END as roi_percentage
                FROM id_item_master
                WHERE rental_class_num IS NOT NULL
                GROUP BY rental_class_num, common_name
                HAVING COUNT(*) > 2 AND SUM(turnover_ytd) > 0
                ORDER BY net_profit_estimate DESC
                LIMIT {limit}
                """,
                'description': 'Equipment profitability and ROI analysis'
            }
        }
    
    def _run(self, query_input: str) -> str:
        """Execute database query based on input parameters"""
        try:
            # Parse input if it's JSON string
            if isinstance(query_input, str):
                try:
                    input_data = json.loads(query_input)
                except json.JSONDecodeError:
                    # Treat as natural language question
                    input_data = {
                        'query_type': 'natural_language',
                        'question': query_input
                    }
            else:
                input_data = query_input
            
            # Validate input
            query_params = DatabaseQueryInput(**input_data)
            
            # Route to appropriate query method
            if query_params.query_type == 'predefined':
                result = self._execute_predefined_query(
                    query_params.predefined_query,
                    query_params.parameters,
                    query_params.limit
                )
            elif query_params.query_type == 'sql':
                result = self._execute_sql_query(
                    query_params.sql_query,
                    query_params.limit
                )
            else:  # natural_language
                result = self._execute_natural_language_query(
                    query_params.question,
                    query_params.limit
                )
            
            return self._format_result(result)
            
        except Exception as e:
            logger.error(f"Database query error: {e}", exc_info=True)
            return json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def _execute_predefined_query(
        self, 
        query_name: str, 
        parameters: Dict[str, Any], 
        limit: int
    ) -> QueryResult:
        """Execute a predefined business query"""
        if query_name not in self.predefined_queries:
            return QueryResult(
                success=False,
                error=f"Unknown predefined query: {query_name}"
            )
        
        query_template = self.predefined_queries[query_name]['sql']
        
        # Set default parameters
        params = {
            'limit': limit,
            'days': parameters.get('days', 7),
            'min_price': parameters.get('min_price', 1000),
            **parameters
        }
        
        # Format the query with parameters
        try:
            formatted_query = query_template.format(**params)
            return self._execute_raw_sql(formatted_query)
        except KeyError as e:
            return QueryResult(
                success=False,
                error=f"Missing required parameter: {e}"
            )
    
    def _execute_sql_query(self, sql_query: str, limit: int) -> QueryResult:
        """Execute a direct SQL query (with safety checks)"""
        if not sql_query:
            return QueryResult(success=False, error="No SQL query provided")
        
        # Security checks - only allow SELECT queries
        sql_clean = sql_query.strip().upper()
        if not sql_clean.startswith('SELECT'):
            return QueryResult(
                success=False,
                error="Only SELECT queries are allowed"
            )
        
        # Check for dangerous keywords
        dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
            'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_clean:
                return QueryResult(
                    success=False,
                    error=f"Query contains prohibited keyword: {keyword}"
                )
        
        # Add LIMIT if not present
        if 'LIMIT' not in sql_clean:
            sql_query = f"{sql_query.rstrip(';')} LIMIT {limit}"
        
        return self._execute_raw_sql(sql_query)
    
    def _execute_natural_language_query(self, question: str, limit: int) -> QueryResult:
        """Convert natural language question to SQL and execute"""
        if not question:
            return QueryResult(success=False, error="No question provided")
        
        # Simple natural language to SQL conversion
        # In production, this would use an LLM for more sophisticated conversion
        sql_query = self._nl_to_sql(question, limit)
        
        if sql_query:
            return self._execute_raw_sql(sql_query)
        else:
            # Fallback to predefined queries based on keywords
            return self._find_best_predefined_query(question, limit)
    
    def _nl_to_sql(self, question: str, limit: int) -> Optional[str]:
        """Basic natural language to SQL conversion"""
        question_lower = question.lower()
        
        # Pattern matching for common business questions
        patterns = {
            r'(inventory|status|equipment).*summary': 'inventory_summary',
            r'revenue.*category': 'revenue_by_category', 
            r'store.*performance': 'store_performance',
            r'high.*value|expensive': 'high_value_items',
            r'recent.*activity|latest': 'recent_activity',
            r'maintenance|repair': 'maintenance_needed',
            r'profit|roi': 'profitability_analysis'
        }
        
        for pattern, query_name in patterns.items():
            if re.search(pattern, question_lower):
                query_template = self.predefined_queries[query_name]['sql']
                return query_template.format(
                    limit=limit,
                    days=7,
                    min_price=1000
                )
        
        return None
    
    def _find_best_predefined_query(self, question: str, limit: int) -> QueryResult:
        """Find the most relevant predefined query based on keywords"""
        question_lower = question.lower()
        
        # Score each predefined query based on keyword matches
        scores = {}
        
        keyword_mapping = {
            'inventory_summary': ['inventory', 'status', 'summary', 'overview'],
            'revenue_by_category': ['revenue', 'category', 'income', 'sales'],
            'store_performance': ['store', 'location', 'performance', 'comparison'],
            'high_value_items': ['expensive', 'valuable', 'high value', 'cost'],
            'recent_activity': ['recent', 'latest', 'new', 'activity'],
            'maintenance_needed': ['maintenance', 'repair', 'broken', 'fix'],
            'profitability_analysis': ['profit', 'roi', 'return', 'investment']
        }
        
        for query_name, keywords in keyword_mapping.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                scores[query_name] = score
        
        if scores:
            best_query = max(scores, key=scores.get)
            return self._execute_predefined_query(best_query, {}, limit)
        
        # Default fallback
        return self._execute_predefined_query('inventory_summary', {}, limit)
    
    def _execute_raw_sql(self, sql_query: str) -> QueryResult:
        """Execute raw SQL query and return structured result"""
        start_time = datetime.now()
        
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql_query))
                rows = result.fetchall()
                columns = list(result.keys()) if rows else []
                
                # Convert to list of dictionaries
                data = [dict(zip(columns, row)) for row in rows]
                
                # Convert datetime and decimal objects for JSON serialization
                for row in data:
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            row[key] = value.isoformat()
                        elif hasattr(value, '__float__'):
                            row[key] = float(value)
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return QueryResult(
                    success=True,
                    data=data,
                    row_count=len(data),
                    execution_time_ms=int(execution_time),
                    query=sql_query,
                    columns=columns
                )
                
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                success=False,
                error=str(e),
                execution_time_ms=int(execution_time),
                query=sql_query
            )
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time_ms=int(execution_time),
                query=sql_query
            )
    
    def _format_result(self, result: QueryResult) -> str:
        """Format query result for LangChain consumption"""
        output = {
            'success': result.success,
            'timestamp': datetime.now().isoformat()
        }
        
        if result.success:
            output.update({
                'data': result.data,
                'row_count': result.row_count,
                'execution_time_ms': result.execution_time_ms,
                'columns': result.columns
            })
            
            # Add summary for large result sets
            if result.row_count > 20:
                output['summary'] = f"Query returned {result.row_count} rows. Showing first 20 rows in data."
                output['data'] = result.data[:20]
        else:
            output['error'] = result.error
        
        return json.dumps(output, indent=2)
    
    def get_available_queries(self) -> Dict[str, str]:
        """Get list of available predefined queries"""
        return {
            name: info['description'] 
            for name, info in self.predefined_queries.items()
        }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        return {
            'tables': list(self.schema_info.keys()),
            'schema_details': self.schema_info
        }