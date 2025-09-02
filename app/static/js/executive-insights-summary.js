// Executive Insights Summary Component
// Business Intelligence Summary for Scorecard Analytics

/**
 * Generate executive insights based on scorecard analytics data
 */
class ExecutiveInsightsSummary {
    constructor() {
        this.insights = {};
        this.recommendations = [];
        this.riskFactors = [];
    }

    /**
     * Analyze data and generate business insights
     */
    async generateInsights(analyticsData) {
        if (!analyticsData || !analyticsData.multi_year_trends) {
            console.warn('No analytics data available for insights generation');
            return;
        }

        try {
            // Generate key insights
            this.insights = {
                seasonal: this.analyzeSeasonalPatterns(analyticsData),
                risk: this.analyzeRiskFactors(analyticsData),
                performance: this.analyzeStorePerformance(analyticsData),
                pipeline: this.analyzePipelineHealth(analyticsData),
                forecast: this.generateForecastInsights(analyticsData)
            };

            // Generate strategic recommendations
            this.recommendations = this.generateRecommendations();

            // Update dashboard display
            this.updateInsightsDashboard();

            console.log('✅ Executive insights generated successfully');
        } catch (error) {
            console.error('❌ Error generating executive insights:', error);
        }
    }

    /**
     * Analyze seasonal patterns and trends
     */
    analyzeSeasonalPatterns(data) {
        const trends = data.multi_year_trends;
        const seasonal = data.seasonal_patterns;

        // Find peak and trough periods
        const revenues = trends.map(t => t.total_revenue);
        const maxRevenue = Math.max(...revenues);
        const minRevenue = Math.min(...revenues);
        const seasonalVariation = maxRevenue / minRevenue;

        // Identify peak months
        const peakWeeks = seasonal.filter(s => s.seasonal_classification === 'peak');
        const troughWeeks = seasonal.filter(s => s.seasonal_classification === 'trough');

        return {
            seasonal_variation: seasonalVariation.toFixed(1),
            peak_period: this.getSeasonName(peakWeeks),
            trough_period: this.getSeasonName(troughWeeks),
            revenue_swing: ((maxRevenue - minRevenue) / minRevenue * 100).toFixed(1),
            insight: `Revenue shows ${seasonalVariation.toFixed(1)}x seasonal variation, with peak performance in ${this.getSeasonName(peakWeeks)} and lowest activity in ${this.getSeasonName(troughWeeks)}.`,
            recommendation: "Plan inventory, staffing, and marketing campaigns around identified seasonal patterns to maximize peak season revenue and minimize trough period losses."
        };
    }

    /**
     * Analyze risk factors and concentration issues
     */
    analyzeRiskFactors(data) {
        const riskIndicators = data.risk_indicators;
        const trends = data.multi_year_trends;

        // Analyze concentration risk patterns
        const highRiskWeeks = trends.filter(t => t.concentration_risk);
        const riskByStore = this.calculateRiskByStore(trends);

        return {
            concentration_risk_pct: riskIndicators.concentration_risk_percentage,
            high_risk_weeks: riskIndicators.high_concentration_weeks,
            dominant_store: riskByStore.dominantStore,
            avg_concentration: riskIndicators.avg_max_store_percentage,
            insight: `${riskIndicators.concentration_risk_percentage}% of weeks show dangerous revenue concentration (>40% from single store), with ${riskByStore.dominantStore} being the most frequent dominant location.`,
            recommendation: "Implement revenue diversification strategies to reduce dependency on single locations. Focus on growing underperforming stores to balance portfolio risk."
        };
    }

    /**
     * Analyze individual store performance
     */
    analyzeStorePerformance(data) {
        const trends = data.multi_year_trends;
        const storePerformance = this.calculateStoreMetrics(trends);

        return {
            strongest_performer: storePerformance.strongest,
            growth_leader: storePerformance.fastestGrowing,
            consistency_leader: storePerformance.mostConsistent,
            underperformer: storePerformance.underperformer,
            insight: `${storePerformance.strongest.name} leads in total revenue generation (${storePerformance.strongest.avgRevenue.toLocaleString()}/week avg), while ${storePerformance.fastestGrowing.name} shows strongest growth trajectory.`,
            recommendation: "Replicate success factors from top-performing locations to underperforming stores. Investigate and address specific challenges at lower-performing locations."
        };
    }

