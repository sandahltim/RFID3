"""
Dashboard Visualization Configuration
Centralized configuration for executive dashboard enhancements
Version: 2025-08-28 - Executive Dashboard Configuration
"""

from datetime import timedelta


class DashboardConfig:
    """Configuration for enhanced dashboard visualizations"""

    # Chart Configuration
    CHART_COLORS = {
        "primary": ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"],
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#06b6d4",
        "purple": "#8b5cf6",
        "indigo": "#6366f1",
    }

    CHART_GRADIENTS = {
        "primary": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "success": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        "warning": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "info": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "dark": "linear-gradient(135deg, #2c3e50 0%, #3498db 100%)",
    }

    # Refresh Configuration
    AUTO_REFRESH_INTERVALS = {
        "executive": 300,  # 5 minutes
        "inventory": 180,  # 3 minutes
        "charts": 120,  # 2 minutes
        "kpis": 60,  # 1 minute
        "alerts": 30,  # 30 seconds
    }

    # Cache Configuration
    CACHE_TIMEOUTS = {
        "kpi_data": timedelta(minutes=2),
        "chart_data": timedelta(minutes=1),
        "financial_data": timedelta(minutes=5),
        "utilization_data": timedelta(minutes=3),
        "alert_data": timedelta(seconds=30),
    }

    # Store Mapping
    STORE_NAMES = {
        "6800": "Brooklyn Park",
        "3607": "Wayzata",
        "8101": "Fridley",
        "728": "Elk River",
        "000": "Legacy/Unassigned",
        "Unassigned": "Unassigned",
    }

    # KPI Configuration
    KPI_THRESHOLDS = {
        "utilization": {
            "good": 75,  # >= 75% is good
            "warning": 60,  # 60-75% is warning
            "danger": 60,  # < 60% is danger
        },
        "revenue_growth": {
            "good": 5,  # >= 5% growth is good
            "warning": 0,  # 0-5% is warning
            "danger": 0,  # < 0% is danger
        },
        "efficiency": {
            "good": 50,  # >= $50/hour is good
            "warning": 30,  # $30-50 is warning
            "danger": 30,  # < $30 is danger
        },
        "alerts": {
            "good": 0,  # 0 alerts is good
            "warning": 5,  # 1-5 alerts is warning
            "danger": 5,  # > 5 alerts is danger
        },
    }

    # Chart Configuration
    CHART_CONFIGS = {
        "revenue_trend": {
            "type": "line",
            "height": 300,
            "responsive": True,
            "maintain_aspect_ratio": False,
            "animation": {"duration": 750, "easing": "easeInOutQuart"},
        },
        "store_performance": {
            "type": "bar",
            "height": 300,
            "responsive": True,
            "maintain_aspect_ratio": False,
            "animation": {"duration": 500, "easing": "easeOutBounce"},
        },
        "utilization_gauge": {
            "type": "doughnut",
            "height": 250,
            "cutout": "75%",
            "animation": {"duration": 1000, "easing": "easeInOutCirc"},
        },
        "inventory_distribution": {
            "type": "doughnut",
            "height": 300,
            "cutout": "60%",
            "animation": {"duration": 800, "easing": "easeInOutBack"},
        },
        "forecast": {
            "type": "line",
            "height": 300,
            "responsive": True,
            "maintain_aspect_ratio": False,
            "animation": {"duration": 1200, "easing": "easeInOutSine"},
        },
    }

    # API Endpoints
    API_ENDPOINTS = {
        "kpis": "/api/enhanced/dashboard/kpis",
        "store_performance": "/api/enhanced/dashboard/store-performance",
        "inventory_distribution": "/api/enhanced/dashboard/inventory-distribution",
        "financial_metrics": "/api/enhanced/dashboard/financial-metrics",
        "utilization_analysis": "/api/enhanced/dashboard/utilization-analysis",
    }

    # Error Messages
    ERROR_MESSAGES = {
        "connection_failed": "Unable to connect to data source",
        "data_not_found": "Requested data not available",
        "calculation_error": "Error calculating metrics",
        "chart_render_error": "Failed to render chart",
        "filter_error": "Invalid filter parameters",
        "cache_error": "Cache system error",
        "auth_error": "Authentication required",
        "timeout_error": "Request timeout - try again",
    }

    # Success Messages
    SUCCESS_MESSAGES = {
        "data_loaded": "Dashboard data loaded successfully",
        "charts_refreshed": "All charts refreshed",
        "filters_applied": "Filters applied successfully",
        "export_complete": "Report exported successfully",
        "cache_cleared": "Cache cleared successfully",
    }

    # Dashboard Layout Configuration
    LAYOUT_CONFIG = {
        "mobile_breakpoint": 768,
        "tablet_breakpoint": 1024,
        "desktop_breakpoint": 1200,
        "grid_columns": {"mobile": 1, "tablet": 2, "desktop": 4},
        "chart_aspect_ratios": {"mobile": 1.2, "tablet": 1.5, "desktop": 2.0},
    }

    # Performance Configuration
    PERFORMANCE_CONFIG = {
        "max_concurrent_requests": 5,
        "request_timeout": 30,  # seconds
        "retry_attempts": 3,
        "retry_delay": 1,  # seconds
        "chunk_size": 1000,  # for large datasets
        "lazy_loading": True,
        "virtual_scrolling": True,
    }

    # Accessibility Configuration
    A11Y_CONFIG = {
        "high_contrast_mode": False,
        "reduce_motion": False,
        "screen_reader_support": True,
        "keyboard_navigation": True,
        "focus_indicators": True,
        "alt_text_required": True,
    }

    # Export Configuration
    EXPORT_CONFIG = {
        "formats": ["pdf", "excel", "csv", "png"],
        "default_format": "pdf",
        "include_charts": True,
        "include_data": True,
        "include_filters": True,
        "max_file_size": "50MB",
        "compression": True,
    }

    # Notification Configuration
    NOTIFICATION_CONFIG = {
        "show_success": True,
        "show_warnings": True,
        "show_errors": True,
        "auto_dismiss": True,
        "dismiss_timeout": 5000,  # milliseconds
        "max_notifications": 3,
        "position": "top-right",
    }


