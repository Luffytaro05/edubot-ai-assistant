/**
 * FeedbackManager.js
 * Manages feedback analytics display for Sub-Admin dashboard
 * Fetches and renders feedback statistics and recent reviews
 */

class FeedbackManager {
    constructor() {
        this.allFeedback = [];
        this.filteredFeedback = [];
        this.currentFilter = null;
        this.timeFilter = { type: null, value: null };
    }

    /**
     * Initialize the feedback manager
     */
    async initialize() {
        console.log('Initializing FeedbackManager...');
        await this.loadFeedbackStats();
        await this.loadRecentFeedback();
        this.setupEventListeners();
    }

    /**
     * Load feedback statistics from API
     */
    async loadFeedbackStats() {
        try {
            // Build query string with time filter if set
            let url = '/api/sub-admin/feedback/stats';
            if (this.timeFilter.type && this.timeFilter.value) {
                url += `?time_filter=${this.timeFilter.type}&time_value=${this.timeFilter.value}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.renderStats(result.data);
            } else {
                console.error('Failed to load feedback stats:', result.message);
                this.showError('Failed to load feedback statistics');
            }
        } catch (error) {
            console.error('Error loading feedback stats:', error);
            this.showError('Error loading feedback statistics');
        }
    }

    /**
     * Load recent feedback from API
     */
    async loadRecentFeedback(limit = 20) {
        try {
            // Build query string
            let url = `/api/sub-admin/feedback/recent?limit=${limit}`;
            
            if (this.currentFilter) {
                url += `&rating=${this.currentFilter}`;
            }
            
            if (this.timeFilter.type && this.timeFilter.value) {
                url += `&time_filter=${this.timeFilter.type}&time_value=${this.timeFilter.value}`;
            }

            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.allFeedback = result.data;
                this.filteredFeedback = result.data;
                this.renderFeedbackList(this.filteredFeedback);
            } else {
                console.error('Failed to load recent feedback:', result.message);
                this.showError('Failed to load recent feedback');
            }
        } catch (error) {
            console.error('Error loading recent feedback:', error);
            this.showError('Error loading recent feedback');
        }
    }

    /**
     * Render statistics to the UI
     */
    renderStats(data) {
        // Average Rating
        const avgRatingEl = document.getElementById('averageRating');
        if (avgRatingEl) {
            avgRatingEl.textContent = `${data.average_rating}/5.0`;
        }

        // Total Reviews
        const totalReviewsEl = document.getElementById('totalReviews');
        if (totalReviewsEl) {
            totalReviewsEl.textContent = this.formatNumber(data.total_reviews);
        }

        // Positive Feedback %
        const positiveFeedbackEl = document.getElementById('positiveFeedback');
        if (positiveFeedbackEl) {
            positiveFeedbackEl.textContent = `${data.positive_percentage}%`;
        }

        // Negative Feedback %
        const negativeFeedbackEl = document.getElementById('negativeFeedback');
        if (negativeFeedbackEl) {
            negativeFeedbackEl.textContent = `${data.negative_percentage}%`;
        }

        console.log('Stats rendered successfully');
    }

    /**
     * Render feedback list to the UI
     */
    renderFeedbackList(feedbackArray) {
        const container = document.getElementById('feedbackContainer');
        if (!container) {
            console.error('Feedback container not found');
            return;
        }

        if (feedbackArray.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-inbox fa-3x mb-3"></i>
                    <p>No feedback found</p>
                </div>
            `;
            return;
        }

        const feedbackHTML = feedbackArray.map(feedback => this.createFeedbackCard(feedback)).join('');
        container.innerHTML = feedbackHTML;
    }

    /**
     * Create a single feedback card HTML
     */
    createFeedbackCard(feedback) {
        const stars = this.generateStars(feedback.rating);
        const timestamp = this.formatTimestamp(feedback.timestamp);
        const sentiment = this.getSentimentBadge(feedback.sentiment || this.determineSentiment(feedback.rating));
        const comment = feedback.comment ? this.escapeHtml(feedback.comment) : '<em class="text-muted">No comment provided</em>';

        return `
            <div class="feedback-item mb-3 p-3 border rounded" data-rating="${feedback.rating}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <div class="feedback-rating mb-1">
                            ${stars}
                        </div>
                        <small class="text-muted">
                            <i class="fas fa-clock"></i> ${timestamp}
                        </small>
                    </div>
                    ${sentiment}
                </div>
                <div class="feedback-comment">
                    ${comment}
                </div>
                ${feedback.user_id ? `<div class="mt-2"><small class="text-muted">User ID: ${feedback.user_id}</small></div>` : ''}
            </div>
        `;
    }

    /**
     * Generate star rating HTML
     */
    generateStars(rating) {
        let starsHTML = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                starsHTML += '<i class="fas fa-star text-warning"></i>';
            } else {
                starsHTML += '<i class="far fa-star text-muted"></i>';
            }
        }
        return starsHTML;
    }

    /**
     * Get sentiment badge HTML
     */
    getSentimentBadge(sentiment) {
        const badges = {
            positive: '<span class="badge bg-success">Positive</span>',
            neutral: '<span class="badge bg-warning">Neutral</span>',
            negative: '<span class="badge bg-danger">Negative</span>'
        };
        return badges[sentiment] || badges.neutral;
    }

    /**
     * Determine sentiment from rating
     */
    determineSentiment(rating) {
        if (rating >= 4) return 'positive';
        if (rating === 3) return 'neutral';
        return 'negative';
    }

    /**
     * Format timestamp to readable format
     */
    formatTimestamp(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

    /**
     * Format numbers with commas
     */
    formatNumber(num) {
        return num.toLocaleString('en-US');
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Filter feedback by rating
     */
    async filterByRating(rating) {
        this.currentFilter = rating;
        await this.loadRecentFeedback();
    }

    /**
     * Clear all filters
     */
    async clearFilters() {
        this.currentFilter = null;
        await this.loadRecentFeedback();
    }

    /**
     * Search feedback by comment text
     */
    searchFeedback(searchTerm) {
        if (!searchTerm || searchTerm.trim() === '') {
            this.filteredFeedback = this.allFeedback;
        } else {
            const term = searchTerm.toLowerCase();
            this.filteredFeedback = this.allFeedback.filter(feedback => {
                const comment = feedback.comment || '';
                return comment.toLowerCase().includes(term);
            });
        }
        this.renderFeedbackList(this.filteredFeedback);
    }

    /**
     * Set time filter
     */
    async setTimeFilter(type, value) {
        this.timeFilter = { type, value };
        await this.loadFeedbackStats();
        await this.loadRecentFeedback();
    }

    /**
     * Clear time filter
     */
    async clearTimeFilter() {
        this.timeFilter = { type: null, value: null };
        await this.loadFeedbackStats();
        await this.loadRecentFeedback();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Add any additional event listeners here if needed
        console.log('Event listeners setup complete');
    }

    /**
     * Show error message
     */
    showError(message) {
        console.error(message);
        // You can integrate with your toast notification system here
        if (window.uiManager && typeof window.uiManager.showToast === 'function') {
            window.uiManager.showToast('Error', message, 'error');
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        console.log(message);
        if (window.uiManager && typeof window.uiManager.showToast === 'function') {
            window.uiManager.showToast('Success', message, 'success');
        }
    }
}

// Export for use in other modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackManager;
}