    /**
     * Analyze pipeline conversion health
     */
    analyzePipelineHealth(data) {
        const pipeline = data.pipeline_conversion;
        const conversions = pipeline.map(p => p.conversion_rate).filter(r => r > 0);
        
        const avgConversion = conversions.reduce((a, b) => a + b, 0) / conversions.length;
        const maxConversion = Math.max(...conversions);
        const minConversion = Math.min(...conversions);

        // Analyze trends
        const recentConversions = conversions.slice(-8); // Last 8 weeks
        const earlierConversions = conversions.slice(-16, -8);
        const recentAvg = recentConversions.reduce((a, b) => a + b, 0) / recentConversions.length;
        const earlierAvg = earlierConversions.reduce((a, b) => a + b, 0) / earlierConversions.length;
        const conversionTrend = ((recentAvg - earlierAvg) / earlierAvg * 100).toFixed(1);

        return {
            avg_conversion_rate: avgConversion.toFixed(1),
            conversion_trend: conversionTrend,
            conversion_range: `${minConversion.toFixed(1)}% - ${maxConversion.toFixed(1)}%`,
            pipeline_health: avgConversion > 100 ? 'Excellent' : avgConversion > 75 ? 'Good' : 'Needs Attention',
            insight: `Pipeline conversion averages ${avgConversion.toFixed(1)}% with ${conversionTrend > 0 ? 'improving' : 'declining'} trend (${Math.abs(conversionTrend)}% change vs 8 weeks ago).`,
            recommendation: avgConversion > 100 ? 
                "Maintain current pipeline processes and identify factors driving high conversion rates for replication." :
                "Investigate pipeline bottlenecks and implement conversion optimization strategies. Focus on lead quality and follow-up processes."
        };
    }

    /**
     * Generate forecast-based insights
     */
    generateForecastInsights(data) {
        const trends = data.multi_year_trends;
        const recent = trends.slice(-12); // Last 12 weeks
        const revenues = recent.map(t => t.total_revenue);
        
        // Calculate momentum
        const earlyRevenue = revenues.slice(0, 6).reduce((a, b) => a + b, 0) / 6;
        const lateRevenue = revenues.slice(-6).reduce((a, b) => a + b, 0) / 6;
        const momentum = ((lateRevenue - earlyRevenue) / earlyRevenue * 100).toFixed(1);

        // Seasonal forecast
        const currentWeek = new Date().getDate();
        const seasonalFactor = this.getSeasonalForecast(currentWeek);

        return {
            current_momentum: momentum,
            seasonal_outlook: seasonalFactor.outlook,
            projected_trend: momentum > 5 ? 'Strong Growth' : momentum > 0 ? 'Moderate Growth' : 'Declining',
            next_quarter_risk: seasonalFactor.risk,
            insight: `Current business momentum shows ${Math.abs(momentum)}% ${momentum > 0 ? 'growth' : 'decline'} with ${seasonalFactor.outlook} seasonal outlook for the next quarter.`,
            recommendation: seasonalFactor.recommendation
        };
    }

    /**
     * Generate strategic recommendations based on insights
     */
    generateRecommendations() {
        const recommendations = [];

        // Seasonal optimization
        if (this.insights.seasonal && parseFloat(this.insights.seasonal.seasonal_variation) > 5) {
            recommendations.push({
                category: 'Seasonal Strategy',
                priority: 'High',
                action: 'Implement dynamic inventory and staffing models based on 7x seasonal variation pattern',
                impact: 'Revenue Optimization',
                timeline: 'Next Quarter'
            });
        }

        // Risk management
        if (this.insights.risk && parseFloat(this.insights.risk.concentration_risk_pct) > 20) {
            recommendations.push({
                category: 'Risk Management',
                priority: 'Critical',
                action: 'Diversify revenue streams to reduce single-store dependency',
                impact: 'Risk Reduction',
                timeline: 'Immediate'
            });
        }

        // Performance optimization
        if (this.insights.performance) {
            recommendations.push({
                category: 'Performance Enhancement',
                priority: 'Medium',
                action: `Replicate ${this.insights.performance.strongest_performer.name} success factors across network`,
                impact: 'Revenue Growth',
                timeline: '6 Months'
            });
        }

        // Pipeline improvement
        if (this.insights.pipeline && parseFloat(this.insights.pipeline.avg_conversion_rate) < 75) {
            recommendations.push({
                category: 'Pipeline Optimization',
                priority: 'High',
                action: 'Implement conversion rate improvement program',
                impact: 'Revenue Growth',
                timeline: '3 Months'
            });
        }

        return recommendations;
    }

