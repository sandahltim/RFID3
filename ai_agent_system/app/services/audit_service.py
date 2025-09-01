"""
Audit Service for AI Agent
Comprehensive logging and security auditing for all agent operations
"""

import logging
from typing import Dict, List, Optional, Any, Union
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import aiosqlite
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    QUERY_SUBMITTED = "query_submitted"
    QUERY_COMPLETED = "query_completed"
    QUERY_FAILED = "query_failed"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    MEMORY_CLEARED = "memory_cleared"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_ALERT = "performance_alert"


@dataclass
class AuditEvent:
    """Audit event structure"""
    event_id: str
    event_type: AuditEventType
    user_id: str
    timestamp: datetime
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


class AuditService:
    """
    Comprehensive audit service for AI agent security and compliance
    
    Features:
    - Query and response logging
    - User activity tracking
    - Performance monitoring and alerting
    - Security event detection
    - Compliance reporting
    """
    
    def __init__(
        self,
        db_path: str = "data/audit.db",
        retention_days: int = 365,
        enable_security_alerts: bool = True
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.enable_security_alerts = enable_security_alerts
        
        # Performance thresholds
        self.performance_thresholds = {
            'query_time_warning': 10000,    # 10 seconds
            'query_time_critical': 30000,   # 30 seconds
            'memory_usage_warning': 80,     # 80%
            'error_rate_warning': 5,        # 5%
            'cache_hit_rate_warning': 50    # 50%
        }
        
        # Security patterns
        self.security_patterns = {
            'sql_injection': [
                r"(?i)(union.*select|drop\s+table|insert\s+into|delete\s+from)",
                r"(?i)(exec\s*\(|script\s*:|javascript\s*:)"
            ],
            'suspicious_patterns': [
                r"(?i)(password|token|secret|key)\s*[:=]",
                r"(?i)(admin|root|superuser)",
                r"(?i)(\.\.\/|\.\.\\|\.\.%2f)"
            ]
        }
        
        # Initialize database
        asyncio.create_task(self._init_database())
    
    async def _init_database(self):
        """Initialize audit database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Audit events table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS audit_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        details TEXT NOT NULL,  -- JSON
                        ip_address TEXT,
                        user_agent TEXT,
                        session_id TEXT,
                        severity TEXT DEFAULT 'info',
                        INDEX (event_type, timestamp),
                        INDEX (user_id, timestamp),
                        INDEX (timestamp)
                    )
                """)
                
                # Performance metrics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        metric_type TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        details TEXT,  -- JSON
                        INDEX (metric_type, timestamp)
                    )
                """)
                
                # Security alerts table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS security_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        user_id TEXT,
                        description TEXT NOT NULL,
                        details TEXT,  -- JSON
                        timestamp DATETIME NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        INDEX (alert_type, timestamp),
                        INDEX (severity, resolved)
                    )
                """)
                
                await db.commit()
                logger.info("Audit database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize audit database: {e}")
    
    async def log_query(
        self,
        query_id: str,
        user_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log query submission"""
        
        # Check for security patterns in query
        await self._check_security_patterns(question, user_id, ip_address)
        
        event = AuditEvent(
            event_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(query_id):x}",
            event_type=AuditEventType.QUERY_SUBMITTED,
            user_id=user_id,
            timestamp=datetime.now(),
            details={
                'query_id': query_id,
                'question': question,
                'context': context,
                'question_length': len(question)
            },
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )
        
        await self._store_audit_event(event)
    
    async def log_completion(
        self,
        query_id: str,
        success: bool,
        confidence: float,
        tools_used: List[str],
        execution_time_ms: int = 0
    ):
        """Log query completion"""
        
        event_type = AuditEventType.QUERY_COMPLETED if success else AuditEventType.QUERY_FAILED
        severity = 'info' if success else 'warning'
        
        event = AuditEvent(
            event_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(query_id):x}_comp",
            event_type=event_type,
            user_id='system',
            timestamp=datetime.now(),
            details={
                'query_id': query_id,
                'success': success,
                'confidence': confidence,
                'tools_used': tools_used,
                'execution_time_ms': execution_time_ms
            }
        )
        
        await self._store_audit_event(event, severity=severity)
        
        # Check performance thresholds
        if execution_time_ms > self.performance_thresholds['query_time_warning']:
            await self._create_performance_alert(
                'slow_query',
                f"Query {query_id} took {execution_time_ms}ms to execute",
                {'query_id': query_id, 'execution_time_ms': execution_time_ms}
            )
    
    async def log_feedback(
        self,
        feedback_id: str,
        query_id: str,
        rating: int,
        user_id: str = 'anonymous'
    ):
        """Log feedback submission"""
        
        event = AuditEvent(
            event_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(feedback_id):x}",
            event_type=AuditEventType.FEEDBACK_SUBMITTED,
            user_id=user_id,
            timestamp=datetime.now(),
            details={
                'feedback_id': feedback_id,
                'query_id': query_id,
                'rating': rating
            }
        )
        
        await self._store_audit_event(event)
    
    async def log_error(
        self,
        query_id: str,
        error: str,
        user_id: str = 'system'
    ):
        """Log system error"""
        
        event = AuditEvent(
            event_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(error):x}",
            event_type=AuditEventType.SYSTEM_ERROR,
            user_id=user_id,
            timestamp=datetime.now(),
            details={
                'query_id': query_id,
                'error': error
            }
        )
        
        await self._store_audit_event(event, severity='error')
    
    async def log_memory_clear(self, user_id: str):
        """Log memory clear operation"""
        
        event = AuditEvent(
            event_id=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(user_id):x}",
            event_type=AuditEventType.MEMORY_CLEARED,
            user_id=user_id,
            timestamp=datetime.now(),
            details={'action': 'memory_cleared'}
        )
        
        await self._store_audit_event(event)
    
    async def _store_audit_event(
        self,
        event: AuditEvent,
        severity: str = 'info'
    ):
        """Store audit event in database"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO audit_events 
                    (event_id, event_type, user_id, timestamp, details, ip_address, user_agent, session_id, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type.value,
                    event.user_id,
                    event.timestamp,
                    json.dumps(event.details, default=str),
                    event.ip_address,
                    event.user_agent,
                    event.session_id,
                    severity
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
    
    async def _check_security_patterns(
        self,
        query_text: str,
        user_id: str,
        ip_address: Optional[str] = None
    ):
        """Check query for security patterns"""
        
        if not self.enable_security_alerts:
            return
        
        import re
        
        # Check for SQL injection patterns
        for pattern in self.security_patterns['sql_injection']:
            if re.search(pattern, query_text):
                await self._create_security_alert(
                    'sql_injection_attempt',
                    'high',
                    f"Potential SQL injection attempt detected from user {user_id}",
                    {
                        'user_id': user_id,
                        'ip_address': ip_address,
                        'query_text': query_text[:200],  # Truncate for security
                        'pattern_matched': pattern
                    }
                )
                break
        
        # Check for suspicious patterns
        for pattern in self.security_patterns['suspicious_patterns']:
            if re.search(pattern, query_text):
                await self._create_security_alert(
                    'suspicious_query',
                    'medium',
                    f"Suspicious query pattern detected from user {user_id}",
                    {
                        'user_id': user_id,
                        'ip_address': ip_address,
                        'query_text': query_text[:200],
                        'pattern_matched': pattern
                    }
                )
                break
    
    async def _create_security_alert(
        self,
        alert_type: str,
        severity: str,
        description: str,
        details: Dict[str, Any]
    ):
        """Create security alert"""
        
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(description):x}"
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO security_alerts 
                    (alert_id, alert_type, severity, user_id, description, details, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert_id,
                    alert_type,
                    severity,
                    details.get('user_id', 'unknown'),
                    description,
                    json.dumps(details, default=str),
                    datetime.now()
                ))
                await db.commit()
                
                logger.warning(f"Security alert created: {alert_type} - {description}")
                
        except Exception as e:
            logger.error(f"Failed to create security alert: {e}")
    
    async def _create_performance_alert(
        self,
        alert_type: str,
        description: str,
        details: Dict[str, Any]
    ):
        """Create performance alert"""
        
        await self._create_security_alert(
            alert_type,
            'warning',
            description,
            details
        )
    
    async def get_audit_summary(
        self,
        days: int = 7,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit summary for specified period"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Base query conditions
                where_clause = "WHERE timestamp >= datetime('now', '-{} days')".format(days)
                params = []
                
                if user_id:
                    where_clause += " AND user_id = ?"
                    params.append(user_id)
                
                # Overall statistics
                cursor = await db.execute(f"""
                    SELECT 
                        event_type,
                        severity,
                        COUNT(*) as count
                    FROM audit_events 
                    {where_clause}
                    GROUP BY event_type, severity
                """, params)
                
                event_stats = {}
                rows = await cursor.fetchall()
                
                for event_type, severity, count in rows:
                    if event_type not in event_stats:
                        event_stats[event_type] = {}
                    event_stats[event_type][severity] = count
                
                # Query performance stats
                cursor = await db.execute(f"""
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(CAST(JSON_EXTRACT(details, '$.execution_time_ms') AS REAL)) as avg_execution_time,
                        MAX(CAST(JSON_EXTRACT(details, '$.execution_time_ms') AS REAL)) as max_execution_time,
                        SUM(CASE WHEN event_type = 'query_completed' THEN 1 ELSE 0 END) as successful_queries,
                        SUM(CASE WHEN event_type = 'query_failed' THEN 1 ELSE 0 END) as failed_queries
                    FROM audit_events 
                    {where_clause} AND event_type IN ('query_completed', 'query_failed')
                """, params)
                
                perf_stats = await cursor.fetchone()
                
                # Security alerts
                cursor = await db.execute(f"""
                    SELECT 
                        alert_type,
                        severity,
                        COUNT(*) as count
                    FROM security_alerts 
                    WHERE timestamp >= datetime('now', '-{} days')
                    GROUP BY alert_type, severity
                """, [days])
                
                security_stats = {}
                rows = await cursor.fetchall()
                
                for alert_type, severity, count in rows:
                    if alert_type not in security_stats:
                        security_stats[alert_type] = {}
                    security_stats[alert_type][severity] = count
                
                return {
                    'period_days': days,
                    'user_filter': user_id,
                    'event_statistics': event_stats,
                    'performance_statistics': {
                        'total_queries': perf_stats[0] or 0,
                        'avg_execution_time_ms': round(perf_stats[1] or 0, 2),
                        'max_execution_time_ms': perf_stats[2] or 0,
                        'successful_queries': perf_stats[3] or 0,
                        'failed_queries': perf_stats[4] or 0,
                        'success_rate': round(
                            (perf_stats[3] or 0) / max(perf_stats[0] or 1, 1) * 100, 2
                        )
                    },
                    'security_statistics': security_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get audit summary: {e}")
            return {'error': str(e)}
    
    async def get_performance_analytics(self, timeframe: str = "7d") -> Dict[str, Any]:
        """Get performance analytics for specified timeframe"""
        
        # Parse timeframe
        if timeframe.endswith('d'):
            days = int(timeframe[:-1])
        elif timeframe.endswith('h'):
            days = int(timeframe[:-1]) / 24
        else:
            days = 7  # Default
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Query performance over time
                cursor = await db.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as query_count,
                        AVG(CAST(JSON_EXTRACT(details, '$.execution_time_ms') AS REAL)) as avg_time,
                        SUM(CASE WHEN event_type = 'query_completed' THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN event_type = 'query_failed' THEN 1 ELSE 0 END) as failed
                    FROM audit_events 
                    WHERE timestamp >= datetime('now', '-{} days') 
                    AND event_type IN ('query_completed', 'query_failed')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """.format(int(days)))
                
                daily_performance = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    daily_performance.append({
                        'date': row[0],
                        'query_count': row[1],
                        'avg_execution_time_ms': round(row[2] or 0, 2),
                        'successful_queries': row[3],
                        'failed_queries': row[4],
                        'success_rate': round(
                            (row[3] or 0) / max(row[1], 1) * 100, 2
                        )
                    })
                
                # Tool usage statistics
                cursor = await db.execute("""
                    SELECT 
                        JSON_EXTRACT(details, '$.tools_used') as tools,
                        COUNT(*) as usage_count,
                        AVG(CAST(JSON_EXTRACT(details, '$.execution_time_ms') AS REAL)) as avg_time
                    FROM audit_events 
                    WHERE timestamp >= datetime('now', '-{} days') 
                    AND event_type = 'query_completed'
                    AND JSON_EXTRACT(details, '$.tools_used') IS NOT NULL
                    GROUP BY tools
                    ORDER BY usage_count DESC
                    LIMIT 10
                """.format(int(days)))
                
                tool_usage = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    try:
                        tools = json.loads(row[0]) if row[0] else []
                        tool_usage.append({
                            'tools': tools,
                            'usage_count': row[1],
                            'avg_execution_time_ms': round(row[2] or 0, 2)
                        })
                    except json.JSONDecodeError:
                        continue
                
                return {
                    'timeframe': timeframe,
                    'daily_performance': daily_performance,
                    'tool_usage_statistics': tool_usage,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get performance analytics: {e}")
            return {'error': str(e)}
    
    async def get_security_alerts(
        self,
        days: int = 7,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get security alerts"""
        
        try:
            where_conditions = ["timestamp >= datetime('now', '-{} days')".format(days)]
            params = []
            
            if severity:
                where_conditions.append("severity = ?")
                params.append(severity)
            
            if resolved is not None:
                where_conditions.append("resolved = ?")
                params.append(resolved)
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(f"""
                    SELECT alert_id, alert_type, severity, user_id, description, details, timestamp, resolved
                    FROM security_alerts 
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, params)
                
                alerts = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    alerts.append({
                        'alert_id': row[0],
                        'alert_type': row[1],
                        'severity': row[2],
                        'user_id': row[3],
                        'description': row[4],
                        'details': json.loads(row[5] or '{}'),
                        'timestamp': row[6],
                        'resolved': bool(row[7])
                    })
                
                return alerts
                
        except Exception as e:
            logger.error(f"Failed to get security alerts: {e}")
            return []
    
    async def cleanup_old_records(self):
        """Clean up old audit records based on retention policy"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Clean audit events
                cursor = await db.execute("""
                    DELETE FROM audit_events WHERE timestamp < ?
                """, (cutoff_date,))
                deleted_events = cursor.rowcount
                
                # Clean performance metrics
                cursor = await db.execute("""
                    DELETE FROM performance_metrics WHERE timestamp < ?
                """, (cutoff_date,))
                deleted_metrics = cursor.rowcount
                
                # Clean resolved security alerts older than retention period
                cursor = await db.execute("""
                    DELETE FROM security_alerts WHERE timestamp < ? AND resolved = TRUE
                """, (cutoff_date,))
                deleted_alerts = cursor.rowcount
                
                await db.commit()
                
                logger.info(
                    f"Cleaned up {deleted_events} audit events, "
                    f"{deleted_metrics} performance metrics, "
                    f"{deleted_alerts} security alerts"
                )
                
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
    
    async def export_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export comprehensive audit report for compliance"""
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get all events in date range
                cursor = await db.execute("""
                    SELECT event_id, event_type, user_id, timestamp, details, severity
                    FROM audit_events 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (start_date, end_date))
                
                events = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    events.append({
                        'event_id': row[0],
                        'event_type': row[1],
                        'user_id': row[2],
                        'timestamp': row[3],
                        'details': json.loads(row[4] or '{}'),
                        'severity': row[5]
                    })
                
                # Get security alerts in date range
                cursor = await db.execute("""
                    SELECT alert_id, alert_type, severity, user_id, description, timestamp, resolved
                    FROM security_alerts 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp
                """, (start_date, end_date))
                
                alerts = []
                rows = await cursor.fetchall()
                
                for row in rows:
                    alerts.append({
                        'alert_id': row[0],
                        'alert_type': row[1],
                        'severity': row[2],
                        'user_id': row[3],
                        'description': row[4],
                        'timestamp': row[5],
                        'resolved': bool(row[6])
                    })
                
                report = {
                    'report_generated': datetime.now().isoformat(),
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'summary': {
                        'total_events': len(events),
                        'total_alerts': len(alerts),
                        'unresolved_alerts': len([a for a in alerts if not a['resolved']])
                    },
                    'events': events,
                    'security_alerts': alerts
                }
                
                return report
                
        except Exception as e:
            logger.error(f"Failed to export audit report: {e}")
            return {'error': str(e)}