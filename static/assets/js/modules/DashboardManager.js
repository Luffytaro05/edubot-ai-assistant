/**
 * UsageStatsManager.js
 * Handles fetching and caching of usage statistics for EduChat Admin Dashboard.
 */
class UsageStatsManager {
    constructor() {
        this.baseUrl = '/api/dashboard';
        this.cachedStats = null;
        this.cacheExpiry = null;
        this.cacheTimeout = 5 * 60 * 1000; // cache for 5 minutes
        this.activeStartDate = null;
        this.activeEndDate = null;
    }

    async getKPIData() {
        // Serve from cache if available
        if (this.cachedStats && Date.now() < this.cacheExpiry) {
            return this.cachedStats;
        }

        try {
            const params = new URLSearchParams();
            if (this.activeStartDate) params.append('start_date', this.activeStartDate);
            if (this.activeEndDate) params.append('end_date', this.activeEndDate);
            const query = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${this.baseUrl}/kpis${query}`);
            if (!response.ok) throw new Error("Failed to fetch KPI data");

            const data = await response.json();
            this.cachedStats = data;
            this.cacheExpiry = Date.now() + this.cacheTimeout;
            return data;
        } catch (error) {
            console.error("Error fetching KPI data:", error);
            return {
                uniqueUsers: 0,
                totalConversations: 0,
                resolvedQueries: 0,
                escalatedIssues: 0
            };
        }
    }

    async getGrowthPercentage() {
        // You can extend this with historical growth calculation
        return {
            users: 0,
            conversations: 0,
            resolution: 0,
            escalated: 0
        };
    }

    async getUsageByTimeData(period = "daily") {
        try {
            const params = new URLSearchParams();
            if (this.activeStartDate) params.append('start_date', this.activeStartDate);
            if (this.activeEndDate) params.append('end_date', this.activeEndDate);
            const query = params.toString() ? `?${params.toString()}` : '';
            const response = await fetch(`${this.baseUrl}/usage/${period}${query}`);
            if (!response.ok) throw new Error("Failed to fetch usage data");
            return await response.json();
        } catch (error) {
            console.error("Error fetching usage chart data:", error);
            return { labels: [], data: [] };
        }
    }

    async getDepartmentStats() {
        try {
            const params = new URLSearchParams();
            if (this.activeStartDate) params.append('start_date', this.activeStartDate);
            if (this.activeEndDate) params.append('end_date', this.activeEndDate);
            const query = params.toString() ? `?${params.toString()}` : '';
            console.log('Fetching department stats from:', `${this.baseUrl}/departments${query}`);
            const response = await fetch(`${this.baseUrl}/departments${query}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch department stats: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            console.log('Department stats received:', data);
            
            // Validate data structure
            if (!data.labels || !data.data) {
                console.error('Invalid department data structure:', data);
                return { labels: [], data: [] };
            }
            
            return data;
        } catch (error) {
            console.error("Error fetching department chart data:", error);
            return { labels: [], data: [] };
        }
    }

    async exportToCSV(type = "kpi") {
        const data = await this.getKPIData();
        let csv = "Metric,Value\n";
        csv += `Unique Users,${data.uniqueUsers}\n`;
        csv += `Total Conversations,${data.totalConversations}\n`;
        csv += `Resolved Queries,${data.resolvedQueries}\n`;
        csv += `Escalated Issues,${data.escalatedIssues}\n`;
        return csv;
    }

    async refreshData() {
        this.cachedStats = null;
        return await this.getKPIData();
    }

    clearCache() {
        this.cachedStats = null;
        this.cacheExpiry = null;
    }

    setDateRange(startDateRaw, endDateRaw) {
        // Expect YYYY-MM-DD strings; store as-is
        this.activeStartDate = startDateRaw || null;
        this.activeEndDate = endDateRaw || null;
        this.clearCache();
    }
}

// Export globally
window.UsageStatsManager = UsageStatsManager;
