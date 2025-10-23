/**
 * UsageStatsManager - Comprehensive usage statistics management for EduChat Admin Portal
 * Handles fetching, processing, and displaying chatbot usage analytics from MongoDB
 */
class UsageStatsManager {
    constructor() {
        this.baseURL = '/api/admin/usage-stats';
        this.cache = new Map();
        this.cacheTimeout = 2 * 60 * 1000; // 2 minutes for faster updates
        this.currentPeriod = 'daily';
        this.currentDateRange = null;
        this.trendDateFilter = null; // Single date filter for Conversation Trends
        this.officeDateFilter = null; // Single date filter for Office Performance
        this.stats = null;
        this.isLoading = false;
        this.loadingPromise = null;
        this.storageKey = 'usage_stats_cache';
        this.storageTimeout = 10 * 60 * 1000; // 10 minutes for browser storage
        
        // Office mappings for charts and performance
        this.offices = [
            { key: 'guidance', name: 'Guidance Office' },
            { key: 'registrar', name: 'Registrar Office' },
            { key: 'admissions', name: 'Admissions Office' },
            { key: 'ict', name: 'ICT Office' },
            { key: 'osa', name: 'Office of the Student Affairs(OSA)' }
        ];
    }

    /**
     * Get authentication headers for API requests
     */
    getAuthHeaders() {
        const token = localStorage.getItem('admin_token');
        if (!token) {
            // Redirect to login if no token
            window.location.href = '/';
            throw new Error('No authentication token found');
        }
        
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Initialize the usage stats manager with optimized loading
     */
    async initialize() {
        try {
            // Check for stored data first
            const storedData = this.loadFromStorage();
            if (storedData) {
                console.log('Loading from browser storage - instant display');
                this.stats = storedData;
                await this.updateUIFromStoredData(storedData);
                this.showSuccess('Data loaded instantly from cache!');
                
                // Load fresh data in background
                this.loadAllStats();
            } else {
                // No stored data, load normally
                await this.preloadCriticalData();
                await this.loadAllStats();
            }
            
            this.setupEventListeners();
            console.log('UsageStatsManager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize UsageStatsManager:', error);
            this.showError('Failed to load usage statistics');
        }
    }

    /**
     * Preload critical data for faster initial display
     */
    async preloadCriticalData() {
        try {
            // Load overview stats first (most important)
            const overviewStats = await this.fetchOverviewStats();
            await this.updateKPICards(overviewStats);
            
            // Show initial success
            this.showSuccess('Critical data loaded successfully!');
        } catch (error) {
            console.error('Error preloading critical data:', error);
        }
    }

    /**
     * Update UI from stored data for instant display
     */
    async updateUIFromStoredData(storedData) {
        try {
            if (storedData.overview) {
                await this.updateKPICards(storedData.overview);
            }
            if (storedData.trends) {
                this.updateTrendsChart(storedData.trends);
            }
            if (storedData.offices) {
                this.updateOfficeChart(storedData.offices);
            }
            if (storedData.detailed) {
                this.updateDetailedTable(storedData.detailed);
            }
        } catch (error) {
            console.error('Error updating UI from stored data:', error);
        }
    }

    /**
     * Load all statistics from the backend with optimized performance
     */
    async loadAllStats() {
        // Prevent duplicate requests
        if (this.isLoading) {
            return this.loadingPromise;
        }

        this.isLoading = true;
        this.loadingPromise = this._performLoadAllStats();
        
        try {
            const result = await this.loadingPromise;
            return result;
        } finally {
            this.isLoading = false;
            this.loadingPromise = null;
        }
    }

    /**
     * Internal method to perform the actual loading
     */
    async _performLoadAllStats() {
        try {
            this.showLoading(true);
            
            // Load all data in parallel for faster loading
            const [overviewStats, trendsData, officeStats, detailedStats] = await Promise.all([
                this.fetchOverviewStats(),
                this.fetchConversationTrends(),
                this.fetchOfficePerformance(),
                this.fetchDetailedStats()
            ]);
            
            // Combine all data
            this.stats = {
                overview: overviewStats,
                trends: trendsData,
                offices: officeStats,
                detailed: detailedStats
            };
            
            // Save to browser storage for instant loading on refresh
            this.saveToStorage(this.stats);
            
            // Update UI
            await this.updateKPICards(overviewStats);
            this.updateTrendsChart(trendsData);
            this.updateOfficeChart(officeStats);
            this.updateDetailedTable(detailedStats);
            
            // Show success notification
            this.showSuccess('Usage statistics loaded successfully!');
            
        } catch (error) {
            console.error('Error loading stats:', error);
            
            // Handle authentication errors
            if (error.message.includes('401') || error.message.includes('UNAUTHORIZED')) {
                this.showError('Authentication failed. Please login again.');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
            } else {
                this.showError('Failed to load statistics');
            }
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Fetch overview statistics from backend
     */
    async fetchOverviewStats() {
        const cacheKey = `overview_${this.currentPeriod}_${this.getDateRangeKey()}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        const params = new URLSearchParams({
            type: 'overview',
            period: this.currentPeriod
        });

        if (this.currentDateRange) {
            params.append('start_date', this.currentDateRange.start);
            params.append('end_date', this.currentDateRange.end);
        }

        const response = await fetch(`${this.baseURL}?${params}`, {
            headers: this.getAuthHeaders(),
            cache: 'default' // Use browser caching
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Cache the result with longer timeout for overview stats
        this.cache.set(cacheKey, {
            data: data,
            timestamp: Date.now()
        });

        return data;
    }

    /**
     * Fetch conversation trends data
     */
    async fetchConversationTrends() {
        const params = new URLSearchParams({
            type: 'trends',
            period: this.currentPeriod
        });

        // Use single date filter if set, otherwise use date range
        if (this.trendDateFilter) {
            params.append('filter_date', this.trendDateFilter);
        } else if (this.currentDateRange) {
            params.append('start_date', this.currentDateRange.start);
            params.append('end_date', this.currentDateRange.end);
        }

        const response = await fetch(`${this.baseURL}?${params}`, {
            headers: this.getAuthHeaders()
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Fetch office performance data
     */
    async fetchOfficePerformance() {
        const params = new URLSearchParams({
            type: 'office_performance',
            period: this.currentPeriod
        });

        // Use single date filter if set, otherwise use date range
        if (this.officeDateFilter) {
            params.append('filter_date', this.officeDateFilter);
        } else if (this.currentDateRange) {
            params.append('start_date', this.currentDateRange.start);
            params.append('end_date', this.currentDateRange.end);
        }

        const response = await fetch(`${this.baseURL}?${params}`, {
            headers: this.getAuthHeaders()
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Fetch detailed statistics
     */
    async fetchDetailedStats() {
        const params = new URLSearchParams({
            type: 'detailed',
            period: this.currentPeriod
        });

        if (this.currentDateRange) {
            params.append('start_date', this.currentDateRange.start);
            params.append('end_date', this.currentDateRange.end);
        }

        const response = await fetch(`${this.baseURL}?${params}`, {
            headers: this.getAuthHeaders()
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Update KPI cards with overview statistics
     */
    async updateKPICards(stats) {
        if (!stats || !stats.success) {
            console.error('Invalid stats data for KPI cards');
            return;
        }

        const data = stats.data;
        
        // Update total conversations
        const totalConversationsEl = document.getElementById('total-conversations');
        if (totalConversationsEl) {
            totalConversationsEl.textContent = this.formatNumber(data.totalConversations || 0);
        }

        // Update unique users - fetch from dashboard KPI to ensure consistency with dashboard
        const uniqueUsersEl = document.getElementById('unique-users');
        if (uniqueUsersEl) {
            try {
                const dashboardKPIResponse = await fetch('/api/dashboard/kpis');
                if (dashboardKPIResponse.ok) {
                    const dashboardKPI = await dashboardKPIResponse.json();
                    uniqueUsersEl.textContent = this.formatNumber(dashboardKPI.uniqueUsers || 0);
                } else {
                    // Fallback to local stats data if dashboard KPI is unavailable
                    uniqueUsersEl.textContent = this.formatNumber(data.uniqueUsers || 0);
                }
            } catch (error) {
                console.error('Error fetching dashboard KPI for unique users:', error);
                // Fallback to local stats data
                uniqueUsersEl.textContent = this.formatNumber(data.uniqueUsers || 0);
            }
        }

        // Update average satisfaction
        const avgSatisfactionEl = document.getElementById('avg-satisfaction');
        if (avgSatisfactionEl) {
            avgSatisfactionEl.textContent = (data.avgSatisfaction || 0).toFixed(1);
        }

        // Update resolution rate
        const resolutionRateEl = document.getElementById('resolution-rate');
        if (resolutionRateEl) {
            resolutionRateEl.textContent = (data.resolutionRate || 0).toFixed(1) + '%';
        }

        // Update trend indicators
        this.updateTrendIndicators(data.trends || {});
    }

    /**
     * Update trend indicators in KPI cards
     */
    updateTrendIndicators(trends) {
        const indicators = [
            { selector: '.stat-card:nth-child(1) .stat-change', value: trends.conversations || 0 },
            { selector: '.stat-card:nth-child(2) .stat-change', value: trends.users || 0 },
            { selector: '.stat-card:nth-child(3) .stat-change', value: trends.satisfaction || 0 },
            { selector: '.stat-card:nth-child(4) .stat-change', value: trends.resolution || 0 }
        ];

        indicators.forEach(indicator => {
            const element = document.querySelector(indicator.selector);
            if (element) {
                const value = indicator.value;
                const isPositive = value >= 0;
                
                element.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
                element.innerHTML = `
                    <i class="fas fa-${isPositive ? 'arrow-up' : 'arrow-down'}"></i>
                    ${isPositive ? '+' : ''}${value.toFixed(1)}%
                `;
            }
        });
    }

    /**
     * Update trends chart
     */
    updateTrendsChart(trendsData) {
        if (!trendsData || !trendsData.success) {
            console.warn('Invalid trends data provided');
            return;
        }

        if (!window.trendsChart) {
            console.warn('Trends chart not initialized yet');
            return;
        }

        const data = trendsData.data;
        
        try {
            window.trendsChart.data.labels = data.labels || [];
            window.trendsChart.data.datasets[0].data = data.values || [];
            window.trendsChart.data.datasets[0].label = `Conversations (${this.currentPeriod})`;
            
            // Update chart colors based on period
            const colors = this.getChartColors(this.currentPeriod);
            window.trendsChart.data.datasets[0].borderColor = colors.border;
            window.trendsChart.data.datasets[0].backgroundColor = colors.background;
            
            window.trendsChart.update('none');
        } catch (error) {
            console.error('Error updating trends chart:', error);
        }
    }

    /**
     * Update office performance chart
     */
    updateOfficeChart(officeData) {
        if (!officeData || !officeData.success) {
            console.warn('Invalid office data provided');
            return;
        }

        if (!window.departmentsChart) {
            console.warn('Departments chart not initialized yet');
            return;
        }

        const data = officeData.data;
        
        try {
            window.departmentsChart.data.labels = data.labels || [];
            window.departmentsChart.data.datasets[0].data = data.values || [];
            
            // Use different colors for each office
            const colors = [
                'rgba(25, 118, 210, 0.8)',   // Blue
                'rgba(76, 175, 80, 0.8)',    // Green
                'rgba(255, 193, 7, 0.8)',    // Yellow
                'rgba(233, 30, 99, 0.8)',    // Pink
                'rgba(156, 39, 176, 0.8)'    // Purple
            ];
            
            window.departmentsChart.data.datasets[0].backgroundColor = colors.slice(0, data.labels.length);
            window.departmentsChart.update('none');
        } catch (error) {
            console.error('Error updating office chart:', error);
        }
    }

    /**
     * Update detailed statistics table - now shows overall statistics only
     */
    updateDetailedTable(detailedData) {
        if (!detailedData || !detailedData.success) {
            return;
        }

        const tbody = document.querySelector('#stats-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        // Show overall statistics instead of office-specific data
        const overallStats = this.stats?.overview?.data || {};
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${this.formatNumber(overallStats.totalConversations || 0)}</td>
            <td>${this.formatNumber(overallStats.uniqueUsers || 0)}</td>
            <td>${this.formatDuration(overallStats.avgDuration || 0)}</td>
            <td>
                <div class="d-flex align-items-center">
                    <span class="me-1">${(overallStats.avgSatisfaction || 0).toFixed(1)}</span>
                    <div class="stars-rating">
                        ${this.generateStarsHTML(overallStats.avgSatisfaction || 0)}
                    </div>
                </div>
            </td>
            <td>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar" role="progressbar" 
                         style="width: ${overallStats.resolutionRate || 0}%"
                         aria-valuenow="${overallStats.resolutionRate || 0}" 
                         aria-valuemin="0" aria-valuemax="100">
                        ${(overallStats.resolutionRate || 0).toFixed(1)}%
                    </div>
                </div>
            </td>
            <td>
                <span class="trend-indicator positive">
                    <i class="fas fa-chart-line"></i>
                    Overall
                </span>
            </td>
        `;
        
        tbody.appendChild(row);
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Period selector buttons
        document.querySelectorAll('.period-buttons .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.period-buttons .btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentPeriod = e.target.dataset.period;
                this.loadAllStats();
            });
        });

        // Date range inputs
        const startDateInput = document.getElementById('start-date');
        const endDateInput = document.getElementById('end-date');
        
        if (startDateInput && endDateInput) {
            // Set default date range (last 7 days)
            const today = new Date();
            const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
            
            startDateInput.value = lastWeek.toISOString().split('T')[0];
            endDateInput.value = today.toISOString().split('T')[0];
            
            this.currentDateRange = {
                start: startDateInput.value,
                end: endDateInput.value
            };
        }

        // Table filter and search removed - no longer needed for overall stats
    }

