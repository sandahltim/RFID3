/**
 * User Feedback System - JavaScript Module
 * Handles all user feedback interactions for predictive analytics correlations
 */

class FeedbackSystem {
    constructor() {
        this.baseUrl = '/api/feedback';
        this.currentUser = this.getCurrentUser();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadFeedbackComponents();
    }

    getCurrentUser() {
        // In a real implementation, this would get user from authentication
        return {
            user_id: 'demo_user_' + Math.random().toString(36).substr(2, 9),
            user_name: 'Demo User',
            user_role: 'Store Manager'
        };
    }

    setupEventListeners() {
        // Global event listeners for feedback components
        document.addEventListener('click', (e) => {
            if (e.target.matches('.feedback-submit-btn')) {
                this.handleFeedbackSubmit(e);
            }
            if (e.target.matches('.suggestion-vote-btn')) {
                this.handleSuggestionVote(e);
            }
            if (e.target.matches('.feedback-modal-trigger')) {
                this.showFeedbackModal(e.target.dataset.type, e.target.dataset.id);
            }
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('.feedback-form')) {
                e.preventDefault();
                this.submitFeedbackForm(e.target);
            }
        });
    }

    loadFeedbackComponents() {
        // Load feedback components where needed
        this.loadCorrelationFeedbackWidgets();
        this.loadSuggestionsPanel();
        this.loadFeedbackSummary();
    }

    // === CORRELATION FEEDBACK ===

    renderCorrelationFeedbackWidget(containerId, correlationId, correlationData = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const widget = document.createElement('div');
        widget.className = 'correlation-feedback-widget';
        widget.innerHTML = `
            <div class="feedback-widget-header">
                <h5><i class="fas fa-comment-dots"></i> Rate This Correlation</h5>
                <p class="text-muted small">Help improve our predictions with your feedback</p>
            </div>
            <div class="feedback-ratings">
                <div class="rating-group">
                    <label class="rating-label">Relevance:</label>
                    <div class="star-rating" data-field="relevance_rating">
                        ${this.renderStarRating('relevance')}
                    </div>
                </div>
                <div class="rating-group">
                    <label class="rating-label">Accuracy:</label>
                    <div class="star-rating" data-field="accuracy_rating">
                        ${this.renderStarRating('accuracy')}
                    </div>
                </div>
                <div class="rating-group">
                    <label class="rating-label">Usefulness:</label>
                    <div class="star-rating" data-field="usefulness_rating">
                        ${this.renderStarRating('usefulness')}
                    </div>
                </div>
                <div class="thumbs-rating">
                    <button type="button" class="btn btn-outline-success btn-sm thumbs-btn" data-vote="up">
                        <i class="fas fa-thumbs-up"></i> Helpful
                    </button>
                    <button type="button" class="btn btn-outline-danger btn-sm thumbs-btn" data-vote="down">
                        <i class="fas fa-thumbs-down"></i> Not Helpful
                    </button>
                </div>
            </div>
            <div class="feedback-comments mt-3">
                <div class="form-group">
                    <label for="feedback-comments-${correlationId}">Comments (Optional):</label>
                    <textarea id="feedback-comments-${correlationId}" class="form-control form-control-sm" 
                              rows="2" placeholder="Share your thoughts on this correlation..."></textarea>
                </div>
                <div class="form-group">
                    <label for="business-context-${correlationId}">Business Context (Optional):</label>
                    <textarea id="business-context-${correlationId}" class="form-control form-control-sm" 
                              rows="2" placeholder="Add relevant business context or local knowledge..."></textarea>
                </div>
            </div>
            <div class="feedback-actions mt-3">
                <button type="button" class="btn btn-primary btn-sm feedback-submit-btn" 
                        data-correlation-id="${correlationId}">
                    <i class="fas fa-paper-plane"></i> Submit Feedback
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm ms-2" 
                        onclick="this.closest('.correlation-feedback-widget').style.display='none'">
                    Maybe Later
                </button>
            </div>
            <div class="feedback-status mt-2" style="display: none;"></div>
        `;

        container.appendChild(widget);
        this.setupStarRatings(widget);
        this.setupThumbsRatings(widget);
    }

    renderStarRating(fieldName) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            stars += `<i class="star fas fa-star" data-rating="${i}" data-field="${fieldName}"></i>`;
        }
        return stars;
    }

    setupStarRatings(container) {
        const stars = container.querySelectorAll('.star');
        stars.forEach(star => {
            star.addEventListener('click', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                const field = e.target.dataset.field;
                const starContainer = e.target.parentElement;
                
                // Update visual state
                starContainer.querySelectorAll('.star').forEach((s, index) => {
                    s.classList.toggle('active', index < rating);
                });
                
                // Store rating
                starContainer.dataset.value = rating;
            });

            star.addEventListener('mouseenter', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                const starContainer = e.target.parentElement;
                
                starContainer.querySelectorAll('.star').forEach((s, index) => {
                    s.classList.toggle('hover', index < rating);
                });
            });

            star.addEventListener('mouseleave', (e) => {
                const starContainer = e.target.parentElement;
                starContainer.querySelectorAll('.star').forEach(s => {
                    s.classList.remove('hover');
                });
            });
        });
    }

    setupThumbsRatings(container) {
        const thumbsBtns = container.querySelectorAll('.thumbs-btn');
        thumbsBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Clear previous selections
                thumbsBtns.forEach(b => {
                    b.classList.remove('active');
                    b.classList.add('btn-outline-success', 'btn-outline-danger');
                    b.classList.remove('btn-success', 'btn-danger');
                });
                
                // Activate clicked button
                const isUp = e.target.closest('.thumbs-btn').dataset.vote === 'up';
                e.target.closest('.thumbs-btn').classList.add('active');
                
                if (isUp) {
                    e.target.closest('.thumbs-btn').classList.remove('btn-outline-success');
                    e.target.closest('.thumbs-btn').classList.add('btn-success');
                } else {
                    e.target.closest('.thumbs-btn').classList.remove('btn-outline-danger');
                    e.target.closest('.thumbs-btn').classList.add('btn-danger');
                }
                
                // Store value
                container.querySelector('.thumbs-rating').dataset.value = isUp ? 'true' : 'false';
            });
        });
    }

    async handleFeedbackSubmit(e) {
        e.preventDefault();
        
        const correlationId = e.target.dataset.correlationId;
        const widget = e.target.closest('.correlation-feedback-widget');
        const statusDiv = widget.querySelector('.feedback-status');
        
        try {
            // Collect feedback data
            const feedbackData = {
                correlation_id: correlationId,
                feedback_type: 'CORRELATION_RATING',
                relevance_rating: this.getStarRating(widget, 'relevance'),
                accuracy_rating: this.getStarRating(widget, 'accuracy'),
                usefulness_rating: this.getStarRating(widget, 'usefulness'),
                thumbs_up_down: this.getThumbsRating(widget),
                comments: widget.querySelector(`#feedback-comments-${correlationId}`).value,
                business_context: widget.querySelector(`#business-context-${correlationId}`).value,
                confidence_level: 4, // Default confidence
                context_data: {
                    page: window.location.pathname,
                    timestamp: new Date().toISOString()
                }
            };

            // Show loading state
            e.target.disabled = true;
            e.target.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-spinner fa-spin"></i> Submitting feedback...</div>';

            // Submit feedback
            const response = await fetch(`${this.baseUrl}/correlation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': this.currentUser.user_id,
                    'X-User-Name': this.currentUser.user_name,
                    'X-User-Role': this.currentUser.user_role
                },
                body: JSON.stringify(feedbackData)
            });

            const result = await response.json();
            
            if (result.success) {
                statusDiv.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i> Thank you for your feedback! Your input helps improve our predictions.
                    </div>
                `;
                
                // Hide form after successful submission
                setTimeout(() => {
                    widget.style.display = 'none';
                }, 3000);
                
            } else {
                throw new Error(result.error || 'Failed to submit feedback');
            }

        } catch (error) {
            console.error('Feedback submission error:', error);
            statusDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i> Error submitting feedback. Please try again.
                </div>
            `;
            
            // Reset button
            e.target.disabled = false;
            e.target.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Feedback';
        }
    }

    getStarRating(widget, field) {
        const starContainer = widget.querySelector(`[data-field="${field}_rating"]`);
        return starContainer ? parseInt(starContainer.dataset.value || '0') : 0;
    }

    getThumbsRating(widget) {
        const thumbsContainer = widget.querySelector('.thumbs-rating');
        const value = thumbsContainer ? thumbsContainer.dataset.value : null;
        return value === 'true' ? true : (value === 'false' ? false : null);
    }

    // === PREDICTION VALIDATION ===

    renderPredictionValidationModal(predictionId, predictionData) {
        const modalHtml = `
            <div class="modal fade" id="predictionValidationModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-check-circle"></i> Validate Prediction
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form class="prediction-validation-form" data-prediction-id="${predictionId}">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6>Prediction Details</h6>
                                        <div class="prediction-summary">
                                            <p><strong>Type:</strong> ${predictionData.type || 'Demand Forecast'}</p>
                                            <p><strong>Period:</strong> ${predictionData.period || 'N/A'}</p>
                                            <p><strong>Predicted Value:</strong> $${predictionData.predicted_value || '0'}</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>Actual Results</h6>
                                        <div class="form-group mb-3">
                                            <label for="actual_value">Actual Value:</label>
                                            <input type="number" id="actual_value" name="actual_value" 
                                                   class="form-control" step="0.01" required>
                                        </div>
                                        <div class="form-group mb-3">
                                            <label for="business_impact_actual">Actual Business Impact:</label>
                                            <select id="business_impact_actual" name="business_impact_actual" class="form-control">
                                                <option value="high">High</option>
                                                <option value="medium">Medium</option>
                                                <option value="low">Low</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="form-group mb-3">
                                    <label for="external_factors">External Factors That Influenced Results:</label>
                                    <textarea id="external_factors" name="external_factors" class="form-control" 
                                              rows="3" placeholder="Weather events, market changes, unexpected circumstances..."></textarea>
                                </div>
                                
                                <div class="form-group mb-3">
                                    <label for="lessons_learned">Lessons Learned:</label>
                                    <textarea id="lessons_learned" name="lessons_learned" class="form-control" 
                                              rows="3" placeholder="What could improve future predictions?"></textarea>
                                </div>
                                
                                <div class="form-group mb-3">
                                    <label for="cost_of_inaccuracy">Cost of Inaccuracy (Optional):</label>
                                    <input type="number" id="cost_of_inaccuracy" name="cost_of_inaccuracy" 
                                           class="form-control" step="0.01" placeholder="Estimated cost impact">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="feedbackSystem.submitPredictionValidation()">
                                <i class="fas fa-check"></i> Submit Validation
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('predictionValidationModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('predictionValidationModal'));
        modal.show();
    }

    async submitPredictionValidation() {
        const form = document.querySelector('.prediction-validation-form');
        const predictionId = form.dataset.predictionId;
        
        try {
            const formData = new FormData(form);
            const validationData = {
                prediction_id: predictionId,
                prediction_date: new Date().toISOString(), // In real implementation, get from prediction data
                predicted_value: 1000, // In real implementation, get from prediction data
                actual_value: parseFloat(formData.get('actual_value')),
                business_impact_actual: formData.get('business_impact_actual'),
                external_factors: formData.get('external_factors'),
                lessons_learned: formData.get('lessons_learned'),
                cost_of_inaccuracy: formData.get('cost_of_inaccuracy') ? parseFloat(formData.get('cost_of_inaccuracy')) : null,
                validation_method: 'manual'
            };

            const response = await fetch(`${this.baseUrl}/prediction-validation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': this.currentUser.user_id,
                    'X-User-Name': this.currentUser.user_name,
                    'X-User-Role': this.currentUser.user_role
                },
                body: JSON.stringify(validationData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('success', `Prediction validated! Accuracy: ${result.accuracy_score.toFixed(1)}%`);
                bootstrap.Modal.getInstance(document.getElementById('predictionValidationModal')).hide();
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            console.error('Validation submission error:', error);
            this.showNotification('error', 'Failed to submit validation. Please try again.');
        }
    }

    // === SUGGESTIONS ===

    renderSuggestionsPanel(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="suggestions-panel">
                <div class="suggestions-header">
                    <h5><i class="fas fa-lightbulb"></i> Suggest Improvements</h5>
                    <button type="button" class="btn btn-primary btn-sm" onclick="feedbackSystem.showSuggestionModal()">
                        <i class="fas fa-plus"></i> New Suggestion
                    </button>
                </div>
                <div class="suggestions-list">
                    <div class="text-center">
                        <i class="fas fa-spinner fa-spin"></i> Loading suggestions...
                    </div>
                </div>
            </div>
        `;

        this.loadSuggestionsList(container.querySelector('.suggestions-list'));
    }

    async loadSuggestionsList(container) {
        try {
            const response = await fetch(`${this.baseUrl}/suggestions?limit=10`);
            const result = await response.json();

            if (result.success && result.suggestions.length > 0) {
                container.innerHTML = result.suggestions.map(suggestion => `
                    <div class="suggestion-item card mb-3">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="suggestion-content">
                                    <h6 class="card-title">${suggestion.title}</h6>
                                    <p class="card-text text-muted small">${suggestion.description}</p>
                                    <div class="suggestion-meta">
                                        <span class="badge bg-info">${suggestion.suggestion_type.replace('_', ' ')}</span>
                                        <span class="text-muted small">by ${suggestion.user_name}</span>
                                        <span class="text-muted small">${this.formatDate(suggestion.submitted_date)}</span>
                                    </div>
                                </div>
                                <div class="suggestion-voting">
                                    <button class="btn btn-outline-success btn-sm suggestion-vote-btn" 
                                            data-suggestion-id="${suggestion.suggestion_id}" data-vote="up">
                                        <i class="fas fa-arrow-up"></i> ${suggestion.upvotes}
                                    </button>
                                    <button class="btn btn-outline-danger btn-sm suggestion-vote-btn" 
                                            data-suggestion-id="${suggestion.suggestion_id}" data-vote="down">
                                        <i class="fas fa-arrow-down"></i> ${suggestion.downvotes}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<div class="text-muted text-center">No suggestions yet. Be the first to suggest an improvement!</div>';
            }

        } catch (error) {
            console.error('Failed to load suggestions:', error);
            container.innerHTML = '<div class="text-danger text-center">Failed to load suggestions</div>';
        }
    }

    showSuggestionModal() {
        const modalHtml = `
            <div class="modal fade" id="suggestionModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-lightbulb"></i> Suggest Improvement
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form class="suggestion-form">
                                <div class="form-group mb-3">
                                    <label for="suggestion_type">Suggestion Type:</label>
                                    <select id="suggestion_type" name="suggestion_type" class="form-control" required>
                                        <option value="new_correlation">New Correlation</option>
                                        <option value="data_source">New Data Source</option>
                                        <option value="metric_enhancement">Metric Enhancement</option>
                                    </select>
                                </div>
                                
                                <div class="form-group mb-3">
                                    <label for="title">Title:</label>
                                    <input type="text" id="title" name="title" class="form-control" 
                                           placeholder="Brief, descriptive title" required>
                                </div>
                                
                                <div class="form-group mb-3">
                                    <label for="description">Description:</label>
                                    <textarea id="description" name="description" class="form-control" 
                                              rows="4" placeholder="Detailed description of your suggestion" required></textarea>
                                </div>
                                
                                <div class="form-group mb-3">
                                    <label for="business_justification">Business Justification:</label>
                                    <textarea id="business_justification" name="business_justification" class="form-control" 
                                              rows="3" placeholder="Why would this be valuable for the business?"></textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="form-group mb-3">
                                            <label for="expected_impact">Expected Impact:</label>
                                            <select id="expected_impact" name="expected_impact" class="form-control">
                                                <option value="high">High</option>
                                                <option value="medium" selected>Medium</option>
                                                <option value="low">Low</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-group mb-3">
                                            <label for="estimated_effort">Implementation Effort:</label>
                                            <select id="estimated_effort" name="estimated_effort" class="form-control">
                                                <option value="low">Low</option>
                                                <option value="medium" selected>Medium</option>
                                                <option value="high">High</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="feedbackSystem.submitSuggestion()">
                                <i class="fas fa-paper-plane"></i> Submit Suggestion
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.getElementById('suggestionModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add modal to page
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('suggestionModal'));
        modal.show();
    }

    async submitSuggestion() {
        const form = document.querySelector('.suggestion-form');
        const formData = new FormData(form);
        
        try {
            const suggestionData = {
                suggestion_type: formData.get('suggestion_type'),
                title: formData.get('title'),
                description: formData.get('description'),
                business_justification: formData.get('business_justification'),
                expected_impact: formData.get('expected_impact'),
                estimated_effort: formData.get('estimated_effort')
            };

            const response = await fetch(`${this.baseUrl}/suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': this.currentUser.user_id,
                    'X-User-Name': this.currentUser.user_name,
                    'X-User-Role': this.currentUser.user_role
                },
                body: JSON.stringify(suggestionData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('success', 'Suggestion submitted successfully!');
                bootstrap.Modal.getInstance(document.getElementById('suggestionModal')).hide();
                
                // Reload suggestions list if visible
                const suggestionsList = document.querySelector('.suggestions-list');
                if (suggestionsList) {
                    this.loadSuggestionsList(suggestionsList);
                }
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            console.error('Suggestion submission error:', error);
            this.showNotification('error', 'Failed to submit suggestion. Please try again.');
        }
    }

    async handleSuggestionVote(e) {
        const suggestionId = e.target.closest('.suggestion-vote-btn').dataset.suggestionId;
        const vote = e.target.closest('.suggestion-vote-btn').dataset.vote;
        
        try {
            const response = await fetch(`${this.baseUrl}/suggestions/${suggestionId}/vote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': this.currentUser.user_id
                },
                body: JSON.stringify({ vote })
            });

            const result = await response.json();
            
            if (result.success) {
                // Update vote counts in UI
                const suggestionItem = e.target.closest('.suggestion-item');
                const upBtn = suggestionItem.querySelector('[data-vote="up"]');
                const downBtn = suggestionItem.querySelector('[data-vote="down"]');
                
                upBtn.innerHTML = `<i class="fas fa-arrow-up"></i> ${result.upvotes}`;
                downBtn.innerHTML = `<i class="fas fa-arrow-down"></i> ${result.downvotes}`;
                
                // Visual feedback
                e.target.closest('.suggestion-vote-btn').classList.add('voted');
                setTimeout(() => {
                    e.target.closest('.suggestion-vote-btn').classList.remove('voted');
                }, 1000);
                
            } else {
                throw new Error(result.error);
            }

        } catch (error) {
            console.error('Vote submission error:', error);
            this.showNotification('error', 'Failed to submit vote');
        }
    }

    // === UTILITY METHODS ===

    loadCorrelationFeedbackWidgets() {
        // Auto-load feedback widgets for correlations on the page
        const correlationElements = document.querySelectorAll('[data-correlation-id]');
        correlationElements.forEach(el => {
            const correlationId = el.dataset.correlationId;
            if (!el.querySelector('.correlation-feedback-widget')) {
                const widgetContainer = document.createElement('div');
                widgetContainer.className = 'feedback-widget-container mt-3';
                el.appendChild(widgetContainer);
                
                this.renderCorrelationFeedbackWidget(widgetContainer.id = `feedback-widget-${correlationId}`, correlationId);
            }
        });
    }

    loadSuggestionsPanel() {
        const panelContainer = document.getElementById('suggestions-panel');
        if (panelContainer) {
            this.renderSuggestionsPanel('suggestions-panel');
        }
    }

    loadFeedbackSummary() {
        const summaryContainer = document.getElementById('feedback-summary');
        if (summaryContainer) {
            this.renderFeedbackSummary('feedback-summary');
        }
    }

    async renderFeedbackSummary(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const response = await fetch(`${this.baseUrl}/summary?days=7`);
            const result = await response.json();

            if (result.success) {
                const data = result;
                container.innerHTML = `
                    <div class="feedback-summary-widget">
                        <h6><i class="fas fa-chart-line"></i> Feedback Summary (7 days)</h6>
                        <div class="row text-center">
                            <div class="col-md-3">
                                <div class="metric">
                                    <div class="metric-value">${data.total_feedback_submissions || 0}</div>
                                    <div class="metric-label">Feedback Items</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric">
                                    <div class="metric-value">${data.unique_contributors || 0}</div>
                                    <div class="metric-label">Contributors</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric">
                                    <div class="metric-value">${data.rating_averages?.usefulness.toFixed(1) || 'N/A'}</div>
                                    <div class="metric-label">Avg Usefulness</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric">
                                    <div class="metric-value">${data.prediction_accuracy?.average_accuracy.toFixed(1) || 'N/A'}%</div>
                                    <div class="metric-label">Prediction Accuracy</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }

        } catch (error) {
            console.error('Failed to load feedback summary:', error);
            container.innerHTML = '<div class="text-muted">Unable to load feedback summary</div>';
        }
    }

    showNotification(type, message) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass} alert-dismissible fade show feedback-notification`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="fas ${icon}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
}

// Initialize feedback system when DOM is loaded
let feedbackSystem;
document.addEventListener('DOMContentLoaded', () => {
    feedbackSystem = new FeedbackSystem();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackSystem;
}