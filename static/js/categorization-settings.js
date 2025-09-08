/**
 * Equipment Categorization Settings
 * JavaScript for managing categorization thresholds, ratios, and keywords
 */

class CategorizationSettings {
    constructor() {
        this.settings = {};
        this.charts = {};
        this.currentStats = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.loadStatistics();
    }
    
    setupEventListeners() {
        // Threshold sliders
        document.getElementById('high-confidence-threshold').addEventListener('input', (e) => {
            document.getElementById('high-confidence-value').textContent = e.target.value;
            this.updateThresholdPreview();
        });
        
        document.getElementById('medium-confidence-threshold').addEventListener('input', (e) => {
            document.getElementById('medium-confidence-value').textContent = e.target.value;
            this.updateThresholdPreview();
        });
        
        document.getElementById('review-threshold').addEventListener('input', (e) => {
            document.getElementById('review-threshold-value').textContent = e.target.value;
            this.updateThresholdPreview();
        });
        
        // Ratio sliders
        document.getElementById('party-ratio-target').addEventListener('input', (e) => {
            document.getElementById('party-target-value').textContent = e.target.value + '%';
            this.updateRatioChart();
        });
        
        document.getElementById('construction-ratio-target').addEventListener('input', (e) => {
            document.getElementById('construction-target-value').textContent = e.target.value + '%';
            this.updateRatioChart();
        });
        
        document.getElementById('landscaping-ratio-target').addEventListener('input', (e) => {
            document.getElementById('landscaping-target-value').textContent = e.target.value + '%';
            this.updateRatioChart();
        });
        
        document.getElementById('mixed-ratio-target').addEventListener('input', (e) => {
            document.getElementById('mixed-target-value').textContent = e.target.value + '%';
            this.updateRatioChart();
        });
        
        // Action buttons
        document.getElementById('save-thresholds').addEventListener('click', () => this.saveThresholds());
        document.getElementById('reset-thresholds').addEventListener('click', () => this.resetThresholds());
        document.getElementById('save-ratios').addEventListener('click', () => this.saveRatios());
        document.getElementById('save-methods').addEventListener('click', () => this.saveMethods());
        document.getElementById('run-categorization').addEventListener('click', () => this.runCategorization());
        
        // Keyword management
        document.getElementById('add-party-keyword').addEventListener('click', () => 
            this.addKeyword('party', document.getElementById('new-party-keyword').value));
        document.getElementById('add-construction-keyword').addEventListener('click', () => 
            this.addKeyword('construction', document.getElementById('new-construction-keyword').value));
        document.getElementById('add-landscaping-keyword').addEventListener('click', () => 
            this.addKeyword('landscaping', document.getElementById('new-landscaping-keyword').value));
        
        // Enter key support for keyword inputs
        ['new-party-keyword', 'new-construction-keyword', 'new-landscaping-keyword'].forEach(id => {
            document.getElementById(id).addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const category = id.split('-')[1];
                    this.addKeyword(category, e.target.value);
                }
            });
        });
        
        // Tab change events
        document.querySelectorAll('[data-bs-toggle="pill"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetTab = e.target.getAttribute('data-bs-target').replace('#', '');
                this.handleTabChange(targetTab);
            });
        });
    }
    
    async loadSettings() {
        try {
            const response = await fetch('/api/minnesota-weather/categorization-settings');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.settings = data.settings;
                this.updateSettingsUI();
                this.loadKeywords();
            } else {
                this.showAlert('error', 'Failed to load settings: ' + data.error);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showAlert('error', 'Failed to load settings');
        }
    }
    
    async loadStatistics() {
        try {
            // Load current categorization statistics
            const response = await fetch('/api/minnesota-weather/equipment-categorization');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentStats = data.categorization_data;
                this.updateStatisticsUI();
            }
        } catch (error) {
            console.error('Failed to load statistics:', error);
        }
    }
    
    updateSettingsUI() {
        if (!this.settings.confidence_thresholds) return;
        
        const thresholds = this.settings.confidence_thresholds;
        
        // Update threshold sliders
        document.getElementById('high-confidence-threshold').value = thresholds.high_confidence;
        document.getElementById('high-confidence-value').textContent = thresholds.high_confidence;
        
        document.getElementById('medium-confidence-threshold').value = thresholds.medium_confidence;
        document.getElementById('medium-confidence-value').textContent = thresholds.medium_confidence;
        
        document.getElementById('review-threshold').value = thresholds.review_required;
        document.getElementById('review-threshold-value').textContent = thresholds.review_required;
        
        // Update ratio settings if available
        if (this.settings.industry_ratios) {
            const ratios = this.settings.industry_ratios;
            
            Object.entries(ratios).forEach(([segment, data]) => {
                const targetRatio = data.target_ratio * 100;
                const currentRatio = data.current_ratio * 100;
                
                const sliderElement = document.getElementById(`${segment.replace('_', '-')}-ratio-target`);
                const currentElement = document.getElementById(`${segment.replace('_', '-')}-current`);
                
                if (sliderElement) {
                    sliderElement.value = targetRatio;
                    document.getElementById(`${segment.replace('_', '-')}-target-value`).textContent = 
                        targetRatio + '%';
                }
                
                if (currentElement) {
                    currentElement.textContent = currentRatio.toFixed(1) + '%';
                }
            });
        }
        
        this.updateThresholdPreview();
        this.updateRatioChart();
    }
    
    updateStatisticsUI() {
        if (!this.currentStats) return;
        
        // Update overview statistics
        let totalItems = 0;
        let categorizedItems = 0;
        let avgConfidence = 0;
        let needsReview = 0;
        
        if (this.currentStats.industry_breakdown) {
            this.currentStats.industry_breakdown.forEach(segment => {
                totalItems += segment.item_count;
                categorizedItems += segment.item_count;
                avgConfidence += segment.avg_confidence * segment.item_count;
            });
            
            if (totalItems > 0) {
                avgConfidence = (avgConfidence / totalItems) * 100;
            }
        }
        
        document.getElementById('total-items').textContent = totalItems.toLocaleString();
        document.getElementById('categorized-items').textContent = categorizedItems.toLocaleString();
        document.getElementById('avg-confidence').textContent = avgConfidence.toFixed(0) + '%';
        document.getElementById('needs-review').textContent = needsReview.toLocaleString();
        
        // Update charts
        this.updateCategorizationStatsChart();
    }
    
    loadKeywords() {
        if (!this.settings.keywords) return;
        
        Object.entries(this.settings.keywords).forEach(([category, keywords]) => {
            const containerId = `${category.replace('_', '-')}-keywords`;
            const container = document.getElementById(containerId);
            
            if (container) {
                container.innerHTML = '';
                
                Object.entries(keywords).forEach(([subcategory, keywordList]) => {
                    keywordList.forEach(keyword => {
                        const keywordTag = this.createKeywordTag(keyword, category, subcategory);
                        container.appendChild(keywordTag);
                    });
                });
            }
        });
    }
    
    createKeywordTag(keyword, category, subcategory) {
        const tag = document.createElement('span');
        tag.className = 'keyword-tag';
        tag.innerHTML = `
            ${keyword}
            <i class="bi bi-x-circle ms-1" style="cursor: pointer;" 
               onclick="categorizationSettings.removeKeyword('${category}', '${subcategory}', '${keyword}')"></i>
        `;
        return tag;
    }
    
    addKeyword(category, keyword) {
        if (!keyword.trim()) return;
        
        // Add to UI immediately
        const containerId = `${category}-keywords`;
        const container = document.getElementById(containerId);
        const inputId = `new-${category}-keyword`;
        const input = document.getElementById(inputId);
        
        if (container && input) {
            const keywordTag = this.createKeywordTag(keyword, category, 'general');
            container.appendChild(keywordTag);
            input.value = '';
            
            this.showAlert('success', `Added keyword "${keyword}" to ${category} category`);
        }
    }
    
    removeKeyword(category, subcategory, keyword) {
        // Remove from UI
        const tags = document.querySelectorAll('.keyword-tag');
        tags.forEach(tag => {
            if (tag.textContent.trim().startsWith(keyword)) {
                tag.remove();
            }
        });
        
        this.showAlert('info', `Removed keyword "${keyword}" from ${category} category`);
    }
    
    updateThresholdPreview() {
        const highThreshold = parseFloat(document.getElementById('high-confidence-threshold').value);
        const mediumThreshold = parseFloat(document.getElementById('medium-confidence-threshold').value);
        const reviewThreshold = parseFloat(document.getElementById('review-threshold').value);
        
        // Simulate impact based on thresholds
        // In a real implementation, this would query the database
        const totalItems = 1000; // Example total
        const autoCount = Math.round(totalItems * 0.6 * (1 - highThreshold));
        const approvalCount = Math.round(totalItems * 0.25 * (highThreshold - mediumThreshold));
        const reviewCount = Math.round(totalItems * 0.15 * (1 - reviewThreshold));
        
        document.getElementById('auto-count').textContent = autoCount;
        document.getElementById('approval-count').textContent = approvalCount;
        document.getElementById('review-count').textContent = reviewCount;
        
        this.updateThresholdImpactChart(autoCount, approvalCount, reviewCount);
    }
    
    updateThresholdImpactChart(autoCount, approvalCount, reviewCount) {
        const ctx = document.getElementById('threshold-impact-chart').getContext('2d');
        
        if (this.charts.thresholdImpact) {
            this.charts.thresholdImpact.destroy();
        }
        
        this.charts.thresholdImpact = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Auto-categorized', 'Needs Approval', 'Needs Review'],
                datasets: [{
                    data: [autoCount, approvalCount, reviewCount],
                    backgroundColor: ['#00b894', '#fdcb6e', '#e17055']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    updateRatioChart() {
        const partyTarget = parseInt(document.getElementById('party-ratio-target').value);
        const constructionTarget = parseInt(document.getElementById('construction-ratio-target').value);
        const landscapingTarget = parseInt(document.getElementById('landscaping-ratio-target').value);
        const mixedTarget = parseInt(document.getElementById('mixed-ratio-target').value);
        
        // Get current values from statistics
        let partyCurrent = 0, constructionCurrent = 0, landscapingCurrent = 0, mixedCurrent = 0;
        
        if (this.currentStats && this.currentStats.industry_breakdown) {
            this.currentStats.industry_breakdown.forEach(segment => {
                switch (segment.industry_segment) {
                    case 'party_event':
                        partyCurrent = segment.revenue_percentage;
                        break;
                    case 'construction_diy':
                        constructionCurrent = segment.revenue_percentage;
                        break;
                    case 'landscaping':
                        landscapingCurrent = segment.revenue_percentage;
                        break;
                    case 'mixed':
                        mixedCurrent = segment.revenue_percentage;
                        break;
                }
            });
        }
        
        const ctx = document.getElementById('ratio-comparison-chart').getContext('2d');
        
        if (this.charts.ratioComparison) {
            this.charts.ratioComparison.destroy();
        }
        
        this.charts.ratioComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Party/Event', 'Construction/DIY', 'Landscaping', 'Mixed'],
                datasets: [{
                    label: 'Current %',
                    data: [partyCurrent, constructionCurrent, landscapingCurrent, mixedCurrent],
                    backgroundColor: 'rgba(116, 185, 255, 0.6)'
                }, {
                    label: 'Target %',
                    data: [partyTarget, constructionTarget, landscapingTarget, mixedTarget],
                    backgroundColor: 'rgba(253, 203, 110, 0.6)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Percentage (%)'
                        }
                    }
                }
            }
        });
        
        this.updateRatioRecommendations(
            [partyCurrent, constructionCurrent, landscapingCurrent, mixedCurrent],
            [partyTarget, constructionTarget, landscapingTarget, mixedTarget]
        );
    }
    
    updateRatioRecommendations(current, target) {
        const categories = ['Party/Event', 'Construction/DIY', 'Landscaping', 'Mixed'];
        const recommendations = [];
        
        current.forEach((currentVal, index) => {
            const targetVal = target[index];
            const difference = Math.abs(currentVal - targetVal);
            
            if (difference > 5) {
                if (currentVal < targetVal) {
                    recommendations.push(`Increase ${categories[index]} inventory by ${difference.toFixed(1)}%`);
                } else {
                    recommendations.push(`Decrease ${categories[index]} inventory by ${difference.toFixed(1)}%`);
                }
            }
        });
        
        if (recommendations.length === 0) {
            recommendations.push('Current distribution is close to targets');
        }
        
        const list = document.getElementById('ratio-rec-list');
        list.innerHTML = '';
        recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.textContent = rec;
            list.appendChild(li);
        });
    }
    
    updateCategorizationStatsChart() {
        const ctx = document.getElementById('categorization-stats-chart').getContext('2d');
        
        if (this.charts.categorizationStats) {
            this.charts.categorizationStats.destroy();
        }
        
        if (!this.currentStats || !this.currentStats.industry_breakdown) return;
        
        const labels = this.currentStats.industry_breakdown.map(segment => 
            this.formatSegmentName(segment.industry_segment));
        const itemCounts = this.currentStats.industry_breakdown.map(segment => segment.item_count);
        const revenues = this.currentStats.industry_breakdown.map(segment => segment.ytd_revenue);
        
        this.charts.categorizationStats = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Item Count',
                    data: itemCounts,
                    backgroundColor: 'rgba(116, 185, 255, 0.8)',
                    yAxisID: 'y'
                }, {
                    label: 'YTD Revenue ($)',
                    data: revenues,
                    backgroundColor: 'rgba(253, 203, 110, 0.8)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Item Count'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Revenue ($)'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    handleTabChange(tabName) {
        // Handle any tab-specific initialization
        switch (tabName) {
            case 'results':
                this.loadCategorizationResults();
                break;
        }
    }
    
    async loadCategorizationResults() {
        // Load any previous categorization results
        // This would typically come from a database or API
    }
    
    async saveThresholds() {
        const thresholds = {
            high_confidence: parseFloat(document.getElementById('high-confidence-threshold').value),
            medium_confidence: parseFloat(document.getElementById('medium-confidence-threshold').value),
            review_required: parseFloat(document.getElementById('review-threshold').value)
        };
        
        try {
            // In a real implementation, this would POST to an API endpoint
            this.showAlert('success', 'Confidence thresholds saved successfully');
        } catch (error) {
            this.showAlert('error', 'Failed to save thresholds');
        }
    }
    
    resetThresholds() {
        document.getElementById('high-confidence-threshold').value = 0.8;
        document.getElementById('high-confidence-value').textContent = '0.8';
        
        document.getElementById('medium-confidence-threshold').value = 0.6;
        document.getElementById('medium-confidence-value').textContent = '0.6';
        
        document.getElementById('review-threshold').value = 0.4;
        document.getElementById('review-threshold-value').textContent = '0.4';
        
        this.updateThresholdPreview();
        this.showAlert('info', 'Thresholds reset to defaults');
    }
    
    async saveRatios() {
        const ratios = {
            party_event: parseInt(document.getElementById('party-ratio-target').value) / 100,
            construction_diy: parseInt(document.getElementById('construction-ratio-target').value) / 100,
            landscaping: parseInt(document.getElementById('landscaping-ratio-target').value) / 100,
            mixed: parseInt(document.getElementById('mixed-ratio-target').value) / 100
        };
        
        try {
            // In a real implementation, this would POST to an API endpoint
            this.showAlert('success', 'Target ratios saved successfully');
        } catch (error) {
            this.showAlert('error', 'Failed to save ratios');
        }
    }
    
    async saveMethods() {
        const methods = {
            keyword_match: document.getElementById('keyword-match').checked,
            ml_classification: document.getElementById('ml-classification').checked,
            manual_override: document.getElementById('manual-override').checked,
            rule_based: document.getElementById('rule-based').checked
        };
        
        try {
            // In a real implementation, this would POST to an API endpoint
            this.showAlert('success', 'Classification methods saved successfully');
        } catch (error) {
            this.showAlert('error', 'Failed to save methods');
        }
    }
    
    async runCategorization() {
        const batchSize = parseInt(document.getElementById('batch-size').value);
        const overwriteExisting = document.getElementById('overwrite-existing').checked;
        
        // Show loading overlay
        document.getElementById('loading-overlay').style.display = 'flex';
        
        // Show progress section
        const progressSection = document.getElementById('categorization-progress');
        progressSection.classList.remove('d-none');
        
        try {
            const response = await fetch('/api/minnesota-weather/categorize-equipment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    batch_size: batchSize,
                    overwrite_existing: overwriteExisting
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayCategorizationResults(data.categorization_results);
                this.showAlert('success', 'Equipment categorization completed successfully');
                await this.loadStatistics(); // Refresh statistics
            } else {
                this.showAlert('error', 'Categorization failed: ' + data.error);
            }
        } catch (error) {
            console.error('Categorization failed:', error);
            this.showAlert('error', 'Categorization failed');
        } finally {
            // Hide loading overlay
            document.getElementById('loading-overlay').style.display = 'none';
            progressSection.classList.add('d-none');
        }
    }
    
    displayCategorizationResults(results) {
        const container = document.getElementById('categorization-results');
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <strong>Total Items Processed:</strong>
                        <span class="badge bg-primary ms-2">${results.total_items}</span>
                    </div>
                    <div class="mb-3">
                        <strong>Successfully Categorized:</strong>
                        <span class="badge bg-success ms-2">${results.categorized}</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <strong>Processing Errors:</strong>
                        <span class="badge bg-danger ms-2">${results.processing_errors || 0}</span>
                    </div>
                    <div class="mb-3">
                        <strong>Success Rate:</strong>
                        <span class="badge bg-info ms-2">${((results.categorized / results.total_items) * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
            
            <h6 class="mt-4">Category Breakdown:</h6>
            <div class="row">
                ${Object.entries(results.categories || {}).map(([category, count]) => `
                    <div class="col-md-3 mb-2">
                        <div class="d-flex justify-content-between">
                            <span class="category-badge category-${category.replace('_', '-')}">${this.formatSegmentName(category)}</span>
                            <strong>${count}</strong>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    formatSegmentName(segment) {
        const names = {
            'party_event': 'Party/Event',
            'construction_diy': 'Construction/DIY',
            'landscaping': 'Landscaping',
            'mixed': 'Mixed',
            'uncategorized': 'Uncategorized'
        };
        return names[segment] || segment;
    }
    
    showAlert(type, message) {
        const alertContainer = document.getElementById('alert-container');
        const alertClass = type === 'error' ? 'danger' : type;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${alertClass} alert-dismissible fade show alert-custom`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize settings when DOM is loaded
let categorizationSettings;
document.addEventListener('DOMContentLoaded', () => {
    categorizationSettings = new CategorizationSettings();
});