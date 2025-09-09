/**
 * FeedbackManager - Manages user feedback and ratings
 */
class FeedbackManager extends BaseManager {
    constructor() {
        super('educhat_feedback');
        this.initializeDefaultFeedback();
    }

    /**
     * Initialize with default feedback
     */
    initializeDefaultFeedback() {
        if (this.data.length === 0) {
            const defaultFeedback = [
                {
                    userId: 'user_001',
                    rating: 5,
                    message: 'Very helpful and responsive chatbot! Got my enrollment issue resolved quickly.',
                    category: 'Enrollment',
                    department: 'Registrar Office',
                    sentiment: 'positive'
                },
                {
                    userId: 'user_002',
                    rating: 4,
                    message: 'Good experience overall. The bot understood my question about counseling services.',
                    category: 'Counseling',
                    department: 'Guidance Office',
                    sentiment: 'positive'
                },
                {
                    userId: 'user_003',
                    rating: 3,
                    message: 'The response was okay, but it took a while to get to the point.',
                    category: 'Technical Support',
                    department: 'ICT Office',
                    sentiment: 'neutral'
                },
                {
                    userId: 'user_004',
                    rating: 2,
                    message: 'Not very helpful. The bot didn\'t understand my specific question about transcripts.',
                    category: 'Transcript',
                    department: 'Registrar Office',
                    sentiment: 'negative'
                },
                {
                    userId: 'user_005',
                    rating: 5,
                    message: 'Excellent service! The chatbot helped me schedule my counseling session easily.',
                    category: 'Counseling',
                    department: 'Guidance Office',
                    sentiment: 'positive'
                }
            ];

            defaultFeedback.forEach(feedback => this.addFeedback(feedback));
        }
    }

    /**
     * Add new feedback with sentiment analysis
     */
    addFeedback(feedbackData) {
        if (!feedbackData.rating || !feedbackData.message) {
            return {
                success: false,
                message: 'Rating and message are required'
            };
        }

        // Determine sentiment based on rating
        let sentiment = 'neutral';
        if (feedbackData.rating >= 4) {
            sentiment = 'positive';
        } else if (feedbackData.rating <= 2) {
            sentiment = 'negative';
        }

        const feedback = {
            userId: feedbackData.userId || `user_${Date.now()}`,
            rating: feedbackData.rating,
            message: feedbackData.message.trim(),
            category: feedbackData.category || 'General',
            department: feedbackData.department || 'General',
            sentiment: sentiment
        };

        const newFeedback = this.add(feedback);
        return {
            success: true,
            feedback: newFeedback
        };
    }

    /**
     * Get feedback by rating
     */
    getFeedbackByRating(rating) {
        return this.data.filter(feedback => feedback.rating === rating);
    }

    /**
     * Get feedback by sentiment
     */
    getFeedbackBySentiment(sentiment) {
        return this.data.filter(feedback => feedback.sentiment === sentiment);
    }

    /**
     * Get feedback by category
     */
    getFeedbackByCategory(category) {
        return this.data.filter(feedback => feedback.category === category);
    }

    /**
     * Get feedback by department
     */
    getFeedbackByDepartment(department) {
        return this.data.filter(feedback => feedback.department === department);
    }

    /**
     * Search feedback
     */
    searchFeedback(query) {
        const searchTerm = query.toLowerCase();
        return this.data.filter(feedback => 
            feedback.message.toLowerCase().includes(searchTerm) ||
            feedback.category.toLowerCase().includes(searchTerm) ||
            feedback.department.toLowerCase().includes(searchTerm)
        );
    }

