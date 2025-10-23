/**
 * UsageStatsManager.js
 * Handles fetching and rendering usage statistics for Sub Admin dashboard
 * Office-specific analytics and metrics
 */
class UsageStatsManager {
    constructor() {
        this.baseUrl = '/api/sub-admin/usage';
        this.charts = {};
        this.cachedData = null;
        this.cacheExpiry = null;
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes cache
        this.filterDate = null; // Single date filter
    }

    /**
     * Initialize the usage stats manager
     */
    async initialize() {
        try {
            console.log('Initializing UsageStatsManager...');
            
            // Load all statistics
            await this.loadOverviewStats();
            await this.loadTimeOfDayChart();
            await this.loadTopCategories();
            
            console.log('UsageStatsManager initialized successfully');
        } catch (error) {
            console.error('Error initializing UsageStatsManager:', error);
            this.showError('Failed to load usage statistics');
        }
    }

    /**
     * Load overview KPI statistics
     */
    async loadOverviewStats() {
        try {
            const params = new URLSearchParams();
            if (this.filterDate) {
                params.append('filter_date', this.filterDate);
            }
            const query = params.toString() ? `?${params.toString()}` : '';
            
            const response = await fetch(`${this.baseUrl}/overview${query}`, {
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
                this.renderOverviewKPIs(result.data);
            } else {
                throw new Error(result.message || 'Failed to load overview stats');
            }
        } catch (error) {
            console.error('Error loading overview stats:', error);
            this.renderOverviewKPIs(this.getDefaultOverviewData());
        }
    }

    /**
     * Render overview KPI cards
     */
    renderOverviewKPIs(data) {
        // Total Sessions
        const totalSessionsEl = document.getElementById('totalSessions');
        if (totalSessionsEl) {
            totalSessionsEl.textContent = this.formatNumber(data.totalSessions || 0);
        }

        // Average Session Duration
        const avgDurationEl = document.getElementById('avgSessionDuration');
        if (avgDurationEl) {
            avgDurationEl.textContent = data.avgSessionDuration || '0s';
        }

        // Response Rate
        const responseRateEl = document.getElementById('responseRate');
        if (responseRateEl) {
            responseRateEl.textContent = `${data.responseRate || 0}%`;
        }

        // Success Rate
        const successRateEl = document.getElementById('successRate');
        if (successRateEl) {
            successRateEl.textContent = `${data.successRate || 0}%`;
        }

        // Update trend indicators (optional - can be calculated from historical data)
        this.updateTrendIndicators(data);
    }

    /**
     * Load usage by time of day chart
     */
    async loadTimeOfDayChart() {
        try {
            const params = new URLSearchParams();
            if (this.filterDate) {
                params.append('filter_date', this.filterDate);
            }
            const query = params.toString() ? `?${params.toString()}` : '';
            
            const response = await fetch(`${this.baseUrl}/time-of-day${query}`, {
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
                this.renderTimeOfDayChart(result.data);
            } else {
                throw new Error(result.message || 'Failed to load time of day data');
            }
        } catch (error) {
            console.error('Error loading time of day chart:', error);
            this.renderTimeOfDayChart(this.getDefaultTimeOfDayData());
        }
    }

    /**
     * Render time of day bar chart
     */
    renderTimeOfDayChart(data) {
        const canvas = document.getElementById('timeOfDayChart');
        if (!canvas) {
            console.warn('timeOfDayChart canvas not found');
            return;
        }

        // Destroy existing chart if it exists
        if (this.charts.timeOfDay) {
            this.charts.timeOfDay.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.timeOfDay = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || ['Morning', 'Afternoon', 'Evening', 'Night'],
                datasets: [{
                    label: 'Usage Count',
                    data: data.counts || [0, 0, 0, 0],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',   // Morning - Blue
                        'rgba(251, 191, 36, 0.8)',   // Afternoon - Yellow
                        'rgba(249, 115, 22, 0.8)',   // Evening - Orange
                        'rgba(99, 102, 241, 0.8)'    // Night - Indigo
                    ],
                    borderColor: [
                        'rgba(59, 130, 246, 1)',
                        'rgba(251, 191, 36, 1)',
                        'rgba(249, 115, 22, 1)',
                        'rgba(99, 102, 241, 1)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return `Queries: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            font: {
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    /**
     * Load top query categories
     */
    async loadTopCategories() {
        try {
            const params = new URLSearchParams({ limit: 10 });
            if (this.filterDate) {
                params.append('filter_date', this.filterDate);
            }
            const query = params.toString() ? `?${params.toString()}` : '';
            
            const response = await fetch(`${this.baseUrl}/top-categories${query}`, {
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
                this.renderTopCategories(result.data);
            } else {
                throw new Error(result.message || 'Failed to load top categories');
            }
        } catch (error) {
            console.error('Error loading top categories:', error);
            this.renderTopCategories(this.getDefaultCategoriesData());
        }
    }

    /**
     * Render top query categories list
     */
    renderTopCategories(data) {
        const container = document.getElementById('queryCategoriesChart');
        if (!container) {
            console.warn('queryCategoriesChart container not found');
            return;
        }

        const categories = data.categories || [];
        
        if (categories.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-2"></i>
                    <p>No category data available</p>
                </div>
            `;
            return;
        }

        let html = '<div class="category-list">';
        
        categories.forEach((category, index) => {
            const barWidth = (category.count / categories[0].count * 100);
            
            html += `
                <div class="query-category-item">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div class="category-name">
                            <span class="badge bg-primary me-2">${index + 1}</span>
                            ${this.escapeHtml(category.name)}
                        </div>
                        <div class="category-count text-muted">
                            ${category.count} queries
                        </div>
                    </div>
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-primary" role="progressbar" 
                             style="width: ${barWidth}%" 
                             aria-valuenow="${category.count}" 
                             aria-valuemin="0" 
                             aria-valuemax="${categories[0].count}">
                        </div>
                    </div>
                    <div class="text-end mt-1">
                        <small class="text-muted">${category.percentage}%</small>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Update trend indicators (growth percentages)
     */
    updateTrendIndicators(data) {
        // This would typically compare current data with previous period
        // For now, we'll use placeholder logic
        
        // You can calculate trends by comparing with historical data
        // Example: const growthRate = ((current - previous) / previous) * 100;
        
        // For demonstration, we'll keep the existing static values in HTML
        // In production, you'd fetch historical data and calculate actual trends
    }

    /**
     * Export usage statistics to CSV
     */
    async exportUsageStats() {
        try {
            const response = await fetch(`${this.baseUrl}/export`, {
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
                // Create and download CSV file
                const blob = new Blob([result.data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = result.filename || 'usage_stats.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showSuccess('Usage statistics exported successfully');
            } else {
                throw new Error(result.message || 'Export failed');
            }
        } catch (error) {
            console.error('Error exporting usage stats:', error);
            this.showError('Failed to export usage statistics');
        }
    }

    /**
     * Refresh all statistics
     */
    async refresh() {
        await this.initialize();
    }

    /**
     * Show success toast
     */
    showSuccess(message) {
        if (window.UIManager && window.UIManager.showToast) {
            window.UIManager.showToast(message, 'success');
        } else {
            alert(message);
        }
    }

    /**
     * Show error toast
     */
    showError(message) {
        if (window.UIManager && window.UIManager.showToast) {
            window.UIManager.showToast(message, 'error');
        } else {
            console.error(message);
        }
    }

    /**
     * Format large numbers with commas
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
     * Default overview data (fallback)
     */
    getDefaultOverviewData() {
        return {
            totalSessions: 0,
            avgSessionDuration: '0s',
            avgSessionDurationSeconds: 0,
            responseRate: 0,
            successRate: 0,
            totalUserMessages: 0,
            totalBotResponses: 0,
            resolvedQueries: 0,
            escalatedQueries: 0
        };
    }

    /**
     * Default time of day data (fallback)
     */
    getDefaultTimeOfDayData() {
        return {
            labels: ['Morning', 'Afternoon', 'Evening', 'Night'],
            counts: [0, 0, 0, 0]
        };
    }

    /**
     * Default categories data (fallback)
     */
    getDefaultCategoriesData() {
        return {
            categories: [],
            totalConversations: 0
        };
    }

    /**
     * Set single-date filter for all usage statistics
     */
    async setDateFilter(filterDate) {
        if (this.filterDate !== filterDate) {
            this.filterDate = filterDate;
            this.clearCache();
            // Reload all statistics with the filter
            await this.loadOverviewStats();
            await this.loadTimeOfDayChart();
            await this.loadTopCategories();
        }
    }

    /**
     * Clear single-date filter
     */
    async clearDateFilter() {
        if (this.filterDate !== null) {
            this.filterDate = null;
            this.clearCache();
            // Reload all statistics without the filter
            await this.loadOverviewStats();
            await this.loadTimeOfDayChart();
            await this.loadTopCategories();
        }
    }

    /**
     * Clear cached data
     */
    clearCache() {
        this.cachedData = null;
        this.cacheExpiry = null;
    }

    /**
     * Destroy all charts (cleanup)
     */
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Export globally
window.UsageStatsManager = UsageStatsManager;

