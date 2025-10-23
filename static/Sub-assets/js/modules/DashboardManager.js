/**
 * DashboardManager.js
 * Enhanced version with modern chart rendering and animations
 */

class DashboardManager {
  constructor() {
    this.baseUrl = "/api/sub-admin";
    this.weeklyChart = null;
    this.office = null;
    this.chartType = "line"; // Default chart type
    this.chartData = null; // Store chart data for type switching
    this.startDate = null; // Date range filter start
    this.endDate = null; // Date range filter end
  }

  async initialize() {
    try {
      console.log("Initializing DashboardManager...");
      
      await this.loadOfficeInfo();
      await this.loadStats();
      await this.loadWeeklyUsage();
      
      console.log("DashboardManager initialized successfully");
    } catch (error) {
      console.error("Error initializing DashboardManager:", error);
      this.showError("Failed to initialize dashboard. Please refresh the page.");
    }
  }

  async loadOfficeInfo() {
    try {
      const response = await fetch(`${this.baseUrl}/office-info`, {
        method: "GET",
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          this.office = data.office;
          console.log(`Dashboard loaded for office: ${this.office}`);
        }
      }
    } catch (error) {
      console.error("Error loading office info:", error);
    }
  }

  async loadStats() {
    try {
      const params = new URLSearchParams();
      if (this.startDate) params.append('start_date', this.startDate);
      if (this.endDate) params.append('end_date', this.endDate);
      const query = params.toString() ? `?${params.toString()}` : '';
      
      const response = await fetch(`${this.baseUrl}/stats${query}`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.stats) {
        this.updateStats(data.stats);
      } else {
        console.warn("Failed to load stats:", data);
        this.showError("Unable to load statistics");
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
      this.showError("Error loading dashboard statistics");
    }
  }

  updateStats(stats) {
    const totalUsersEl = document.getElementById("totalUsers");
    if (totalUsersEl && stats.office_users !== undefined) {
      totalUsersEl.textContent = stats.office_users.toLocaleString();
    }

    const chatbotQueriesEl = document.getElementById("chatbotQueries");
    if (chatbotQueriesEl && stats.office_conversations !== undefined) {
      chatbotQueriesEl.textContent = stats.office_conversations.toLocaleString();
    }

    const successRateEl = document.getElementById("querySuccessRate");
    if (successRateEl && stats.office_resolved_queries !== undefined && stats.office_conversations !== undefined) {
      const total = stats.office_conversations || 1;
      const resolved = stats.office_resolved_queries;
      const percentage = Math.round((resolved / total) * 100);
      successRateEl.textContent = `${percentage}%`;
    }

    const escalatedEl = document.getElementById("escalatedQueries");
    if (escalatedEl && stats.office_escalated_issues !== undefined) {
      escalatedEl.textContent = stats.office_escalated_issues.toLocaleString();
    }

    console.log("Stats updated:", stats);
  }

  async loadWeeklyUsage() {
    try {
      const params = new URLSearchParams();
      if (this.startDate) params.append('start_date', this.startDate);
      if (this.endDate) params.append('end_date', this.endDate);
      const query = params.toString() ? `?${params.toString()}` : '';
      
      const response = await fetch(`${this.baseUrl}/weekly-usage${query}`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.usage) {
        this.chartData = data.usage; // Store for later use
        this.renderWeeklyChart(data.usage, data.office);
        this.updateChartStats(data.usage);
      } else {
        console.warn("Failed to load weekly usage:", data);
        this.showError("Unable to load weekly usage chart");
      }
    } catch (error) {
      console.error("Error fetching weekly usage:", error);
      this.showError("Error loading weekly usage data");
    }
  }

  renderWeeklyChart(usageData, office) {
    const canvas = document.getElementById("weeklyChart");
    
    if (!canvas) {
      console.error("Canvas element 'weeklyChart' not found");
      return;
    }

    const ctx = canvas.getContext("2d");
    const labels = usageData.map((d) => this.formatDateLabel(d.date));
    const values = usageData.map((d) => d.count);

    // Create gradient for the chart
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(102, 126, 234, 0.8)');
    gradient.addColorStop(0.5, 'rgba(118, 75, 162, 0.4)');
    gradient.addColorStop(1, 'rgba(118, 75, 162, 0.1)');

    // Destroy existing chart if it exists
    if (this.weeklyChart) {
      this.weeklyChart.destroy();
    }

    // Determine chart configuration based on type
    const config = this.getChartConfig(labels, values, gradient, office);

    // Create new chart with animation
    this.weeklyChart = new Chart(ctx, config);

    console.log("Weekly chart rendered with data:", usageData);
  }

  getChartConfig(labels, values, gradient, office) {
    const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const textColor = isDarkMode ? '#e2e8f0' : '#475569';
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';

    const baseConfig = {
      data: {
        labels: labels,
        datasets: [
          {
            label: `${office || 'Office'} Chatbot Queries`,
            data: values,
            borderColor: '#667eea',
            backgroundColor: this.chartType === 'bar' ? gradient : (this.chartType === 'area' ? gradient : 'rgba(102, 126, 234, 0.1)'),
            fill: this.chartType !== 'line',
            tension: 0.4,
            borderWidth: 3,
            pointBackgroundColor: '#667eea',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 3,
            pointRadius: 6,
            pointHoverRadius: 9,
            pointHoverBackgroundColor: '#764ba2',
            pointHoverBorderColor: '#ffffff',
            pointHoverBorderWidth: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 2000,
          easing: 'easeInOutQuart',
          onComplete: () => {
            console.log('Chart animation complete');
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            align: 'end',
            labels: {
              font: {
                size: 13,
                family: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                weight: '500',
              },
              padding: 16,
              usePointStyle: true,
              pointStyle: 'circle',
              color: textColor,
              boxWidth: 10,
              boxHeight: 10,
            },
          },
          tooltip: {
            enabled: true,
            backgroundColor: isDarkMode ? 'rgba(30, 41, 59, 0.95)' : 'rgba(0, 0, 0, 0.85)',
            titleColor: '#ffffff',
            bodyColor: '#e2e8f0',
            borderColor: '#667eea',
            borderWidth: 2,
            titleFont: {
              size: 15,
              weight: '600',
              family: "'Inter', sans-serif",
            },
            bodyFont: {
              size: 14,
              family: "'Inter', sans-serif",
            },
            padding: 16,
            cornerRadius: 12,
            displayColors: true,
            boxWidth: 12,
            boxHeight: 12,
            boxPadding: 6,
            caretSize: 8,
            caretPadding: 12,
            callbacks: {
              title: (context) => {
                return `📅 ${context[0].label}`;
              },
              label: (context) => {
                const value = context.parsed.y;
                const plural = value !== 1 ? 'queries' : 'query';
                return `  ${value.toLocaleString()} ${plural}`;
              },
              afterLabel: (context) => {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                return `  ${percentage}% of weekly total`;
              }
            }
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: '📆 Date',
              font: {
                size: 14,
                weight: '600',
                family: "'Inter', sans-serif",
              },
              color: textColor,
              padding: { top: 10 }
            },
            grid: {
              display: false,
              drawBorder: false,
            },
            ticks: {
              font: {
                size: 12,
                weight: '500',
              },
              color: textColor,
              padding: 8,
              maxRotation: 45,
              minRotation: 0,
            },
          },
          y: {
            title: {
              display: true,
              text: '💬 Number of Queries',
              font: {
                size: 14,
                weight: '600',
                family: "'Inter', sans-serif",
              },
              color: textColor,
              padding: { bottom: 10 }
            },
            beginAtZero: true,
            ticks: {
              stepSize: Math.ceil(Math.max(...values) / 5),
              font: {
                size: 12,
                weight: '500',
              },
              color: textColor,
              padding: 10,
              callback: function(value) {
                return value.toLocaleString();
              }
            },
            grid: {
              color: gridColor,
              drawBorder: false,
              lineWidth: 1,
            },
          },
        },
        interaction: {
          intersect: false,
          mode: 'index',
        },
        hover: {
          mode: 'index',
          intersect: false,
          animationDuration: 400,
        },
      },
    };

    // Set chart type
    baseConfig.type = this.chartType === 'area' ? 'line' : this.chartType;

    return baseConfig;
  }

  formatDateLabel(dateString) {
    const date = new Date(dateString);
    const options = { month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
  }

  updateChartStats(usageData) {
    const values = usageData.map(d => d.count);
    const total = values.reduce((a, b) => a + b, 0);
    const average = Math.round(total / values.length);
    const maxValue = Math.max(...values);
    const maxIndex = values.indexOf(maxValue);
    const peakDay = this.formatDateLabel(usageData[maxIndex].date);

    // Calculate trend
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    const trendPercentage = ((secondAvg - firstAvg) / firstAvg * 100).toFixed(1);

    // Update DOM elements
    const totalEl = document.getElementById("chartTotalQueries");
    if (totalEl) totalEl.textContent = total.toLocaleString();

    const avgEl = document.getElementById("chartAvgQueries");
    if (avgEl) avgEl.textContent = average.toLocaleString();

    const peakEl = document.getElementById("chartPeakDay");
    if (peakEl) peakEl.textContent = peakDay;

    const trendEl = document.getElementById("chartTrend");
    if (trendEl) {
      const indicator = trendEl.querySelector('.trend-indicator');
      if (indicator) {
        indicator.textContent = `${trendPercentage > 0 ? '+' : ''}${trendPercentage}%`;
        indicator.className = 'trend-indicator';
        if (trendPercentage > 0) {
          indicator.classList.add('trend-up');
        } else if (trendPercentage < 0) {
          indicator.classList.add('trend-down');
        } else {
          indicator.classList.add('trend-stable');
        }
      }
    }
  }

  changeChartType(type) {
    this.chartType = type;
    if (this.chartData) {
      this.renderWeeklyChart(this.chartData, this.office);
    }
  }

  async refreshDashboard() {
    try {
      console.log("Refreshing dashboard...");
      await this.loadStats();
      await this.loadWeeklyUsage();
      this.showSuccess("Dashboard refreshed successfully");
    } catch (error) {
      console.error("Error refreshing dashboard:", error);
      this.showError("Failed to refresh dashboard");
    }
  }

  async exportDashboardData() {
    try {
      const exportData = {
        office: this.office,
        exportDate: new Date().toISOString(),
        stats: {
          totalUsers: document.getElementById("totalUsers")?.textContent || "N/A",
          chatbotQueries: document.getElementById("chatbotQueries")?.textContent || "N/A",
          successRate: document.getElementById("querySuccessRate")?.textContent || "N/A",
          escalatedQueries: document.getElementById("escalatedQueries")?.textContent || "N/A",
        },
        weeklyData: this.chartData || [],
      };

      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement("a");
      link.href = url;
      link.download = `dashboard-export-${this.office}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      URL.revokeObjectURL(url);
      
      this.showSuccess("Dashboard data exported successfully");
    } catch (error) {
      console.error("Error exporting dashboard data:", error);
      this.showError("Failed to export dashboard data");
    }
  }

  showError(message) {
    console.error(message);
    const noticeElement = document.getElementById("access-notice");
    const messageElement = document.getElementById("access-message");
    
    if (noticeElement && messageElement) {
      messageElement.textContent = message;
      noticeElement.style.display = "block";
      noticeElement.className = "alert alert-danger";
    }
  }

  showSuccess(message) {
    console.log(message);
    const noticeElement = document.getElementById("access-notice");
    const messageElement = document.getElementById("access-message");
    
    if (noticeElement && messageElement) {
      messageElement.textContent = message;
      noticeElement.style.display = "block";
      noticeElement.className = "alert alert-success";
      
      setTimeout(() => {
        noticeElement.style.display = "none";
      }, 3000);
    }
  }

  async applyDateFilter(startDate, endDate) {
    try {
      if (!startDate || !endDate) {
        this.showError("Please select both start and end dates");
        return;
      }
      
      this.startDate = startDate;
      this.endDate = endDate;
      
      // Reload all dashboard data with date filter
      await this.loadStats();
      await this.loadWeeklyUsage();
      
      this.showSuccess(`Date filter applied: ${startDate} to ${endDate}`);
    } catch (error) {
      console.error("Error applying date filter:", error);
      this.showError("Failed to apply date filter");
    }
  }

  async clearDateFilter() {
    try {
      this.startDate = null;
      this.endDate = null;
      
      // Reload all dashboard data without date filter
      await this.loadStats();
      await this.loadWeeklyUsage();
      
      this.showSuccess("Date filter cleared");
    } catch (error) {
      console.error("Error clearing date filter:", error);
      this.showError("Failed to clear date filter");
    }
  }

  async exportDashboardCSV() {
    try {
      const params = new URLSearchParams();
      if (this.startDate) params.append('start_date', this.startDate);
      if (this.endDate) params.append('end_date', this.endDate);
      const query = params.toString() ? `?${params.toString()}` : '';
      
      this.showSuccess("Preparing export...");
      
      const response = await fetch(`${this.baseUrl}/export${query}`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.csv) {
        // Create and download CSV file
        const blob = new Blob([data.csv], { type: 'text/csv;charset=utf-8;' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename || `sub-dashboard-${this.office}-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        this.showSuccess("Dashboard data exported successfully");
      } else {
        throw new Error(data.message || "Export failed");
      }
    } catch (error) {
      console.error("Error exporting dashboard:", error);
      this.showError("Failed to export dashboard data");
    }
  }

  destroy() {
    if (this.weeklyChart) {
      this.weeklyChart.destroy();
      this.weeklyChart = null;
    }
  }
}

// Global helper functions for chart actions
function refreshChart() {
  if (window.dashboardManager) {
    window.dashboardManager.loadWeeklyUsage();
  }
}

function exportChartData() {
  if (window.dashboardManager) {
    window.dashboardManager.exportDashboardData();
  }
}

function changeChartType(type) {
  if (window.dashboardManager) {
    window.dashboardManager.changeChartType(type);
  }
  return false; // Prevent default link behavior
}

// Make it globally accessible
if (typeof window !== 'undefined') {
  window.DashboardManager = DashboardManager;
}