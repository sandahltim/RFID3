"""
Predictive Visualization Service for RFID3 Equipment Rental System
Creates interactive visualizations for predictive analytics insights
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union
import logging
import json

from app.services.logger import get_logger
from app.services.predictive_analytics_service import PredictiveAnalyticsService
from app.services.ml_data_pipeline_service import MLDataPipelineService

logger = get_logger(__name__)

class PredictiveVisualizationService:
    """
    Service for creating predictive analytics visualizations
    
    Features:
    - Forecasting charts with confidence bands
    - Equipment recommendation dashboards
    - Risk/opportunity alerts
    - Model performance monitoring
    - Interactive drill-down capabilities
    - Executive-friendly summary views
    """
    
    def __init__(self):
        self.predictive_service = PredictiveAnalyticsService()
        self.pipeline_service = MLDataPipelineService()
        self.logger = logger
        
        # Visualization configuration
        self.chart_colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#6C757D',
            'light': '#F8F9FA',
            'dark': '#343A40'
        }
        
        self.confidence_colors = {
            '80%': 'rgba(46, 134, 171, 0.2)',
            '90%': 'rgba(46, 134, 171, 0.3)',
            '95%': 'rgba(46, 134, 171, 0.4)'
        }
    
    def get_executive_predictive_dashboard(self, store_id: Optional[int] = None) -> Dict:
        """
        Get executive-level predictive analytics dashboard
        """
        try:
            # Get predictive data
            predictive_data = self.predictive_service.get_predictive_dashboard(store_id)
            
            if not predictive_data.get('success'):
                return {'error': 'Failed to get predictive data'}
            
            dashboard = {
                'forecast_charts': self.create_forecast_visualization(predictive_data['data']['demand_forecasts']),
                'revenue_predictions': self.create_revenue_prediction_charts(predictive_data['data']['revenue_predictions']),
                'utilization_heatmap': self.create_utilization_heatmap(predictive_data['data']['utilization_optimization']),
                'seasonal_insights': self.create_seasonal_insight_charts(predictive_data['data']['seasonal_insights']),
                'risk_opportunity_alerts': self.create_alert_visualizations(predictive_data['data']['risk_opportunities']),
                'kpi_summary_cards': self.create_kpi_summary_cards(predictive_data),
                'model_performance_charts': self.create_model_performance_charts(predictive_data['data']['model_performance']),
                'data_quality_gauge': self.create_data_quality_gauge(predictive_data['data']['data_quality_score'])
            }
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'dashboard': dashboard,
                'metadata': predictive_data.get('metadata', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error creating executive dashboard: {str(e)}")
            return {'error': str(e)}
    
    def create_forecast_visualization(self, forecast_data: Dict) -> Dict:
        """
        Create demand forecast visualization with confidence bands
        """
        try:
            if 'overall_forecasts' not in forecast_data:
                return {'error': 'No forecast data available'}
            
            charts = {}
            
            for horizon, data in forecast_data['overall_forecasts'].items():
                if 'error' in data:
                    continue
                
                chart_config = {
                    'type': 'line',
                    'title': f'{horizon.replace("_", " ").title()} Demand Forecast',
                    'data': {
                        'labels': data.get('forecast_dates', []),
                        'datasets': []
                    },
                    'options': {
                        'responsive': True,
                        'interaction': {
                            'mode': 'index',
                            'intersect': False,
                        },
                        'plugins': {
                            'title': {
                                'display': True,
                                'text': f'Equipment Demand Forecast - {horizon.replace("_", " ").title()}'
                            },
                            'legend': {
                                'position': 'top'
                            }
                        },
                        'scales': {
                            'x': {
                                'display': True,
                                'title': {
                                    'display': True,
                                    'text': 'Date'
                                }
                            },
                            'y': {
                                'display': True,
                                'title': {
                                    'display': True,
                                    'text': 'Demand (Units)'
                                }
                            }
                        }
                    }
                }
                
                # Main forecast line
                chart_config['data']['datasets'].append({
                    'label': 'Forecast',
                    'data': data.get('forecast_values', []),
                    'borderColor': self.chart_colors['primary'],
                    'backgroundColor': 'transparent',
                    'borderWidth': 3,
                    'fill': False,
                    'tension': 0.4
                })
                
                # Confidence bands
                for level, band_data in data.get('confidence_bands', {}).items():
                    # Upper bound
                    chart_config['data']['datasets'].append({
                        'label': f'{level} Upper Bound',
                        'data': band_data.get('upper', []),
                        'borderColor': 'transparent',
                        'backgroundColor': self.confidence_colors.get(level, 'rgba(0,0,0,0.1)'),
                        'fill': f'+{len(chart_config["data"]["datasets"])}'  # Fill to next dataset
                    })
                    
                    # Lower bound
                    chart_config['data']['datasets'].append({
                        'label': f'{level} Lower Bound',
                        'data': band_data.get('lower', []),
                        'borderColor': 'transparent',
                        'backgroundColor': 'transparent',
                        'fill': False
                    })
                
                charts[horizon] = chart_config
            
            # Category-specific forecasts
            if 'category_forecasts' in forecast_data:
                category_chart = self.create_category_forecast_chart(forecast_data['category_forecasts'])
                charts['category_breakdown'] = category_chart
            
            return {
                'charts': charts,
                'summary': {
                    'total_forecasts': len(charts),
                    'forecast_accuracy': forecast_data.get('forecast_accuracy', {}),
                    'data_coverage': forecast_data.get('data_coverage', {})
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error creating forecast visualization: {str(e)}")
            return {'error': str(e)}
    
    def create_revenue_prediction_charts(self, revenue_data: Dict) -> Dict:
        """
        Create revenue prediction visualizations
        """
        try:
            if 'revenue_predictions' not in revenue_data:
                return {'error': 'No revenue prediction data available'}
            
            charts = {}
            
            # Revenue trend chart
            revenue_chart = {
                'type': 'bar',
                'title': 'Revenue Predictions by Time Horizon',
                'data': {
                    'labels': [],
                    'datasets': [{
                        'label': 'Predicted Revenue',
                        'data': [],
                        'backgroundColor': self.chart_colors['success'],
                        'borderColor': self.chart_colors['success'],
                        'borderWidth': 1
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Revenue Predictions by Time Horizon'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Revenue ($)'
                            }
                        }
                    }
                }
            }
            
            # Populate revenue prediction data
            for horizon, prediction in revenue_data['revenue_predictions'].items():
                if 'error' not in prediction:
                    revenue_chart['data']['labels'].append(horizon.replace('_', ' ').title())
                    total_prediction = sum(prediction.get('forecast_values', [0]))
                    revenue_chart['data']['datasets'][0]['data'].append(total_prediction)
            
            charts['revenue_predictions'] = revenue_chart
            
            # Seasonal revenue patterns
            if 'seasonal_patterns' in revenue_data:
                seasonal_chart = self.create_seasonal_revenue_chart(revenue_data['seasonal_patterns'])
                charts['seasonal_patterns'] = seasonal_chart
            
            # Category revenue breakdown
            if 'category_predictions' in revenue_data:
                category_chart = self.create_category_revenue_chart(revenue_data['category_predictions'])
                charts['category_breakdown'] = category_chart
            
            return {
                'charts': charts,
                'revenue_drivers': revenue_data.get('revenue_drivers', {}),
                'confidence_metrics': revenue_data.get('confidence_metrics', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error creating revenue prediction charts: {str(e)}")
            return {'error': str(e)}
    
    def create_utilization_heatmap(self, utilization_data: Dict) -> Dict:
        """
        Create equipment utilization heatmap
        """
        try:
            if 'underutilized_equipment' not in utilization_data:
                return {'error': 'No utilization data available'}
            
            # Equipment utilization heatmap
            heatmap = {
                'type': 'heatmap',
                'title': 'Equipment Utilization Analysis',
                'data': {
                    'datasets': [{
                        'label': 'Utilization Rate',
                        'data': [],
                        'backgroundColor': []
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Equipment Utilization Heatmap'
                        },
                        'legend': {
                            'display': False
                        }
                    }
                }
            }
            
            # Process utilization data
            utilization_categories = ['underutilized_equipment', 'overutilized_equipment']
            
            for category in utilization_categories:
                if category in utilization_data:
                    items = utilization_data[category]
                    for item in items[:10]:  # Top 10 items
                        heatmap['data']['datasets'][0]['data'].append({
                            'x': item.get('category', 'Unknown'),
                            'y': item.get('item_num', 'Unknown'),
                            'v': item.get('utilization_rate', 0) * 100
                        })
            
            # Recommendations chart
            recommendations_chart = self.create_recommendations_chart(utilization_data)
            
            return {
                'heatmap': heatmap,
                'recommendations_chart': recommendations_chart,
                'priority_scores': utilization_data.get('priority_scores', {}),
                'optimization_opportunities': utilization_data.get('roi_improvement_opportunities', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error creating utilization heatmap: {str(e)}")
            return {'error': str(e)}
    
    def create_seasonal_insight_charts(self, seasonal_data: Dict) -> Dict:
        """
        Create seasonal insight visualizations
        """
        try:
            charts = {}
            
            # Seasonal demand patterns
            if 'predictive_seasonal_insights' in seasonal_data:
                insights = seasonal_data['predictive_seasonal_insights']
                
                # Seasonal demand chart
                seasonal_chart = {
                    'type': 'line',
                    'title': 'Seasonal Demand Patterns',
                    'data': {
                        'labels': ['Winter', 'Spring', 'Summer', 'Fall'],
                        'datasets': [{
                            'label': 'Historical Pattern',
                            'data': [75, 90, 100, 85],  # Placeholder seasonal factors
                            'borderColor': self.chart_colors['primary'],
                            'backgroundColor': 'transparent',
                            'borderWidth': 2
                        }, {
                            'label': 'Predicted Pattern',
                            'data': [80, 95, 105, 90],  # Placeholder predictions
                            'borderColor': self.chart_colors['secondary'],
                            'backgroundColor': 'transparent',
                            'borderWidth': 2,
                            'borderDash': [5, 5]
                        }]
                    },
                    'options': {
                        'responsive': True,
                        'plugins': {
                            'title': {
                                'display': True,
                                'text': 'Seasonal Demand Patterns'
                            }
                        },
                        'scales': {
                            'y': {
                                'title': {
                                    'display': True,
                                    'text': 'Demand Index'
                                }
                            }
                        }
                    }
                }
                
                charts['seasonal_patterns'] = seasonal_chart
            
            # Weather impact chart
            weather_impact_chart = {
                'type': 'scatter',
                'title': 'Weather Impact on Equipment Demand',
                'data': {
                    'datasets': [{
                        'label': 'Temperature vs Demand',
                        'data': self.generate_weather_demand_data(),
                        'backgroundColor': self.chart_colors['info'],
                        'borderColor': self.chart_colors['info']
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Weather Impact Analysis'
                        }
                    },
                    'scales': {
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Temperature (°F)'
                            }
                        },
                        'y': {
                            'title': {
                                'display': True,
                                'text': 'Demand Index'
                            }
                        }
                    }
                }
            }
            
            charts['weather_impact'] = weather_impact_chart
            
            return {
                'charts': charts,
                'seasonal_risks': seasonal_data.get('seasonal_risk_factors', {}),
                'inventory_recommendations': seasonal_data.get('predictive_seasonal_insights', {}).get('seasonal_inventory_recommendations', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error creating seasonal insight charts: {str(e)}")
            return {'error': str(e)}
    
    def create_alert_visualizations(self, alert_data: Dict) -> Dict:
        """
        Create risk and opportunity alert visualizations
        """
        try:
            alerts = {
                'priority_alerts': [],
                'risk_gauge': None,
                'opportunity_chart': None
            }
            
            # Process prioritized alerts
            if 'prioritized_alerts' in alert_data:
                for alert in alert_data['prioritized_alerts'][:5]:  # Top 5 alerts
                    alert_item = {
                        'type': alert.get('type', 'info'),
                        'title': alert.get('title', 'Alert'),
                        'message': alert.get('message', ''),
                        'priority': alert.get('priority', 'medium'),
                        'impact': alert.get('impact', 'unknown'),
                        'timestamp': alert.get('timestamp', datetime.now().isoformat())
                    }
                    alerts['priority_alerts'].append(alert_item)
            
            # Risk gauge
            risk_score = self.calculate_overall_risk_score(alert_data)
            alerts['risk_gauge'] = {
                'type': 'gauge',
                'value': risk_score,
                'min': 0,
                'max': 100,
                'title': 'Overall Risk Score',
                'color': self.get_risk_color(risk_score),
                'ranges': [
                    {'from': 0, 'to': 30, 'color': '#28A745', 'label': 'Low Risk'},
                    {'from': 30, 'to': 70, 'color': '#FFC107', 'label': 'Medium Risk'},
                    {'from': 70, 'to': 100, 'color': '#DC3545', 'label': 'High Risk'}
                ]
            }
            
            # Opportunity chart
            if 'revenue_opportunities' in alert_data:
                opportunity_chart = {
                    'type': 'doughnut',
                    'title': 'Revenue Opportunities',
                    'data': {
                        'labels': [],
                        'datasets': [{
                            'data': [],
                            'backgroundColor': [
                                self.chart_colors['success'],
                                self.chart_colors['warning'],
                                self.chart_colors['info'],
                                self.chart_colors['secondary']
                            ]
                        }]
                    }
                }
                
                # Populate opportunity data
                opportunities = alert_data['revenue_opportunities'][:4]  # Top 4
                for opp in opportunities:
                    opportunity_chart['data']['labels'].append(opp.get('title', 'Opportunity'))
                    opportunity_chart['data']['datasets'][0]['data'].append(opp.get('potential_value', 0))
                
                alerts['opportunity_chart'] = opportunity_chart
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error creating alert visualizations: {str(e)}")
            return {'error': str(e)}
    
    def create_kpi_summary_cards(self, predictive_data: Dict) -> List[Dict]:
        """
        Create KPI summary cards for the dashboard
        """
        try:
            cards = []
            
            if not predictive_data.get('success'):
                return []
            
            data = predictive_data.get('data', {})
            
            # Forecast accuracy card
            forecast_accuracy = data.get('model_performance', {}).get('forecast_accuracy', {})
            cards.append({
                'title': 'Forecast Accuracy',
                'value': f"{forecast_accuracy.get('overall_accuracy', 0):.1f}%",
                'change': f"+{forecast_accuracy.get('improvement', 0):.1f}%",
                'trend': 'up' if forecast_accuracy.get('improvement', 0) > 0 else 'down',
                'color': 'success',
                'icon': 'fa-chart-line'
            })
            
            # Data quality card
            quality_score = data.get('data_quality_score', {})
            cards.append({
                'title': 'Data Quality Score',
                'value': f"{quality_score.get('overall_score', 0):.1f}/100",
                'change': f"{quality_score.get('score_trend', {}).get('change_rate', 0):+.1f}/month",
                'trend': 'up' if quality_score.get('score_trend', {}).get('change_rate', 0) > 0 else 'down',
                'color': 'info',
                'icon': 'fa-database'
            })
            
            # RFID correlation coverage
            metadata = predictive_data.get('metadata', {})
            cards.append({
                'title': 'RFID Coverage',
                'value': metadata.get('rfid_correlation_coverage', '1.78%'),
                'change': f"{metadata.get('correlated_items', 290)}/{metadata.get('total_equipment_items', 16259)} items",
                'trend': 'stable',
                'color': 'warning',
                'icon': 'fa-tags'
            })
            
            # Revenue prediction confidence
            revenue_confidence = data.get('revenue_predictions', {}).get('confidence_metrics', {})
            cards.append({
                'title': 'Prediction Confidence',
                'value': f"{revenue_confidence.get('average_confidence', 0):.1f}%",
                'change': f"±{revenue_confidence.get('confidence_interval', 0):.1f}%",
                'trend': 'stable',
                'color': 'primary',
                'icon': 'fa-bullseye'
            })
            
            return cards
            
        except Exception as e:
            self.logger.error(f"Error creating KPI summary cards: {str(e)}")
            return []
    
    def create_model_performance_charts(self, performance_data: Dict) -> Dict:
        """
        Create model performance monitoring charts
        """
        try:
            charts = {}
            
            # Forecast accuracy over time
            accuracy_chart = {
                'type': 'line',
                'title': 'Model Performance Over Time',
                'data': {
                    'labels': self.generate_time_labels(30),  # Last 30 days
                    'datasets': [{
                        'label': 'Forecast Accuracy',
                        'data': self.generate_performance_data(30),
                        'borderColor': self.chart_colors['primary'],
                        'backgroundColor': 'transparent',
                        'borderWidth': 2
                    }, {
                        'label': 'Data Quality Score',
                        'data': self.generate_quality_data(30),
                        'borderColor': self.chart_colors['secondary'],
                        'backgroundColor': 'transparent',
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Model Performance Tracking'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': 'Performance Score (%)'
                            }
                        }
                    }
                }
            }
            
            charts['performance_tracking'] = accuracy_chart
            
            # Model drift detection
            drift_chart = {
                'type': 'bar',
                'title': 'Model Drift Detection',
                'data': {
                    'labels': ['Demand Model', 'Revenue Model', 'Utilization Model'],
                    'datasets': [{
                        'label': 'Drift Score',
                        'data': [0.15, 0.08, 0.22],  # Example drift scores
                        'backgroundColor': [
                            self.get_drift_color(0.15),
                            self.get_drift_color(0.08),
                            self.get_drift_color(0.22)
                        ]
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Model Drift Analysis'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 1,
                            'title': {
                                'display': True,
                                'text': 'Drift Score'
                            }
                        }
                    }
                }
            }
            
            charts['drift_detection'] = drift_chart
            
            return {
                'charts': charts,
                'performance_summary': performance_data,
                'recommendations': self.get_model_improvement_recommendations(performance_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating model performance charts: {str(e)}")
            return {'error': str(e)}
    
    def create_data_quality_gauge(self, quality_data: Dict) -> Dict:
        """
        Create data quality gauge visualization
        """
        try:
            if not quality_data:
                return {'error': 'No quality data available'}
            
            overall_score = quality_data.get('overall_score', 0)
            component_scores = quality_data.get('component_scores', {})
            
            gauge = {
                'type': 'gauge',
                'title': 'Data Quality Score',
                'value': overall_score,
                'min': 0,
                'max': 100,
                'color': self.get_quality_color(overall_score),
                'ranges': [
                    {'from': 0, 'to': 50, 'color': '#DC3545', 'label': 'Poor'},
                    {'from': 50, 'to': 75, 'color': '#FFC107', 'label': 'Fair'},
                    {'from': 75, 'to': 90, 'color': '#28A745', 'label': 'Good'},
                    {'from': 90, 'to': 100, 'color': '#17A2B8', 'label': 'Excellent'}
                ],
                'components': [
                    {
                        'name': 'RFID Coverage',
                        'score': component_scores.get('rfid_correlation_coverage', 0),
                        'color': self.get_quality_color(component_scores.get('rfid_correlation_coverage', 0))
                    },
                    {
                        'name': 'Data Completeness',
                        'score': component_scores.get('data_completeness', 0),
                        'color': self.get_quality_color(component_scores.get('data_completeness', 0))
                    },
                    {
                        'name': 'Data Freshness',
                        'score': component_scores.get('data_freshness', 0),
                        'color': self.get_quality_color(component_scores.get('data_freshness', 0))
                    },
                    {
                        'name': 'Data Consistency',
                        'score': component_scores.get('data_consistency', 0),
                        'color': self.get_quality_color(component_scores.get('data_consistency', 0))
                    },
                    {
                        'name': 'Historical Depth',
                        'score': component_scores.get('historical_depth', 0),
                        'color': self.get_quality_color(component_scores.get('historical_depth', 0))
                    }
                ]
            }
            
            return {
                'gauge': gauge,
                'improvement_recommendations': quality_data.get('improvement_recommendations', []),
                'trend': quality_data.get('score_trend', {})
            }
            
        except Exception as e:
            self.logger.error(f"Error creating data quality gauge: {str(e)}")
            return {'error': str(e)}
    
    # Helper methods for chart creation
    
    def create_category_forecast_chart(self, category_data: Dict) -> Dict:
        """Create category-specific forecast chart"""
        chart = {
            'type': 'bar',
            'title': 'Demand Forecast by Equipment Category',
            'data': {
                'labels': [],
                'datasets': [{
                    'label': 'Predicted Demand',
                    'data': [],
                    'backgroundColor': self.chart_colors['primary']
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Equipment Category Demand Forecasts'
                    }
                }
            }
        }
        
        # Populate with category data
        for category, forecast in category_data.items():
            if isinstance(forecast, dict) and 'forecast_values' in forecast:
                chart['data']['labels'].append(category)
                chart['data']['datasets'][0]['data'].append(sum(forecast['forecast_values']))
        
        return chart
    
    def create_seasonal_revenue_chart(self, seasonal_data: Dict) -> Dict:
        """Create seasonal revenue pattern chart"""
        return {
            'type': 'radar',
            'title': 'Seasonal Revenue Patterns',
            'data': {
                'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
                'datasets': [{
                    'label': 'Revenue Pattern',
                    'data': [85, 100, 120, 90],  # Example seasonal factors
                    'borderColor': self.chart_colors['success'],
                    'backgroundColor': 'rgba(247, 143, 1, 0.2)',
                    'pointBackgroundColor': self.chart_colors['success']
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Seasonal Revenue Patterns'
                    }
                }
            }
        }
    
    def create_category_revenue_chart(self, category_data: Dict) -> Dict:
        """Create category revenue breakdown chart"""
        return {
            'type': 'pie',
            'title': 'Revenue by Equipment Category',
            'data': {
                'labels': list(category_data.keys())[:6],  # Top 6 categories
                'datasets': [{
                    'data': [sum(cat_data.get('forecast_values', [0])) for cat_data in list(category_data.values())[:6]],
                    'backgroundColor': [
                        self.chart_colors['primary'],
                        self.chart_colors['secondary'],
                        self.chart_colors['success'],
                        self.chart_colors['warning'],
                        self.chart_colors['info'],
                        self.chart_colors['dark']
                    ]
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Predicted Revenue by Category'
                    }
                }
            }
        }
    
    def create_recommendations_chart(self, utilization_data: Dict) -> Dict:
        """Create utilization recommendations chart"""
        return {
            'type': 'horizontalBar',
            'title': 'Utilization Optimization Recommendations',
            'data': {
                'labels': ['Rebalance Equipment', 'Increase Marketing', 'Seasonal Adjustment', 'Capacity Optimization'],
                'datasets': [{
                    'label': 'Potential Impact (%)',
                    'data': [25, 15, 30, 20],  # Example impact values
                    'backgroundColor': self.chart_colors['warning']
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Optimization Recommendations'
                    }
                },
                'scales': {
                    'x': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Impact (%)'
                        }
                    }
                }
            }
        }
    
    # Utility methods
    
    def generate_weather_demand_data(self) -> List[Dict]:
        """Generate sample weather vs demand data"""
        data_points = []
        for temp in range(20, 100, 5):
            # Simulate relationship between temperature and demand
            demand = 50 + (temp - 60) * 0.3 + np.random.normal(0, 5)
            data_points.append({'x': temp, 'y': max(0, demand)})
        return data_points
    
    def generate_time_labels(self, days: int) -> List[str]:
        """Generate time labels for the last N days"""
        dates = []
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            dates.append(date.strftime('%m/%d'))
        return dates
    
    def generate_performance_data(self, days: int) -> List[float]:
        """Generate sample performance data"""
        return [85 + np.random.normal(0, 5) for _ in range(days)]
    
    def generate_quality_data(self, days: int) -> List[float]:
        """Generate sample quality data"""
        return [75 + np.random.normal(0, 3) for _ in range(days)]
    
    def calculate_overall_risk_score(self, alert_data: Dict) -> float:
        """Calculate overall risk score from alert data"""
        risk_factors = [
            len(alert_data.get('demand_risks', [])) * 10,
            len(alert_data.get('inventory_warnings', [])) * 15,
            len(alert_data.get('operational_risks', [])) * 20,
            len(alert_data.get('competitive_threats', [])) * 25
        ]
        return min(100, sum(risk_factors))
    
    def get_risk_color(self, score: float) -> str:
        """Get color based on risk score"""
        if score < 30:
            return '#28A745'  # Green
        elif score < 70:
            return '#FFC107'  # Yellow
        else:
            return '#DC3545'  # Red
    
    def get_quality_color(self, score: float) -> str:
        """Get color based on quality score"""
        if score >= 90:
            return '#17A2B8'  # Blue
        elif score >= 75:
            return '#28A745'  # Green
        elif score >= 50:
            return '#FFC107'  # Yellow
        else:
            return '#DC3545'  # Red
    
    def get_drift_color(self, drift_score: float) -> str:
        """Get color based on model drift score"""
        if drift_score < 0.1:
            return '#28A745'  # Green - Low drift
        elif drift_score < 0.3:
            return '#FFC107'  # Yellow - Medium drift
        else:
            return '#DC3545'  # Red - High drift
    
    def get_model_improvement_recommendations(self, performance_data: Dict) -> List[str]:
        """Generate model improvement recommendations"""
        recommendations = []
        
        accuracy = performance_data.get('forecast_accuracy', {}).get('overall_accuracy', 0)
        if accuracy < 80:
            recommendations.append("Consider adding more historical data to improve forecast accuracy")
        
        drift_data = performance_data.get('model_drift_detection', {})
        if any(drift > 0.2 for drift in drift_data.values() if isinstance(drift, (int, float))):
            recommendations.append("Retrain models showing high drift indicators")
        
        quality_impact = performance_data.get('data_quality_impact', {})
        if quality_impact.get('rfid_coverage_impact', 0) > 0.3:
            recommendations.append("Increase RFID tagging to improve prediction accuracy")
        
        return recommendations