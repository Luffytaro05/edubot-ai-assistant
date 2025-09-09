/**
 * UsageStatsManager - Manages usage statistics and analytics
 */
class UsageStatsManager extends BaseManager {
    constructor() {
        super('educhat_usage_stats');
        this.initializeDefaultStats();
    }

    /**
     * Initialize with default usage statistics
     */
    initializeDefaultStats() {
        if (this.data.length === 0) {
            const defaultStats = {
                totalConversations: 3456,
                uniqueUsers: 1247,
                avgSatisfaction: 4.2,
                resolutionRate: 87.5,
                usageByTime: {
                    daily: [65, 59, 80, 81, 56, 55, 40],
                    weekly: [320, 280, 350, 400, 380, 420, 390],
                    monthly: [1200, 1100, 1300, 1400, 1350, 1500, 1450]
                },
                queryCategories: {
                    'Enrollment': 35,
                    'Technical Support': 25,
                    'Academic': 20,
                    'Financial': 15,
                    'General': 5
                },
                departmentStats: {
                    'Guidance Office': 30,
                    'Registrar Office': 25,
                    'Admissions Office': 20,
                    'ICT Office': 15,
                    'OSA Office': 10
                },
                departments: {
                    'guidance': {
                        conversations: 1037,
                        users: 374,
                        avgDuration: 180,
                        satisfaction: 4.3,
                        resolutionRate: 89.2,
                        trend: 12.5
                    },
                    'registrar': {
                        conversations: 864,
                        users: 312,
                        avgDuration: 150,
                        satisfaction: 4.1,
                        resolutionRate: 85.7,
                        trend: 8.3
                    },
                    'admissions': {
                        conversations: 691,
                        users: 249,
                        avgDuration: 165,
                        satisfaction: 4.0,
                        resolutionRate: 82.1,
                        trend: 15.2
                    },
                    'ict': {
                        conversations: 518,
                        users: 187,
                        avgDuration: 200,
                        satisfaction: 4.4,
                        resolutionRate: 91.5,
                        trend: 5.7
                    },
                    'osa': {
                        conversations: 346,
                        users: 125,
                        avgDuration: 140,
                        satisfaction: 4.2,
                        resolutionRate: 88.9,
                        trend: 18.1
                    }
                }
            };

            this.add(defaultStats);
        }
    }

    /**
     * Get current stats
     */
    getCurrentStats() {
        return this.data[0] || {};
    }

    /**
     * Update stats
     */
    updateStats(updates) {
        const currentStats = this.getCurrentStats();
        if (currentStats.id) {
            return this.update(currentStats.id, updates);
        } else {
            return this.add(updates);
        }
    }

    /**
     * Get KPI data
     */
    getKPIData() {
        const stats = this.getCurrentStats();
        return {
            totalConversations: stats.totalConversations || 0,
            uniqueUsers: stats.uniqueUsers || 0,
            avgSatisfaction: stats.avgSatisfaction || 0,
            resolutionRate: stats.resolutionRate || 0
        };
    }

    /**
     * Get usage by time data
     */
    getUsageByTimeData(period = 'daily') {
        const stats = this.getCurrentStats();
        const usageData = stats.usageByTime || {};
        
        const labels = {
            daily: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            weekly: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7'],
            monthly: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul']
        };

        return {
            labels: labels[period] || labels.daily,
            data: usageData[period] || usageData.daily || []
        };
    }

    /**
     * Get query categories data
     */
    getQueryCategoriesData() {
        const stats = this.getCurrentStats();
        const categories = stats.queryCategories || {};
        
        return {
            labels: Object.keys(categories),
            data: Object.values(categories)
        };
    }

    /**
     * Get department stats
     */
    getDepartmentStats() {
        const stats = this.getCurrentStats();
        const departmentStats = stats.departmentStats || {};
        
        return {
            labels: Object.keys(departmentStats),
            data: Object.values(departmentStats)
        };
    }

    /**
     * Get weekly stats
     */
    getWeeklyStats() {
        const stats = this.getCurrentStats();
        const usageData = stats.usageByTime || {};
        return usageData.weekly || [];
    }

    /**
     * Get monthly stats
     */
    getMonthlyStats() {
        const stats = this.getCurrentStats();
        const usageData = stats.usageByTime || {};
        return usageData.monthly || [];
    }

    /**
     * Get growth percentage
     */
    getGrowthPercentage() {
        const stats = this.getCurrentStats();
        // Simulate growth calculation
        return {
            conversations: 12.5,
            users: 8.3,
            satisfaction: 2.1,
            resolution: 5.7
        };
    }

    /**
     * Export to CSV
     */
    exportToCSV(dataType = 'current') {
        const stats = this.getCurrentStats();
        let csvContent = '';
        
        switch(dataType) {
            case 'kpi':
                csvContent = 'Metric,Value\n';
                csvContent += `Total Conversations,${stats.totalConversations}\n`;
                csvContent += `Unique Users,${stats.uniqueUsers}\n`;
                csvContent += `Average Satisfaction,${stats.avgSatisfaction}\n`;
                csvContent += `Resolution Rate,${stats.resolutionRate}%\n`;
                break;
                
            case 'departments':
                csvContent = 'Department,Conversations,Users,Avg Duration,Satisfaction,Resolution Rate,Trend\n';
                Object.entries(stats.departments || {}).forEach(([dept, data]) => {
                    csvContent += `${dept},${data.conversations},${data.users},${data.avgDuration},${data.satisfaction},${data.resolutionRate}%,${data.trend}%\n`;
                });
                break;
                
            case 'categories':
                csvContent = 'Category,Count\n';
                Object.entries(stats.queryCategories || {}).forEach(([category, count]) => {
                    csvContent += `${category},${count}\n`;
                });
                break;
                
            default:
                csvContent = 'Metric,Value\n';
                csvContent += `Total Conversations,${stats.totalConversations}\n`;
                csvContent += `Unique Users,${stats.uniqueUsers}\n`;
                csvContent += `Average Satisfaction,${stats.avgSatisfaction}\n`;
                csvContent += `Resolution Rate,${stats.resolutionRate}%\n`;
        }
        
        return csvContent;
    }

    /**
     * Get chart configuration
     */
    getChartConfig(chartType) {
        const configs = {
            line: {
                type: 'line',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            },
            doughnut: {
                type: 'doughnut',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            },
            bar: {
                type: 'bar',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            }
        };
        
        return configs[chartType] || configs.line;
    }

    /**
     * Get summary stats
     */
    getSummaryStats() {
        const stats = this.getCurrentStats();
        return {
            totalConversations: stats.totalConversations || 0,
            uniqueUsers: stats.uniqueUsers || 0,
            avgSatisfaction: stats.avgSatisfaction || 0,
            resolutionRate: stats.resolutionRate || 0,
            growth: this.getGrowthPercentage()
        };
    }
}