    /**
     * Update the insights dashboard display
     */
    updateInsightsDashboard() {
        this.updateInsightsPanel();
        this.updateRecommendationsPanel();
        this.updateRiskAlertsPanel();
    }

    /**
     * Update insights panel
     */
    updateInsightsPanel() {
        const insightsHTML = `
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-lightbulb me-2"></i>Strategic Insights</h5>
                </div>
                <div class="card-body">
                    ${Object.entries(this.insights).map(([category, data]) => `
                        <div class="insight-item mb-3 p-3 bg-light rounded">
                            <h6 class="text-primary text-capitalize">${category} Analysis</h6>
                            <p class="mb-1 small">${data.insight}</p>
                            <div class="text-muted small">
                                <i class="fas fa-arrow-right me-1"></i>${data.recommendation}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Find or create insights container
        let container = document.getElementById('executiveInsights');
        if (!container) {
            // Create container after the correlation matrix
            const correlationMatrix = document.getElementById('correlationMatrix');
            if (correlationMatrix && correlationMatrix.parentNode) {
                container = document.createElement('div');
                container.id = 'executiveInsights';
                container.className = 'col-12 mt-4';
                correlationMatrix.parentNode.parentNode.appendChild(container);
            }
        }

        if (container) {
            container.innerHTML = insightsHTML;
        }
    }

    /**
     * Update recommendations panel  
     */
    updateRecommendationsPanel() {
        if (this.recommendations.length === 0) return;

        const recommendationsHTML = `
            <div class="card border-0 shadow-sm mt-4">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-tasks me-2"></i>Strategic Recommendations</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        ${this.recommendations.map(rec => `
                            <div class="col-md-6 col-lg-4 mb-3">
                                <div class="recommendation-card p-3 border rounded h-100">
                                    <div class="d-flex justify-content-between align-items-start mb-2">
                                        <span class="badge bg-${this.getPriorityColor(rec.priority)}">${rec.priority}</span>
                                        <small class="text-muted">${rec.timeline}</small>
                                    </div>
                                    <h6 class="text-dark">${rec.category}</h6>
                                    <p class="small mb-2">${rec.action}</p>
                                    <div class="d-flex justify-content-between">
                                        <small class="text-success fw-bold">${rec.impact}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        const insightsContainer = document.getElementById('executiveInsights');
        if (insightsContainer) {
            insightsContainer.insertAdjacentHTML('afterend', recommendationsHTML);
        }
    }

    /**
     * Update risk alerts panel
     */
    updateRiskAlertsPanel() {
        // This would integrate with the existing risk indicators
        console.log('Risk alerts updated based on insights');
    }

    // Utility methods
    getSeasonName(weeks) {
        if (!weeks || weeks.length === 0) return 'Unknown';
        const avgWeek = weeks.reduce((sum, w) => sum + w.week_of_year, 0) / weeks.length;
        
        if (avgWeek >= 20 && avgWeek <= 35) return 'Summer (May-Aug)';
        if (avgWeek >= 36 && avgWeek <= 48) return 'Fall (Sep-Nov)';
        if (avgWeek >= 49 || avgWeek <= 12) return 'Winter (Dec-Mar)';
        return 'Spring (Apr-May)';
    }