    /**
     * Apply date range filter
     */
    applyDateRange() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        if (startDate && endDate) {
            this.currentDateRange = {
                start: startDate,
                end: endDate
            };
            this.loadAllStats();
        }
    }

    // Filter and search functions removed - no longer needed for overall stats

    /**
     * Export statistics to CSV
     */
    async exportToCSV() {
        try {
            const response = await fetch(`${this.baseURL}/export?period=${this.currentPeriod}`, {
                headers: this.getAuthHeaders()
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.downloadCSV(data.csv, data.filename || 'usage_statistics.csv');
                return data.csv;
            } else {
                throw new Error(data.message || 'Export failed');
            }
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    }

    /**
     * Download CSV file
     */
    downloadCSV(csvContent, filename) {
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    /**
     * Get current statistics (for external access)
     */
    getCurrentStats() {
        return this.stats;
    }

    /**
     * Get usage by time data for charts
     */
    getUsageByTimeData(period) {
        if (!this.stats || !this.stats.trends) {
            return { labels: [], data: [] };
        }
        
        return {
            labels: this.stats.trends.data.labels || [],
            data: this.stats.trends.data.values || []
        };
    }

    /**
     * Get department stats for charts
     */
    getDepartmentStats() {
        if (!this.stats || !this.stats.offices) {
            return { labels: [], data: [] };
        }
        
        return {
            labels: this.stats.offices.data.labels || [],
            data: this.stats.offices.data.values || []
        };
    }

    /**
     * Get detailed office performance data
     */
    getOfficePerformanceDetails() {
        if (!this.stats || !this.stats.offices || !this.stats.offices.data.details) {
            return {};
        }
        
        return this.stats.offices.data.details;
    }

    // Utility methods

    /**
     * Format numbers with commas
     */
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    /**
     * Format duration in seconds to readable format
     */
    formatDuration(seconds) {
        if (seconds < 60) {
            return `${seconds}s`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}m ${remainingSeconds}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
    }

    /**
     * Generate stars HTML for rating display
     */
    generateStarsHTML(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        
        let html = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            html += '<i class="fas fa-star text-warning"></i>';
        }
        
        // Half star
        if (hasHalfStar) {
            html += '<i class="fas fa-star-half-alt text-warning"></i>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            html += '<i class="far fa-star text-muted"></i>';
        }
        
        return html;
    }

    /**
     * Get chart colors based on period
     */
    getChartColors(period) {
        const colorMap = {
            daily: {
                border: '#1976d2',
                background: 'rgba(25, 118, 210, 0.1)'
            },
            weekly: {
                border: '#388e3c',
                background: 'rgba(56, 142, 60, 0.1)'
            },
            monthly: {
                border: '#f57c00',
                background: 'rgba(245, 124, 0, 0.1)'
            }
        };
        
        return colorMap[period] || colorMap.daily;
    }

    /**
     * Get office color for indicators
     */
    getOfficeColor(officeKey) {
        const colorMap = {
            guidance: '#1976d2',
            registrar: '#388e3c',
            admissions: '#f57c00',
            ict: '#7b1fa2',
            osa: '#d32f2f'
        };
        
        return colorMap[officeKey] || '#6c757d';
    }

    /**
     * Get date range key for caching
     */
    getDateRangeKey() {
        if (!this.currentDateRange) return 'default';
        return `${this.currentDateRange.start}_${this.currentDateRange.end}`;
    }

    /**
     * Clear cache for faster updates
     */
    clearCache() {
        this.cache.clear();
        console.log('Cache cleared for faster updates');
    }

    /**
     * Get cached data if available
     */
    getCachedData(key) {
        if (this.cache.has(key)) {
            const cached = this.cache.get(key);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }
        return null;
    }

    /**
     * Set cached data
     */
    setCachedData(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Save data to browser storage for persistence across refreshes
     */
    saveToStorage(data) {
        try {
            const storageData = {
                data: data,
                timestamp: Date.now(),
                period: this.currentPeriod,
                dateRange: this.currentDateRange
            };
            localStorage.setItem(this.storageKey, JSON.stringify(storageData));
            console.log('Data saved to browser storage');
        } catch (error) {
            console.error('Failed to save to storage:', error);
        }
    }

    /**
     * Load data from browser storage
     */
    loadFromStorage() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (!stored) return null;

            const storageData = JSON.parse(stored);
            const now = Date.now();
            
            // Check if data is still valid
            if (now - storageData.timestamp < this.storageTimeout) {
                // Check if period/date range matches
                if (storageData.period === this.currentPeriod && 
                    JSON.stringify(storageData.dateRange) === JSON.stringify(this.currentDateRange)) {
                    console.log('Loading data from browser storage');
                    return storageData.data;
                }
            }
            
            // Clear expired data
            localStorage.removeItem(this.storageKey);
            return null;
        } catch (error) {
            console.error('Failed to load from storage:', error);
            localStorage.removeItem(this.storageKey);
            return null;
        }
    }

    /**
     * Clear browser storage
     */
    clearStorage() {
        try {
            localStorage.removeItem(this.storageKey);
            console.log('Browser storage cleared');
        } catch (error) {
            console.error('Failed to clear storage:', error);
        }
    }

    /**
     * Handle period change and clear storage if needed
     */
    setPeriod(period) {
        if (this.currentPeriod !== period) {
            this.currentPeriod = period;
            this.clearStorage(); // Clear storage for new period
            this.loadAllStats();
        }
    }

    /**
     * Handle date range change and clear storage if needed
     */
    setDateRange(startDate, endDate) {
        const newDateRange = { start: startDate, end: endDate };
        if (JSON.stringify(this.currentDateRange) !== JSON.stringify(newDateRange)) {
            this.currentDateRange = newDateRange;
            this.clearStorage(); // Clear storage for new date range
            this.loadAllStats();
        }
    }

    /**
     * Set single-date filter for Conversation Trends only
     */
    async setTrendDateFilter(filterDate) {
        if (this.trendDateFilter !== filterDate) {
            this.trendDateFilter = filterDate;
            this.clearCache(); // Clear cache for new filter
            // Reload only trends data
            const trendsData = await this.fetchConversationTrends();
            this.updateTrendsChart(trendsData);
            if (this.stats) {
                this.stats.trends = trendsData;
                this.saveToStorage(this.stats);
            }
        }
    }

    /**
     * Clear single-date filter for Conversation Trends
     */
    async clearTrendDateFilter() {
        if (this.trendDateFilter !== null) {
            this.trendDateFilter = null;
            this.clearCache(); // Clear cache
            // Reload only trends data
            const trendsData = await this.fetchConversationTrends();
            this.updateTrendsChart(trendsData);
            if (this.stats) {
                this.stats.trends = trendsData;
                this.saveToStorage(this.stats);
            }
        }
    }

    /**
     * Set single-date filter for Office Performance only
     */
    async setOfficeDateFilter(filterDate) {
        if (this.officeDateFilter !== filterDate) {
            this.officeDateFilter = filterDate;
            this.clearCache(); // Clear cache for new filter
            // Reload only office performance data
            const officeData = await this.fetchOfficePerformance();
            this.updateOfficeChart(officeData);
            if (this.stats) {
                this.stats.offices = officeData;
                this.saveToStorage(this.stats);
            }
        }
    }

    /**
     * Clear single-date filter for Office Performance
     */
    async clearOfficeDateFilter() {
        if (this.officeDateFilter !== null) {
            this.officeDateFilter = null;
            this.clearCache(); // Clear cache
            // Reload only office performance data
            const officeData = await this.fetchOfficePerformance();
            this.updateOfficeChart(officeData);
            if (this.stats) {
                this.stats.offices = officeData;
                this.saveToStorage(this.stats);
            }
        }
    }

    /**
     * Show loading state
     */
    showLoading(show) {
        const loadingElements = document.querySelectorAll('.loading-spinner');
        loadingElements.forEach(el => {
            el.style.display = show ? 'block' : 'none';
        });
        
        // Disable interactive elements during loading
        const interactiveElements = document.querySelectorAll('.period-buttons .btn, #start-date, #end-date, #table-filter');
        interactiveElements.forEach(el => {
            el.disabled = show;
        });
    }

    /**
     * Show error message
     */
    showError(message) {
        if (window.toast) {
            window.toast.error(message);
        } else {
            console.error(message);
            alert(message);
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        if (window.toast) {
            window.toast.success(message);
        } else {
            console.log(message);
        }
    }
}

// Make the class available globally
window.UsageStatsManager = UsageStatsManager;