    /**
     * Get feedback statistics
     */
    getStats() {
        const totalFeedback = this.data.length;
        const positiveFeedback = this.data.filter(feedback => feedback.sentiment === 'positive').length;
        const negativeFeedback = this.data.filter(feedback => feedback.sentiment === 'negative').length;
        const neutralFeedback = this.data.filter(feedback => feedback.sentiment === 'neutral').length;

        const positivePercentage = totalFeedback > 0 ? (positiveFeedback / totalFeedback) * 100 : 0;
        const negativePercentage = totalFeedback > 0 ? (negativeFeedback / totalFeedback) * 100 : 0;

        const feedbackByCategory = {};
        const categories = [...new Set(this.data.map(feedback => feedback.category))];
        
        categories.forEach(category => {
            feedbackByCategory[category] = this.data.filter(feedback => feedback.category === category).length;
        });

        const feedbackByDepartment = {};
        const departments = ['Guidance Office', 'Registrar Office', 'Admissions Office', 'ICT Office', 'OSA Office'];
        
        departments.forEach(department => {
            feedbackByDepartment[department] = this.data.filter(feedback => feedback.department === department).length;
        });

        return {
            totalFeedback,
            positiveFeedback,
            negativeFeedback,
            neutralFeedback,
            positivePercentage: Math.round(positivePercentage * 10) / 10,
            negativePercentage: Math.round(negativePercentage * 10) / 10,
            feedbackByCategory,
            feedbackByDepartment
        };
    }

    /**
     * Get average rating
     */
    getAverageRating() {
        if (this.data.length === 0) return 0;
        const totalRating = this.data.reduce((sum, feedback) => sum + feedback.rating, 0);
        return Math.round((totalRating / this.data.length) * 10) / 10;
    }

    /**
     * Get rating distribution
     */
    getRatingDistribution() {
        const distribution = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
        this.data.forEach(feedback => {
            distribution[feedback.rating]++;
        });
        return distribution;
    }

    /**
     * Get feedback by category with count
     */
    getFeedbackByCategoryWithCount() {
        const categories = [...new Set(this.data.map(feedback => feedback.category))];
        return categories.map(category => ({
            category,
            count: this.data.filter(feedback => feedback.category === category).length
        }));
    }

    /**
     * Get recent feedback
     */
    getRecentFeedback(limit = 10) {
        return this.data
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
            .slice(0, limit);
    }

    /**
     * Get feedback from date range
     */
    getFeedbackFromDateRange(startDate, endDate) {
        return this.data.filter(feedback => {
            const feedbackDate = new Date(feedback.createdAt);
            return feedbackDate >= startDate && feedbackDate <= endDate;
        });
    }

    /**
     * Get top categories
     */
    getTopCategories(limit = 5) {
        const categoryCounts = {};
        this.data.forEach(feedback => {
            categoryCounts[feedback.category] = (categoryCounts[feedback.category] || 0) + 1;
        });

        return Object.entries(categoryCounts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, limit)
            .map(([category, count]) => ({ category, count }));
    }

    /**
     * Get feedback trends
     */
    getFeedbackTrends() {
        // Simulate trend data
        return {
            averageRating: this.getAverageRating(),
            totalFeedback: this.data.length,
            positiveTrend: 5.2,
            negativeTrend: 1.8
        };
    }

    /**
     * Export feedback to CSV
     */
    exportToCSV(filteredFeedback = null) {
        const feedback = filteredFeedback || this.data;
        
        const headers = ['User ID', 'Rating', 'Message', 'Category', 'Department', 'Sentiment', 'Date'];
        const rows = feedback.map(fb => [
            fb.userId,
            fb.rating,
            fb.message,
            fb.category,
            fb.department,
            fb.sentiment,
            new Date(fb.createdAt).toLocaleDateString()
        ]);

        const csvContent = [headers, ...rows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\n');

        return csvContent;
    }

    /**
     * Get dashboard summary
     */
    getDashboardSummary() {
        const stats = this.getStats();
        const averageRating = this.getAverageRating();
        
        return {
            averageRating,
            totalFeedback: stats.totalFeedback,
            positivePercentage: stats.positivePercentage,
            negativePercentage: stats.negativePercentage,
            recentFeedback: this.getRecentFeedback(5)
        };
    }

    /**
     * Filter feedback
     */
    filterFeedback(filters) {
        return this.data.filter(feedback => {
            if (filters.rating && feedback.rating !== filters.rating) return false;
            if (filters.sentiment && feedback.sentiment !== filters.sentiment) return false;
            if (filters.category && feedback.category !== filters.category) return false;
            if (filters.department && feedback.department !== filters.department) return false;
            return true;
        });
    }
}
