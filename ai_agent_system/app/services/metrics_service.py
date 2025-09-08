"""
Metrics Service for AI Agent Performance Monitoring
Provides Prometheus metrics and business intelligence tracking
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
import asyncio

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Comprehensive metrics service for AI agent monitoring
    
    Provides:
    - Application performance metrics
    - Business intelligence metrics  
    - User behavior analytics
    - System health indicators
    - Custom Minnesota equipment rental metrics
    """
    
    def __init__(self):
        # Create custom registry for AI agent metrics
        self.registry = CollectorRegistry()
        
        # Application Performance Metrics
        self.queries_total = Counter(
            'ai_agent_queries_total',
            'Total number of queries processed',
            ['user_type', 'query_category'],
            registry=self.registry
        )
        
        self.query_duration = Histogram(
            'ai_agent_query_duration_seconds',
            'Query processing duration in seconds',
            ['tool_used', 'success'],
            registry=self.registry
        )
        
        self.query_errors = Counter(
            'ai_agent_query_errors_total',
            'Total query errors by type',
            ['error_type', 'tool_name'],
            registry=self.registry
        )
        
        # LLM Model Metrics
        self.llm_inference_duration = Histogram(
            'ai_agent_llm_inference_duration_seconds',
            'LLM inference time in seconds',
            ['model_name'],
            registry=self.registry
        )
        
        self.llm_token_count = Histogram(
            'ai_agent_llm_tokens_total',
            'Number of tokens processed',
            ['direction'],  # input, output
            registry=self.registry
        )
        
        # Cache Metrics
        self.cache_hits = Counter(
            'ai_agent_cache_hits_total',
            'Cache hit count',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'ai_agent_cache_misses_total',
            'Cache miss count',
            ['cache_type'],
            registry=self.registry
        )
        
        # Tool Usage Metrics
        self.tool_usage = Counter(
            'ai_agent_tool_usage_total',
            'Tool usage count',
            ['tool_name', 'success'],
            registry=self.registry
        )
        
        self.tool_duration = Histogram(
            'ai_agent_tool_duration_seconds',
            'Tool execution duration',
            ['tool_name'],
            registry=self.registry
        )
        
        # Feedback and Quality Metrics
        self.feedback_total = Counter(
            'ai_agent_feedback_total',
            'Total feedback received',
            ['rating'],
            registry=self.registry
        )
        
        self.feedback_positive = Counter(
            'ai_agent_feedback_positive_total',
            'Positive feedback count',
            registry=self.registry
        )
        
        self.feedback_negative = Counter(
            'ai_agent_feedback_negative_total',
            'Negative feedback count',
            registry=self.registry
        )
        
        # Security Metrics
        self.security_alerts = Counter(
            'ai_agent_security_alerts_total',
            'Security alerts by type',
            ['alert_type', 'severity'],
            registry=self.registry
        )
        
        # Business Intelligence Metrics
        self.insights_generated = Counter(
            'ai_agent_insights_generated_total',
            'Business insights generated',
            ['insight_type', 'confidence_level'],
            registry=self.registry
        )
        
        self.data_correlations = Counter(
            'ai_agent_correlations_found_total',
            'Data correlations discovered',
            ['data_source_combo'],
            registry=self.registry
        )
        
        # Minnesota-Specific Business Metrics
        self.equipment_queries = Counter(
            'ai_agent_equipment_queries_total',
            'Equipment-related queries',
            ['equipment_category', 'business_unit'],  # A1 Rent It, Broadway Tent
            registry=self.registry
        )
        
        self.weather_impact_analysis = Counter(
            'ai_agent_weather_analysis_total',
            'Weather impact analyses performed',
            ['season', 'equipment_category'],
            registry=self.registry
        )
        
        self.seasonal_predictions = Counter(
            'ai_agent_seasonal_predictions_total',
            'Seasonal demand predictions made',
            ['season', 'accuracy_level'],
            registry=self.registry
        )
        
        # System Health Gauges
        self.active_users = Gauge(
            'ai_agent_active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'ai_agent_memory_usage_bytes',
            'Memory usage in bytes',
            ['component'],
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'ai_agent_database_connections',
            'Active database connections',
            registry=self.registry
        )
        
        # Application Info
        self.app_info = Info(
            'ai_agent_info',
            'AI Agent application information',
            registry=self.registry
        )
        
        # Initialize app info
        self.app_info.info({
            'version': '1.0.0',
            'model': 'qwen2.5:7b-instruct',
            'business': 'minnesota_equipment_rental',
            'deployment': 'rtx_4070'
        })
        
        # Performance tracking
        self.start_time = time.time()
        self.last_metrics_export = time.time()
        
        logger.info("Metrics service initialized with custom Prometheus registry")
    
    def record_query(
        self,
        duration_seconds: float,
        success: bool,
        user_type: str = "authenticated",
        query_category: str = "general",
        tools_used: List[str] = None,
        error_type: str = None
    ):
        """Record query metrics"""
        
        # Basic query metrics
        self.queries_total.labels(
            user_type=user_type,
            query_category=query_category
        ).inc()
        
        # Duration by tool usage
        primary_tool = tools_used[0] if tools_used else "none"
        self.query_duration.labels(
            tool_used=primary_tool,
            success="true" if success else "false"
        ).observe(duration_seconds)
        
        # Error tracking
        if not success and error_type:
            tool_name = primary_tool if tools_used else "system"
            self.query_errors.labels(
                error_type=error_type,
                tool_name=tool_name
            ).inc()
        
        # Equipment-specific tracking
        if query_category in ['equipment', 'inventory', 'rental']:
            business_unit = self._detect_business_unit(tools_used or [])
            equipment_category = self._detect_equipment_category(query_category)
            
            self.equipment_queries.labels(
                equipment_category=equipment_category,
                business_unit=business_unit
            ).inc()
    
    def record_tool_usage(
        self,
        tool_name: str,
        duration_seconds: float,
        success: bool
    ):
        """Record tool usage metrics"""
        
        self.tool_usage.labels(
            tool_name=tool_name,
            success="true" if success else "false"
        ).inc()
        
        self.tool_duration.labels(tool_name=tool_name).observe(duration_seconds)
    
    def record_llm_inference(
        self,
        duration_seconds: float,
        input_tokens: int,
        output_tokens: int,
        model_name: str = "qwen2.5:7b-instruct"
    ):
        """Record LLM inference metrics"""
        
        self.llm_inference_duration.labels(model_name=model_name).observe(duration_seconds)
        self.llm_token_count.labels(direction="input").observe(input_tokens)
        self.llm_token_count.labels(direction="output").observe(output_tokens)
    
    def record_cache_event(self, hit: bool, cache_type: str = "query"):
        """Record cache hit/miss"""
        
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_feedback(
        self,
        rating: int,
        helpful: bool
    ):
        """Record user feedback"""
        
        self.feedback_total.labels(rating=str(rating)).inc()
        
        if helpful or rating >= 4:
            self.feedback_positive.inc()
        elif rating <= 2:
            self.feedback_negative.inc()
    
    def record_security_alert(
        self,
        alert_type: str,
        severity: str = "medium"
    ):
        """Record security alert"""
        
        self.security_alerts.labels(
            alert_type=alert_type,
            severity=severity
        ).inc()
    
    def record_business_insight(
        self,
        insight_type: str,
        confidence: float
    ):
        """Record business insight generation"""
        
        # Map confidence to level
        if confidence >= 0.8:
            confidence_level = "high"
        elif confidence >= 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        self.insights_generated.labels(
            insight_type=insight_type,
            confidence_level=confidence_level
        ).inc()
    
    def record_weather_analysis(
        self,
        equipment_category: str,
        season: str = None
    ):
        """Record weather impact analysis"""
        
        if not season:
            season = self._get_current_season()
        
        self.weather_impact_analysis.labels(
            season=season,
            equipment_category=equipment_category
        ).inc()
    
    def record_data_correlation(self, data_sources: List[str]):
        """Record data correlation discovery"""
        
        # Create combo identifier
        data_source_combo = "+".join(sorted(data_sources))
        
        self.data_correlations.labels(
            data_source_combo=data_source_combo
        ).inc()
    
    def update_system_metrics(
        self,
        active_users: int = 0,
        memory_usage_bytes: int = 0,
        database_connections: int = 0
    ):
        """Update system health metrics"""
        
        self.active_users.set(active_users)
        
        if memory_usage_bytes > 0:
            self.memory_usage.labels(component="total").set(memory_usage_bytes)
        
        if database_connections > 0:
            self.database_connections.set(database_connections)
    
    def _detect_business_unit(self, tools_used: List[str]) -> str:
        """Detect business unit from context"""
        
        # This would be enhanced with actual business logic
        if any('construction' in tool.lower() for tool in tools_used):
            return "a1_rent_it"
        elif any('event' in tool.lower() or 'tent' in tool.lower() for tool in tools_used):
            return "broadway_tent"
        else:
            return "general"
    
    def _detect_equipment_category(self, query_category: str) -> str:
        """Detect equipment category from query"""
        
        category_mapping = {
            'equipment': 'general_equipment',
            'inventory': 'inventory_management',
            'rental': 'rental_operations',
            'construction': 'construction_equipment',
            'event': 'event_equipment'
        }
        
        return category_mapping.get(query_category, 'general')
    
    def _get_current_season(self) -> str:
        """Get current Minnesota season"""
        
        month = datetime.now().month
        
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:  # 9, 10, 11
            return "fall"
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of key metrics"""
        
        current_time = time.time()
        uptime_seconds = current_time - self.start_time
        
        return {
            'uptime_seconds': uptime_seconds,
            'last_export': self.last_metrics_export,
            'registry_collectors': len(list(self.registry._collector_to_names.keys())),
            'system_info': {
                'version': '1.0.0',
                'model': 'qwen2.5:7b-instruct',
                'deployment': 'rtx_4070'
            }
        }
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        
        self.last_metrics_export = time.time()
        
        # Update system metrics before export
        import psutil
        import os
        
        # Memory usage
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        self.memory_usage.labels(component="rss").set(memory_info.rss)
        self.memory_usage.labels(component="vms").set(memory_info.vms)
        
        # Export in Prometheus format
        return generate_latest(self.registry)
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business-specific metrics summary"""
        
        return {
            'equipment_queries': {
                'a1_rent_it': self._get_metric_value('ai_agent_equipment_queries_total', {'business_unit': 'a1_rent_it'}),
                'broadway_tent': self._get_metric_value('ai_agent_equipment_queries_total', {'business_unit': 'broadway_tent'})
            },
            'seasonal_analysis': {
                'current_season': self._get_current_season(),
                'weather_analyses': self._get_metric_value('ai_agent_weather_analysis_total'),
                'seasonal_predictions': self._get_metric_value('ai_agent_seasonal_predictions_total')
            },
            'insights_generated': self._get_metric_value('ai_agent_insights_generated_total'),
            'data_correlations': self._get_metric_value('ai_agent_correlations_found_total')
        }
    
    def _get_metric_value(self, metric_name: str, labels: Dict[str, str] = None) -> float:
        """Get current value of a metric (simplified for example)"""
        
        # In production, this would query the actual metric values
        # For now, return 0 as placeholder
        return 0.0