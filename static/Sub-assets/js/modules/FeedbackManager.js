class FeedbackManager {
    constructor() {
        this.storageManager = window.storageManager;
        this.uiManager = window.uiManager;
        this.feedback = [];
        this.filteredFeedback = [];
        this.currentFilter = null;
    }

    initialize() {
        this.loadFeedback();
        this.updateKPICards();
        this.renderFeedback();
    }

    // Load feedback from storage
    loadFeedback() {
        this.feedback = this.storageManager.getFeedback();
        this.filteredFeedback = [...this.feedback];
    }

    // Update KPI cards with real data
    updateKPICards() {
        const stats = this.getFeedbackStats();
        
        document.getElementById('averageRating').textContent = `${stats.averageRating}/5.0`;
        document.getElementById('totalReviews').textContent = this.formatNumber(stats.totalReviews);
        document.getElementById('positiveFeedback').textContent = `${stats.positivePercentage}%`;
        document.getElementById('negativeFeedback').textContent = `${stats.negativePercentage}%`;
    }

    // Render feedback items
    renderFeedback() {
        const container = document.getElementById('feedbackContainer');
        if (!container) return;

        if (this.filteredFeedback.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-heart fa-3x mb-3"></i>
                    <h4>No feedback found</h4>
                    <p>No feedback matches your current filter.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.filteredFeedback.map(feedback => `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex align-items-start">
                        <div class="flex-shrink-0 me-3">
                            <i class="fas fa-${feedback.sentiment === 'positive' ? 'thumbs-up text-success' : 'thumbs-down text-danger'} fa-2x"></i>
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <div>
                                    <h6 class="mb-1">${feedback.user}</h6>
                                    <div class="mb-2">
                                        ${this.generateStarRating(feedback.rating)}
                                    </div>
                                </div>
                                <small class="text-muted">${this.uiManager.formatDateTime(feedback.timestamp)}</small>
                            </div>
                            <p class="mb-2">${feedback.comment}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge badge-info">${feedback.category}</span>
                                <small class="text-muted">${this.uiManager.formatRelativeTime(feedback.timestamp)}</small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Generate star rating HTML
    generateStarRating(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 !== 0;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

        let starsHTML = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star text-warning"></i>';
        }
        
        // Half star
        if (hasHalfStar) {
            starsHTML += '<i class="fas fa-star-half-alt text-warning"></i>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star text-warning"></i>';
        }

        return starsHTML;
    }

    // Filter feedback by rating
    filterByRating(rating) {
        this.currentFilter = rating;
        
        if (rating === null) {
            this.filteredFeedback = [...this.feedback];
        } else {
            this.filteredFeedback = this.feedback.filter(feedback => feedback.rating === rating);
        }
        
        this.renderFeedback();
        this.updateFilterButtons();
    }

    // Update filter buttons
    updateFilterButtons() {
        const buttons = document.querySelectorAll('.btn-outline-secondary');
        buttons.forEach(button => {
            button.classList.remove('btn-primary');
            button.classList.add('btn-outline-secondary');
        });

        if (this.currentFilter) {
            const activeButton = document.querySelector(`[onclick="filterFeedback(${this.currentFilter})"]`);
            if (activeButton) {
                activeButton.classList.remove('btn-outline-secondary');
                activeButton.classList.add('btn-primary');
            }
        }
    }

    // Get feedback statistics
    getFeedbackStats() {
        const totalReviews = this.feedback.length;
        
        if (totalReviews === 0) {
            return {
                totalReviews: 0,
                averageRating: 0,
                positivePercentage: 0,
                negativePercentage: 0,
                neutralPercentage: 0
            };
        }

        // Calculate average rating
        const totalRating = this.feedback.reduce((sum, feedback) => sum + feedback.rating, 0);
        const averageRating = (totalRating / totalReviews).toFixed(1);

        // Calculate sentiment percentages
        const positiveCount = this.feedback.filter(f => f.sentiment === 'positive').length;
        const negativeCount = this.feedback.filter(f => f.sentiment === 'negative').length;
        const neutralCount = this.feedback.filter(f => f.sentiment === 'neutral').length;

        return {
            totalReviews,
            averageRating,
            positivePercentage: Math.round((positiveCount / totalReviews) * 100),
            negativePercentage: Math.round((negativeCount / totalReviews) * 100),
            neutralPercentage: Math.round((neutralCount / totalReviews) * 100),
            positiveCount,
            negativeCount,
            neutralCount
        };
    }

    // Get feedback by sentiment
    getFeedbackBySentiment(sentiment) {
        return this.feedback.filter(f => f.sentiment === sentiment);
    }

    // Get feedback by category
    getFeedbackByCategory(category) {
        return this.feedback.filter(f => f.category === category);
    }

    // Get feedback by date range
    getFeedbackByDateRange(startDate, endDate) {
        return this.feedback.filter(feedback => {
            const feedbackDate = new Date(feedback.timestamp);
            return feedbackDate >= new Date(startDate) && feedbackDate <= new Date(endDate);
        });
    }

    // Get recent feedback (last N days)
    getRecentFeedback(days = 7) {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - days);
        
        return this.feedback.filter(feedback => 
            new Date(feedback.timestamp) >= cutoffDate
        );
    }

    // Get feedback trends
    getFeedbackTrends() {
        const trends = [];
        const today = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateString = date.toISOString().split('T')[0];
            
            const dayFeedback = this.feedback.filter(feedback => 
                feedback.timestamp.startsWith(dateString)
            );
            
            trends.push({
                date: this.uiManager.formatDate(dateString),
                total: dayFeedback.length,
                positive: dayFeedback.filter(f => f.sentiment === 'positive').length,
                negative: dayFeedback.filter(f => f.sentiment === 'negative').length,
                neutral: dayFeedback.filter(f => f.sentiment === 'neutral').length,
                averageRating: dayFeedback.length > 0 ? 
                    (dayFeedback.reduce((sum, f) => sum + f.rating, 0) / dayFeedback.length).toFixed(1) : 0
            });
        }
        
        return trends;
    }

    // Get top categories
    getTopCategories() {
        const categories = {};
        this.feedback.forEach(feedback => {
            categories[feedback.category] = (categories[feedback.category] || 0) + 1;
        });

        return Object.entries(categories)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([category, count]) => ({ category, count }));
    }

    // Get rating distribution
    getRatingDistribution() {
        const distribution = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
        
        this.feedback.forEach(feedback => {
            const rating = Math.floor(feedback.rating);
            if (distribution[rating] !== undefined) {
                distribution[rating]++;
            }
        });

        return distribution;
    }

    // Export feedback to CSV
    exportFeedback() {
        const exportData = this.feedback.map(feedback => ({
            User: feedback.user,
            Rating: feedback.rating,
            Comment: feedback.comment,
            Category: feedback.category,
            Sentiment: feedback.sentiment,
            'Submitted Date': this.uiManager.formatDateTime(feedback.timestamp)
        }));

        const success = this.uiManager.exportToCSV(exportData, 'feedback_export.csv');
        
        if (success) {
            this.uiManager.showSuccess('Feedback exported successfully!');
        } else {
            this.uiManager.showError('Failed to export feedback');
        }
    }

    // Get feedback insights
    getFeedbackInsights() {
        const stats = this.getFeedbackStats();
        const trends = this.getFeedbackTrends();
        const categories = this.getTopCategories();
        const ratingDistribution = this.getRatingDistribution();

        // Calculate satisfaction score
        const satisfactionScore = (stats.averageRating / 5) * 100;

        // Get most common category
        const mostCommonCategory = categories[0]?.category || 'N/A';

        // Calculate response rate (simulated)
        const responseRate = 95.8;

        return {
            stats,
            trends,
            categories,
            ratingDistribution,
            insights: {
                satisfactionScore: Math.round(satisfactionScore),
                mostCommonCategory,
                responseRate,
                averageRating: stats.averageRating,
                totalReviews: stats.totalReviews
            }
        };
    }

    // Search feedback
    searchFeedback(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredFeedback = this.currentFilter ? 
                this.feedback.filter(f => f.rating === this.currentFilter) : 
                [...this.feedback];
        } else {
            this.filteredFeedback = this.feedback.filter(feedback => 
                feedback.comment.toLowerCase().includes(searchTerm.toLowerCase()) ||
                feedback.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
                feedback.user.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }
        
        this.renderFeedback();
    }

    // Get feedback by rating range
    getFeedbackByRatingRange(minRating, maxRating) {
        return this.feedback.filter(feedback => 
            feedback.rating >= minRating && feedback.rating <= maxRating
        );
    }

    // Get high priority feedback (low ratings)
    getHighPriorityFeedback() {
        return this.getFeedbackByRatingRange(1, 2);
    }

    // Get positive feedback (high ratings)
    getPositiveFeedback() {
        return this.getFeedbackByRatingRange(4, 5);
    }

    // Format number with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Get feedback summary by month
    getFeedbackSummaryByMonth() {
        const monthlyData = {};
        
        this.feedback.forEach(feedback => {
            const date = new Date(feedback.timestamp);
            const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
            
            if (!monthlyData[monthKey]) {
                monthlyData[monthKey] = {
                    total: 0,
                    positive: 0,
                    negative: 0,
                    neutral: 0,
                    totalRating: 0
                };
            }
            
            monthlyData[monthKey].total++;
            monthlyData[monthKey][feedback.sentiment]++;
            monthlyData[monthKey].totalRating += feedback.rating;
        });

        return Object.entries(monthlyData).map(([month, data]) => ({
            month,
            ...data,
            averageRating: data.total > 0 ? (data.totalRating / data.total).toFixed(1) : 0
        }));
    }

    // Clear all filters
    clearFilters() {
        this.currentFilter = null;
        this.filteredFeedback = [...this.feedback];
        this.renderFeedback();
        this.updateFilterButtons();
    }
}

// Initialize global feedback manager
window.FeedbackManager = FeedbackManager;