class ChartDefaults:
    """Default Chart.js configuration for consistent styling"""

    @staticmethod
    def get_default_options():
        return {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "labels": {
                        "usePointStyle": True,
                        "padding": 15,
                        "font": {
                            "family": "'Segoe UI', system-ui, sans-serif",
                            "size": 12,
                            "weight": "600",
                        },
                        "color": "#4a5568",
                    }
                },
                "tooltip": {
                    "backgroundColor": "rgba(26, 32, 44, 0.95)",
                    "titleColor": "#ffffff",
                    "bodyColor": "#ffffff",
                    "borderColor": "rgba(102, 126, 234, 0.8)",
                    "borderWidth": 2,
                    "cornerRadius": 12,
                    "padding": 16,
                    "displayColors": True,
                    "titleFont": {"size": 14, "weight": "600"},
                    "bodyFont": {"size": 13},
                },
            },
            "scales": {
                "x": {
                    "grid": {"color": "rgba(0, 0, 0, 0.1)", "drawBorder": False},
                    "ticks": {
                        "font": {
                            "family": "'Segoe UI', system-ui, sans-serif",
                            "size": 11,
                            "weight": "500",
                        },
                        "color": "#4a5568",
                    },
                },
                "y": {
                    "grid": {"color": "rgba(0, 0, 0, 0.1)", "drawBorder": False},
                    "ticks": {
                        "font": {
                            "family": "'Segoe UI', system-ui, sans-serif",
                            "size": 11,
                            "weight": "500",
                        },
                        "color": "#4a5568",
                    },
                },
            },
            "animation": {"duration": 750, "easing": "easeInOutQuart"},
            "interaction": {"intersect": False, "mode": "index"},
        }

    @staticmethod
    def get_color_palette():
        return DashboardConfig.CHART_COLORS["primary"]

    @staticmethod
    def get_gradient_definitions():
        return DashboardConfig.CHART_GRADIENTS


# Global dashboard configuration instance
dashboard_config = DashboardConfig()
chart_defaults = ChartDefaults()
