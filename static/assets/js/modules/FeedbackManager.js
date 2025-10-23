/**
 * FeedbackManager.js
 * Manages feedback analytics display for Admin dashboard
 * Fetches and renders feedback statistics and detailed feedback table
 */

class FeedbackManager {
    constructor() {
        this.analytics = null;
        this.feedbackData = [];
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.currentFilter = 'all';
        this.showTimezone = true; // Toggle for timezone display
    }

    /**
     * Initialize the feedback manager
     */
    async initialize() {
        console.log('Initializing FeedbackManager...');
        
        // Check authentication first
        if (!this.checkAuth()) {
            console.error('User not authenticated');
            this.showError('Authentication required. Please login again.');
            // Redirect to login page
            setTimeout(() => {
                window.location.href = '/admin/index';
            }, 2000);
            return;
        }
        
        // Test timezone conversion
        this.testTimezoneConversion();
        
        // Update current time display
        this.updateCurrentTimeDisplay();
        
        // Ensure time is always current
        this.ensureCurrentTime();
        
        // Try to sync with server time
        await this.syncTimeWithServer();
        
        await this.loadFeedbackAnalytics();
        this.setupEventListeners();
        this.renderAnalytics();
        this.renderFeedbackTable();
    }

    /**
     * Test timezone conversion
     */
    testTimezoneConversion() {
        const now = new Date();
        const philippineTimezone = 'Asia/Manila';
        
        console.log('🇵🇭 Philippine Timezone Information:');
        console.log('Target timezone:', philippineTimezone);
        console.log('Current UTC time:', now.toISOString());
        
        // Show current time in Philippine timezone
        const philippineTime = now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: philippineTimezone
        });
        console.log('Current Philippine time:', philippineTime);
        
        // Test with a sample date from the database
        const sampleDate = '2025-10-01T19:28:38.159000';
        console.log('Sample date conversion:');
        console.log('Original (UTC):', sampleDate);
        console.log('Converted to Philippine time:', this.formatDate(sampleDate));
    }

    /**
     * Update current time display
     */
    updateCurrentTimeDisplay() {
        const currentTimeElement = document.getElementById('currentTime');
        if (!currentTimeElement) return;
        
        const philippineTimezone = 'Asia/Manila';
        
        const updateTime = () => {
            // Always get the latest time
            const now = new Date();
            const timeString = now.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZone: philippineTimezone
            });
            
            // Add live indicator
            const liveIndicator = '🟢 LIVE';
            currentTimeElement.textContent = `${timeString} (${liveIndicator} Philippine Time, UTC+8)`;
        };
        
        // Update immediately
        updateTime();
        
        // Update every second for real-time display
        setInterval(updateTime, 1000);
        
        // Also update when page becomes visible (in case user switches tabs)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                updateTime();
            }
        });
        
        // Update when window regains focus
        window.addEventListener('focus', updateTime);
    }

    /**
     * Ensure time is always current
     */
    ensureCurrentTime() {
        // Force immediate time update
        const currentTimeElement = document.getElementById('currentTime');
        if (currentTimeElement) {
            const now = new Date();
            const philippineTimezone = 'Asia/Manila';
            const timeString = now.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZone: philippineTimezone
            });
        }
        
        // Update every 500ms for more frequent updates
        setInterval(() => {
            const currentTimeElement = document.getElementById('currentTime');
            if (currentTimeElement) {
                const now = new Date();
                const philippineTimezone = 'Asia/Manila';
                const timeString = now.toLocaleString('en-US', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false,
                    timeZone: philippineTimezone
                });
            }
        }, 500);
    }

    /**
     * Sync time with server for accuracy
     */
    async syncTimeWithServer() {
        try {
            // Get server time from a simple endpoint
            const response = await fetch('/api/test/feedback', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.timestamp) {
                    console.log('🕐 Server time sync:', data.timestamp);
                    // Update display with server time
                    const serverTime = new Date(data.timestamp);
                    const philippineTimezone = 'Asia/Manila';
                    const timeString = serverTime.toLocaleString('en-US', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        hour12: false,
                        timeZone: philippineTimezone
                    });
                    
                    const currentTimeElement = document.getElementById('currentTime');
                    if (currentTimeElement) {
                        currentTimeElement.textContent = `${timeString} (🟢 SYNCED Philippine Time, UTC+8)`;
                    }
                }
            }
        } catch (error) {
            console.log('Time sync not available, using local time');
        }
    }

    /**
     * Check if user is authenticated
     */
    checkAuth() {
        const token = localStorage.getItem('admin_token');
        const user = localStorage.getItem('admin_user');
        return !!(token && user);
    }

    /**
     * Load feedback analytics from API
     */
    async loadFeedbackAnalytics() {
        try {
            console.log('Attempting to fetch feedback analytics from /api/admin/feedback');
            
            // Get authentication token
            const token = localStorage.getItem('admin_token');
            if (!token) {
                console.error('No authentication token found');
                this.showError('Authentication required. Please login again.');
                return;
            }
            
            // First test if server is responding
            try {
                const testResponse = await fetch('/api/test/feedback', {
                    method: 'GET',
                    credentials: 'include'
                });
                console.log('Test route response:', testResponse.status);
            } catch (testError) {
                console.log('Test route failed:', testError);
            }
            
            // Try the main route first, then fallback to stats route
            let response;
            try {
                response = await fetch('/api/admin/feedback', {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                });
            } catch (error) {
                console.log('Main route failed, trying fallback route...');
                response = await fetch('/api/feedback/stats', {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                });
            }

            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Response error text:', errorText);
                
                // Handle authentication errors
                if (response.status === 401) {
                    console.error('Authentication failed - token may be expired');
                    this.showError('Session expired. Please login again.');
                    setTimeout(() => {
                        window.location.href = '/admin/index';
                    }, 2000);
                    return;
                }
                
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Response data:', result);

            if (result.success) {
                this.analytics = result.analytics;
                this.feedbackData = result.analytics.feedback_data;
                console.log('✅ Feedback analytics loaded from MongoDB:', this.analytics);
                console.log(`📊 Loaded ${this.feedbackData.length} feedback records from database`);
                
                // Show success message
                this.showSuccess(`Loaded ${this.feedbackData.length} feedback records from database`);
            } else {
                console.error('Failed to load feedback analytics:', result.message);
                this.showError('Failed to load feedback analytics');
            }
        } catch (error) {
            console.error('Error loading feedback analytics:', error);
            this.showError('Error loading feedback analytics from database');
            
            // Show empty state instead of mock data
            this.analytics = {
                average_rating: 0,
                total_feedback: 0,
                positive_feedback_percentage: 0,
                negative_feedback_percentage: 0,
                feedback_data: []
            };
            this.feedbackData = [];
            this.renderAnalytics();
            this.renderFeedbackTable();
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Filter buttons
        const filterButtons = document.querySelectorAll('.feedback-filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.setFilter(filter);
            });
        });

        // Pagination
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousPage());
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextPage());
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshFeedbackBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // Timezone toggle button
        const timezoneToggleBtn = document.getElementById('toggleTimezoneBtn');
        if (timezoneToggleBtn) {
            timezoneToggleBtn.addEventListener('click', () => this.toggleTimezone());
        }

        // Update time when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.ensureCurrentTime();
            }
        });

        // Update time when window regains focus
        window.addEventListener('focus', () => {
            this.ensureCurrentTime();
        });
    }

    /**
     * Render analytics KPI cards
     */
    renderAnalytics() {
        if (!this.analytics) return;

        // Update KPI cards
        this.updateKPICard('averageRating', this.analytics.average_rating, '⭐');
        this.updateKPICard('totalFeedback', this.analytics.total_feedback, '📝');
        this.updateKPICard('positiveFeedback', this.analytics.positive_feedback_percentage, '%', 'positive');
        this.updateKPICard('negativeFeedback', this.analytics.negative_feedback_percentage, '%', 'negative');
    }

    /**
     * Update a KPI card
     */
    updateKPICard(cardId, value, suffix = '', type = '') {
        const card = document.getElementById(cardId);
        if (!card) return;

        const valueElement = card.querySelector('.kpi-value');
        const suffixElement = card.querySelector('.kpi-suffix');
        
        if (valueElement) {
            valueElement.textContent = value;
        }
        if (suffixElement) {
            suffixElement.textContent = suffix;
        }

        // Add type-specific styling
        if (type === 'positive') {
            card.classList.add('kpi-positive');
        } else if (type === 'negative') {
            card.classList.add('kpi-negative');
        }
    }

    /**
     * Render feedback table
     */
    renderFeedbackTable() {
        const tableBody = document.getElementById('feedbackTableBody');
        if (!tableBody) return;

        // Filter data based on current filter
        let filteredData = this.feedbackData;
        if (this.currentFilter !== 'all') {
            filteredData = this.feedbackData.filter(item => item.sentiment === this.currentFilter);
        }

        // Calculate pagination
        const totalPages = Math.ceil(filteredData.length / this.itemsPerPage);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageData = filteredData.slice(startIndex, endIndex);

        // Clear existing content
        tableBody.innerHTML = '';

        if (pageData.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted">No feedback data available</td>
                </tr>
            `;
            return;
        }

        // Render table rows
        pageData.forEach(feedback => {
            const row = this.createFeedbackRow(feedback);
            tableBody.appendChild(row);
        });

        // Update pagination
        this.updatePagination(totalPages);
    }

    /**
     * Create a feedback table row
     */
    createFeedbackRow(feedback) {
        const row = document.createElement('tr');
        
        // Format date with proper timezone handling
        const formattedDate = this.formatDate(feedback.date);
        
        // Create rating stars
        const stars = this.createStarRating(feedback.rating);
        
        // Create sentiment badge with scores
        const sentimentBadge = this.createSentimentBadge(feedback.sentiment, feedback.sentiment_scores);
        
        row.innerHTML = `
            <td>${stars}</td>
            <td class="feedback-message">${feedback.message || 'No message'}</td>
            <td>${sentimentBadge}</td>
            <td>${formattedDate}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="feedbackManager.viewFeedback('${feedback.id}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        
        return row;
    }

    /**
     * Format date with proper timezone and locale
     */
    formatDate(dateString) {
        try {
            if (!dateString) {
                return 'No Date';
            }
            
            // Create date object - this automatically handles timezone conversion
            const date = new Date(dateString);
            
            // Check if date is valid
            if (isNaN(date.getTime())) {
                console.warn('Invalid date string:', dateString);
                return 'Invalid Date';
            }
            
            // Force Philippine timezone (UTC+8)
            const philippineTimezone = 'Asia/Manila';
            console.log('Using Philippine timezone:', philippineTimezone);
            
            // Format in Philippine timezone with explicit options
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false, // Use 24-hour format
                timeZone: philippineTimezone // Force Philippine timezone
            };
            
            // This will display in Philippine time
            const formatted = date.toLocaleString('en-US', options);
            
            // Add timezone info if enabled
            if (this.showTimezone) {
                const timezoneString = 'Philippine Time (UTC+8)';
                return `${formatted} (${timezoneString})`;
            }
            
            return formatted;
        } catch (error) {
            console.error('Error formatting date:', error, 'Input:', dateString);
            return 'Date Error';
        }
    }

    /**
     * Create star rating display
     */
    createStarRating(rating) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            if (i <= rating) {
                stars += '<i class="fas fa-star text-warning"></i>';
            } else {
                stars += '<i class="far fa-star text-muted"></i>';
            }
        }
        return `<span class="rating-display">${stars} (${rating})</span>`;
    }

    /**
     * Create sentiment badge with VADER scores tooltip
     */
    createSentimentBadge(sentiment, scores) {
        const badgeClasses = {
            'positive': 'badge bg-success',
            'negative': 'badge bg-danger',
            'neutral': 'badge bg-secondary'
        };
        
        const badgeClass = badgeClasses[sentiment] || 'badge bg-secondary';
        const sentimentLabel = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
        
        // Create tooltip with VADER scores if available
        if (scores && scores.compound !== undefined) {
            const tooltipText = `VADER Sentiment Analysis:
• Overall: ${(scores.compound * 100).toFixed(1)}% (${scores.compound >= 0.05 ? 'Positive' : scores.compound <= -0.05 ? 'Negative' : 'Neutral'})
• Positive: ${(scores.pos * 100).toFixed(1)}%
• Neutral: ${(scores.neu * 100).toFixed(1)}%
• Negative: ${(scores.neg * 100).toFixed(1)}%`;
            
            // Get sentiment icon
            const icon = sentiment === 'positive' ? '😊' : sentiment === 'negative' ? '😞' : '😐';
            
            return `<span class="${badgeClass}" 
                          style="cursor: help; position: relative;" 
                          title="${tooltipText}"
                          data-bs-toggle="tooltip" 
                          data-bs-placement="top"
                          data-bs-html="true"
                          data-bs-title="<div style='text-align: left;'><strong>VADER Sentiment Analysis</strong><br/>
                                        <small>Overall Score: <strong>${(scores.compound * 100).toFixed(1)}%</strong></small><br/>
                                        <small>Positive: ${(scores.pos * 100).toFixed(1)}%</small><br/>
                                        <small>Neutral: ${(scores.neu * 100).toFixed(1)}%</small><br/>
                                        <small>Negative: ${(scores.neg * 100).toFixed(1)}%</small></div>">
                        ${icon} ${sentimentLabel}
                    </span>`;
        }
        
        return `<span class="${badgeClass}">${sentimentLabel}</span>`;
    }

    /**
     * Update pagination controls
     */
    updatePagination(totalPages) {
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');
        const pageInfo = document.getElementById('pageInfo');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentPage <= 1;
        }
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= totalPages;
        }
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
        }
    }

    /**
     * Set filter
     */
    setFilter(filter) {
        this.currentFilter = filter;
        this.currentPage = 1;
        
        // Update filter button states
        document.querySelectorAll('.feedback-filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-filter="${filter}"]`).classList.add('active');
        
        this.renderFeedbackTable();
    }

    /**
     * Go to previous page
     */
    previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.renderFeedbackTable();
        }
    }

    /**
     * Go to next page
     */
    nextPage() {
        const filteredData = this.getFilteredData();
        const totalPages = Math.ceil(filteredData.length / this.itemsPerPage);
        
        if (this.currentPage < totalPages) {
            this.currentPage++;
            this.renderFeedbackTable();
        }
    }

    /**
     * Get filtered data
     */
    getFilteredData() {
        if (this.currentFilter === 'all') {
            return this.feedbackData;
        }
        return this.feedbackData.filter(item => item.sentiment === this.currentFilter);
    }

    /**
     * View feedback details
     */
    viewFeedback(feedbackId) {
        const feedback = this.feedbackData.find(f => f.id === feedbackId);
        if (!feedback) return;

        // Create modal or show details
        this.showFeedbackModal(feedback);
    }

    /**
     * Show feedback modal
     */
    showFeedbackModal(feedback) {
        // Create a simple modal without Bootstrap dependency
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        // Create sentiment scores HTML if available
        let sentimentScoresHtml = '';
        if (feedback.sentiment_scores && feedback.sentiment_scores.compound !== undefined) {
            const scores = feedback.sentiment_scores;
            sentimentScoresHtml = `
                <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-radius: 6px;">
                    <strong>VADER Sentiment Analysis:</strong><br>
                    <div style="margin-top: 8px;">
                        <div style="margin-bottom: 6px;">
                            <small><strong>Overall Score:</strong> ${(scores.compound * 100).toFixed(1)}%</small>
                            <div style="background: #e9ecef; height: 6px; border-radius: 3px; margin-top: 2px;">
                                <div style="background: ${scores.compound >= 0 ? '#28a745' : '#dc3545'}; height: 100%; width: ${Math.abs(scores.compound) * 100}%; border-radius: 3px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 6px;">
                            <small>😊 Positive: ${(scores.pos * 100).toFixed(1)}%</small>
                            <div style="background: #e9ecef; height: 4px; border-radius: 2px; margin-top: 2px;">
                                <div style="background: #28a745; height: 100%; width: ${scores.pos * 100}%; border-radius: 2px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 6px;">
                            <small>😐 Neutral: ${(scores.neu * 100).toFixed(1)}%</small>
                            <div style="background: #e9ecef; height: 4px; border-radius: 2px; margin-top: 2px;">
                                <div style="background: #6c757d; height: 100%; width: ${scores.neu * 100}%; border-radius: 2px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 6px;">
                            <small>😞 Negative: ${(scores.neg * 100).toFixed(1)}%</small>
                            <div style="background: #e9ecef; height: 4px; border-radius: 2px; margin-top: 2px;">
                                <div style="background: #dc3545; height: 100%; width: ${scores.neg * 100}%; border-radius: 2px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        modal.innerHTML = `
            <div style="
                background: white;
                border-radius: 8px;
                padding: 20px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h5 style="margin: 0;">Feedback Details</h5>
                    <button onclick="this.closest('.modal').remove()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #666;
                    ">&times;</button>
                </div>
                <div>
                    <div style="margin-bottom: 15px;">
                        <strong>Rating:</strong><br>
                        ${this.createStarRating(feedback.rating)}
                    </div>
                    <div style="margin-bottom: 15px;">
                        <strong>Sentiment:</strong><br>
                        ${this.createSentimentBadge(feedback.sentiment, feedback.sentiment_scores)}
                    </div>
                    ${sentimentScoresHtml}
                    <div style="margin-bottom: 15px;">
                        <strong>Date:</strong><br>
                        ${this.formatDate(feedback.date)}
                    </div>
                    <div style="margin-bottom: 15px;">
                        <strong>Message:</strong><br>
                        ${feedback.message || 'No message provided'}
                    </div>
                    ${feedback.user_id ? `
                    <div style="margin-bottom: 15px;">
                        <strong>User ID:</strong><br>
                        ${feedback.user_id}
                    </div>
                    ` : ''}
                </div>
                <div style="text-align: right; margin-top: 20px;">
                    <button onclick="this.closest('.modal').remove()" style="
                        background: #6c757d;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Close</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Refresh data
     */
    async refreshData() {
        const refreshBtn = document.getElementById('refreshFeedbackBtn');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            refreshBtn.disabled = true;
        }
        
        // Check authentication before refresh
        if (!this.checkAuth()) {
            this.showError('Authentication required. Please login again.');
            setTimeout(() => {
                window.location.href = '/admin/index';
            }, 2000);
            return;
        }
        
        await this.loadFeedbackAnalytics();
        this.renderAnalytics();
        this.renderFeedbackTable();
        
        // Update time display to latest
        this.updateCurrentTimeDisplay();
        
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
            refreshBtn.disabled = false;
        }
    }

    /**
     * Toggle timezone display
     */
    toggleTimezone() {
        this.showTimezone = !this.showTimezone;
        
        // Update button text
        const timezoneToggleText = document.getElementById('timezoneToggleText');
        if (timezoneToggleText) {
            timezoneToggleText.textContent = this.showTimezone ? 'Hide TZ' : 'Show TZ';
        }
        
        // Re-render table with new date format
        this.renderFeedbackTable();
        
        // Show feedback
        const message = this.showTimezone ? 'Philippine timezone display enabled' : 'Philippine timezone display disabled';
        this.showSuccess(message);
    }

    /**
     * Show error message
     */
    showError(message) {
        // Create simple alert for now (Bootstrap not loaded)
        console.error('Feedback Error:', message);
        
        // Create a simple notification div
        const notification = document.createElement('div');
        notification.className = 'alert alert-danger alert-dismissible fade show';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        console.log('Feedback Success:', message);
        
        // Create a simple success notification div
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.style.backgroundColor = '#d4edda';
        notification.style.borderColor = '#c3e6cb';
        notification.style.color = '#155724';
        notification.innerHTML = `
            <strong>Success:</strong> ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 3000);
    }

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.feedbackManager = new FeedbackManager();
    feedbackManager.initialize();
});