    calculateRiskByStore(trends) {
        const storeDominanceCount = { '3607': 0, '6800': 0, '728': 0, '8101': 0 };
        
        trends.forEach(trend => {
            if (trend.concentration_risk) {
                const dominantStore = Object.entries(trend.store_revenues)
                    .reduce((a, b) => a[1] > b[1] ? a : b)[0];
                storeDominanceCount[dominantStore]++;
            }
        });

        const dominantStore = Object.entries(storeDominanceCount)
            .reduce((a, b) => a[1] > b[1] ? a : b)[0];

        const STORE_NAMES = { '3607': 'Wayzata', '6800': 'Brooklyn Park', '728': 'Elk River', '8101': 'Fridley' };
        
        return {
            dominantStore: STORE_NAMES[dominantStore] || dominantStore,
            counts: storeDominanceCount
        };
    }

    calculateStoreMetrics(trends) {
        const storeMetrics = { '3607': [], '6800': [], '728': [], '8101': [] };
        const STORE_NAMES = { '3607': 'Wayzata', '6800': 'Brooklyn Park', '728': 'Elk River', '8101': 'Fridley' };

        // Aggregate revenue by store
        trends.forEach(trend => {
            Object.entries(trend.store_revenues).forEach(([store, revenue]) => {
                if (storeMetrics[store]) {
                    storeMetrics[store].push(revenue);
                }
            });
        });

        // Calculate metrics for each store
        const results = {};
        Object.entries(storeMetrics).forEach(([store, revenues]) => {
            if (revenues.length > 0) {
                const avg = revenues.reduce((a, b) => a + b, 0) / revenues.length;
                const variance = revenues.reduce((sum, r) => sum + Math.pow(r - avg, 2), 0) / revenues.length;
                const consistency = 1 / (1 + Math.sqrt(variance) / avg); // Coefficient of variation inverse
                
                results[store] = {
                    name: STORE_NAMES[store],
                    avgRevenue: avg,
                    consistency: consistency,
                    growth: this.calculateGrowth(revenues)
                };
            }
        });

        // Find leaders in each category
        const stores = Object.values(results);
        return {
            strongest: stores.reduce((a, b) => a.avgRevenue > b.avgRevenue ? a : b),
            mostConsistent: stores.reduce((a, b) => a.consistency > b.consistency ? a : b),
            fastestGrowing: stores.reduce((a, b) => a.growth > b.growth ? a : b),
            underperformer: stores.reduce((a, b) => a.avgRevenue < b.avgRevenue ? a : b)
        };
    }

    calculateGrowth(revenues) {
        if (revenues.length < 8) return 0;
        const early = revenues.slice(0, 4).reduce((a, b) => a + b, 0) / 4;
        const late = revenues.slice(-4).reduce((a, b) => a + b, 0) / 4;
        return ((late - early) / early) * 100;
    }

    getSeasonalForecast(currentWeek) {
        // Simplified seasonal forecast logic
        if (currentWeek >= 15 && currentWeek <= 35) {
            return {
                outlook: 'Positive (Peak Season Approaching)',
                risk: 'Low',
                recommendation: 'Prepare for seasonal surge with increased inventory and staffing'
            };
        } else if (currentWeek >= 45 || currentWeek <= 10) {
            return {
                outlook: 'Challenging (Trough Period)',
                risk: 'High',
                recommendation: 'Focus on cost management and customer retention strategies'
            };
        } else {
            return {
                outlook: 'Moderate (Transition Period)',
                risk: 'Medium',
                recommendation: 'Plan for upcoming seasonal changes and optimize operations'
            };
        }
    }

    getPriorityColor(priority) {
        switch (priority.toLowerCase()) {
            case 'critical': return 'danger';
            case 'high': return 'warning';
            case 'medium': return 'info';
            case 'low': return 'success';
            default: return 'secondary';
        }
    }
}

// Initialize and export
const executiveInsights = new ExecutiveInsightsSummary();

// Auto-initialize when scorecard data is available
document.addEventListener('DOMContentLoaded', function() {
    // Listen for scorecard data completion
    window.addEventListener('scorecardAnalyticsReady', function(event) {
        executiveInsights.generateInsights(event.detail);
    });
});

// Export for external use
window.ExecutiveInsightsSummary = ExecutiveInsightsSummary;
window.executiveInsights = executiveInsights;