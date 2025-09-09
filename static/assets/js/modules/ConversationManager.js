/**
 * ConversationManager - Updated to work with MongoDB backend API
 * Manages chatbot conversation logs with sentiment analysis and filtering
 * Now uses REST API calls instead of localStorage
 */
class ConversationManager {
    constructor() {
        this.baseURL = '/api/conversations';
        this.cache = null;
        this.lastFetch = null;
        this.cacheTimeout = 30000; // 30 seconds
    }

    /**
     * Get authentication token from localStorage
     * @returns {string|null} JWT token
     */
    getAuthToken() {
        return localStorage.getItem('auth_token');
    }

    /**
     * Get authentication headers
     * @returns {Object} Headers object with Authorization
     */
    getAuthHeaders() {
        const token = this.getAuthToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
    }

    /**
     * Handle API errors
     * @param {Response} response - Fetch response
     * @returns {Promise<Object>} Error object
     */
    async handleError(response) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            errorData = { message: 'An unexpected error occurred' };
        }
        
        if (response.status === 401) {
            // Token expired or invalid, redirect to login
            localStorage.removeItem('auth_token');
            window.location.href = '/index.html';
            return;
        }
        
        throw new Error(errorData.message || `HTTP ${response.status}`);
    }

    /**
     * Make authenticated API request
     * @param {string} url - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} API response
     */
    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...this.getAuthHeaders(),
                    ...options.headers
                }
            });

            if (!response.ok) {
                await this.handleError(response);
                return;
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    /**
     * Get all conversations with optional filtering and pagination
     * @param {Object} options - Query options
     * @returns {Promise<Object>} Conversations data
     */
    async getAll(options = {}) {
        try {
            // Build query parameters
            const params = new URLSearchParams();
            
            if (options.page) params.append('page', options.page);
            if (options.per_page) params.append('per_page', options.per_page);
            if (options.search) params.append('search', options.search);
            if (options.sentiment) params.append('sentiment', options.sentiment);
            if (options.status) params.append('status', options.status);
            if (options.user_type) params.append('user_type', options.user_type);
            if (options.date_range) params.append('date_range', options.date_range);
            if (options.start_date) params.append('start_date', options.start_date);
            if (options.end_date) params.append('end_date', options.end_date);

            const url = params.toString() ? `${this.baseURL}?${params.toString()}` : this.baseURL;
            const response = await this.apiRequest(url);
            
            if (response.success) {
                // Update cache
                this.cache = response.conversations;
                this.lastFetch = Date.now();
                return response;
            } else {
                throw new Error(response.message || 'Failed to fetch conversations');
            }
        } catch (error) {
            console.error('Error fetching conversations:', error);
            toast.error('Failed to load conversations');
            return { success: false, conversations: [], pagination: {}, message: error.message };
        }
    }

    /**
     * Get conversations from cache if available and not expired
     * @returns {Array|null} Cached conversations or null
     */
    getCachedConversations() {
        if (this.cache && this.lastFetch && (Date.now() - this.lastFetch) < this.cacheTimeout) {
            return this.cache;
        }
        return null;
    }

    /**
     * Get conversation by ID
     * @param {string} id - Conversation ID
     * @returns {Promise<Object>} Conversation data
     */
    async getById(id) {
        try {
            const response = await this.apiRequest(`${this.baseURL}/${id}`);
            
            if (response.success) {
                return response.conversation;
            } else {
                throw new Error(response.message || 'Conversation not found');
            }
        } catch (error) {
            console.error('Error fetching conversation:', error);
            toast.error('Failed to load conversation');
            return null;
        }
    }

    /**
     * Add a new conversation
     * @param {Object} conversationData - The conversation data
     * @returns {Promise<Object>} Result object with success status and message
     */
    async addConversation(conversationData) {
        try {
            const response = await this.apiRequest(this.baseURL, {
                method: 'POST',
                body: JSON.stringify(conversationData)
            });

            if (response.success) {
                // Invalidate cache
                this.cache = null;
                toast.success('Conversation added successfully');
                return response;
            } else {
                throw new Error(response.message || 'Failed to add conversation');
            }
        } catch (error) {
            console.error('Error adding conversation:', error);
            toast.error('Failed to add conversation');
            return { success: false, message: error.message };
        }
    }

    /**
     * Update an existing conversation
     * @param {string} id - The conversation ID
     * @param {Object} updates - The updates to apply
     * @returns {Promise<Object>} Result object with success status and message
     */
    async updateConversation(id, updates) {
        try {
            const response = await this.apiRequest(`${this.baseURL}/${id}`, {
                method: 'PUT',
                body: JSON.stringify(updates)
            });

            if (response.success) {
                // Invalidate cache
                this.cache = null;
                toast.success('Conversation updated successfully');
                return response;
            } else {
                throw new Error(response.message || 'Failed to update conversation');
            }
        } catch (error) {
            console.error('Error updating conversation:', error);
            toast.error('Failed to update conversation');
            return { success: false, message: error.message };
        }
    }

    /**
     * Delete a conversation
     * @param {string} id - The conversation ID
     * @returns {Promise<Object>} Result object with success status and message
     */
    async deleteConversation(id) {
        try {
            const response = await this.apiRequest(`${this.baseURL}/${id}`, {
                method: 'DELETE'
            });

            if (response.success) {
                // Invalidate cache
                this.cache = null;
                toast.success('Conversation deleted successfully');
                return response;
            } else {
                throw new Error(response.message || 'Failed to delete conversation');
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            toast.error('Failed to delete conversation');
            return { success: false, message: error.message };
        }
    }

    /**
     * Search conversations
     * @param {string} query - The search query
     * @param {Object} options - Additional search options
     * @returns {Promise<Array>} Array of matching conversations
     */
    async searchConversations(query, options = {}) {
        try {
            const searchOptions = {
                ...options,
                search: query,
                per_page: options.per_page || 50 // Get more results for search
            };

            const response = await this.getAll(searchOptions);
            return response.success ? response.conversations : [];
        } catch (error) {
            console.error('Error searching conversations:', error);
            return [];
        }
    }

    /**
     * Get filtered conversations based on criteria
     * @param {Object} filters - Filter criteria
     * @returns {Promise<Array>} Array of filtered conversations
     */
    async getFilteredConversations(filters) {
        try {
            const response = await this.getAll(filters);
            return response.success ? response.conversations : [];
        } catch (error) {
            console.error('Error filtering conversations:', error);
            return [];
        }
    }

    /**
     * Escalate a conversation
     * @param {string} id - The conversation ID
     * @returns {Promise<Object>} Result object with success status and message
     */
    async escalateConversation(id) {
        try {
            const response = await this.apiRequest(`${this.baseURL}/${id}/escalate`, {
                method: 'POST'
            });

            if (response.success) {
                // Invalidate cache
                this.cache = null;
                toast.success('Conversation escalated successfully');
                return response;
            } else {
                throw new Error(response.message || 'Failed to escalate conversation');
            }
        } catch (error) {
            console.error('Error escalating conversation:', error);
            toast.error('Failed to escalate conversation');
            return { success: false, message: error.message };
        }
    }

    /**
     * Get conversation statistics
     * @returns {Promise<Object>} Statistics object
     */
    async getStats() {
        try {
            const response = await this.apiRequest(`${this.baseURL}/stats`);
            
            if (response.success) {
                return response.stats;
            } else {
                throw new Error(response.message || 'Failed to get statistics');
            }
        } catch (error) {
            console.error('Error getting stats:', error);
            return {
                total: 0,
                recent_30_days: 0,
                by_sentiment: { positive: 0, neutral: 0, negative: 0 },
                by_status: { resolved: 0, pending: 0, escalated: 0 },
                by_user_type: { student: 0, faculty: 0, staff: 0 },
                by_department: {}
            };
        }
    }

    /**
     * Get conversations by sentiment
     * @param {string} sentiment - The sentiment to filter by
     * @returns {Promise<Array>} Array of conversations with the specified sentiment
     */
    async getBySentiment(sentiment) {
        return await this.getFilteredConversations({ sentiment });
    }

    /**
     * Get conversations by status
     * @param {string} status - The status to filter by
     * @returns {Promise<Array>} Array of conversations with the specified status
     */
    async getByStatus(status) {
        return await this.getFilteredConversations({ status });
    }

    /**
     * Get conversations by department
     * @param {string} department - The department to filter by
     * @returns {Promise<Array>} Array of conversations for the specified department
     */
    async getByDepartment(department) {
        // Note: This would require backend support for department filtering
        return await this.getFilteredConversations({ department });
    }

    /**
     * Get recent conversations
     * @param {number} limit - Maximum number of conversations to return
     * @returns {Promise<Array>} Array of recent conversations
     */
    async getRecent(limit = 10) {
        try {
            const response = await this.getAll({ per_page: limit });
            return response.success ? response.conversations : [];
        } catch (error) {
            console.error('Error getting recent conversations:', error);
            return [];
        }
    }

    /**
     * Export conversations to CSV
     * @param {Object} filters - Export filters (optional)
     * @returns {Promise<string|null>} CSV content or null if failed
     */
    async exportToCSV(filters = {}) {
        try {
            const response = await this.apiRequest(`${this.baseURL}/export`, {
                method: 'GET'
            });

            if (response.success) {
                return {
                    content: response.csv_content,
                    filename: response.filename
                };
            } else {
                throw new Error(response.message || 'Failed to export conversations');
            }
        } catch (error) {
            console.error('Error exporting conversations:', error);
            toast.error('Failed to export conversations');
            return null;
        }
    }

    /**
     * Download CSV export
     * @param {Object} filters - Export filters (optional)
     */
    async downloadCSV(filters = {}) {
        try {
            const exportData = await this.exportToCSV(filters);
            
            if (exportData) {
                const blob = new Blob([exportData.content], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = exportData.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                toast.success('Conversations exported successfully');
            }
        } catch (error) {
            console.error('Error downloading CSV:', error);
            toast.error('Failed to download export');
        }
    }

    /**
     * Get conversation trends over time
     * @param {string} period - Time period ('day', 'week', 'month')
     * @returns {Promise<Array>} Array of trend data
     */
    async getTrends(period = 'week') {
        try {
            const response = await this.apiRequest(`${this.baseURL}/trends?period=${period}`);
            
            if (response.success) {
                return response.trends;
            } else {
                throw new Error(response.message || 'Failed to get trends');
            }
        } catch (error) {
            console.error('Error getting trends:', error);
            return [];
        }
    }

    /**
     * Initialize sample data (admin only)
     * @returns {Promise<Object>} Result object
     */
    async initializeSampleData() {
        try {
            const response = await this.apiRequest(`${this.baseURL}/initialize-sample-data`, {
                method: 'POST'
            });

            if (response.success) {
                // Invalidate cache
                this.cache = null;
                toast.success('Sample data initialized successfully');
                return response;
            } else {
                throw new Error(response.message || 'Failed to initialize sample data');
            }
        } catch (error) {
            console.error('Error initializing sample data:', error);
            toast.error('Failed to initialize sample data');
            return { success: false, message: error.message };
        }
    }

    /**
     * Get average response time (placeholder - would require backend implementation)
     * @returns {Promise<number>} Average response time in seconds
     */
    async getAverageResponseTime() {
        // This would require backend implementation to track response times
        // For now, return a placeholder value
        return Math.floor(Math.random() * 25) + 5; // 5-30 seconds
    }

    /**
     * Validate conversation data before submission
     * @param {Object} data - Conversation data to validate
     * @returns {Object} Validation result
     */
    validateConversationData(data) {
        const errors = [];

        if (!data.user) {
            errors.push('User information is required');
        } else {
            if (!data.user.name || !data.user.name.trim()) {
                errors.push('User name is required');
            }
            if (!data.user.email || !data.user.email.trim()) {
                errors.push('User email is required');
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.user.email)) {
                errors.push('Valid email address is required');
            }
        }

        if (!data.message || !data.message.trim()) {
            errors.push('Message is required');
        }

        if (!data.response || !data.response.trim()) {
            errors.push('Response is required');
        }

        if (data.sentiment && !['Positive', 'Neutral', 'Negative'].includes(data.sentiment)) {
            errors.push('Invalid sentiment value');
        }

        if (data.status && !['Resolved', 'Pending', 'Escalated'].includes(data.status)) {
            errors.push('Invalid status value');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Clear cache (useful for testing or manual cache invalidation)
     */
    clearCache() {
        this.cache = null;
        this.lastFetch = null;
    }

    /**
     * Get cache status
     * @returns {Object} Cache status information
     */
    getCacheStatus() {
        return {
            hasCache: !!this.cache,
            lastFetch: this.lastFetch,
            cacheAge: this.lastFetch ? Date.now() - this.lastFetch : null,
            isExpired: this.lastFetch ? (Date.now() - this.lastFetch) > this.cacheTimeout : true
        };
    }
}