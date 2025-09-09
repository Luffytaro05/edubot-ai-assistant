class ConversationManager {
    constructor() {
        this.storageManager = window.storageManager;
        this.uiManager = window.uiManager;
        this.conversations = [];
        this.filteredConversations = [];
    }

    initialize() {
        this.loadConversations();
        this.renderConversations();
        this.initializeEventListeners();
    }

    // Load conversations from storage
    loadConversations() {
        this.conversations = this.storageManager.getConversations();
        this.filteredConversations = [...this.conversations];
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('conversationSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.uiManager.debounce((e) => {
                this.searchConversations(e.target.value);
            }, 300));
        }
    }

    // Search conversations
    searchConversations(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredConversations = [...this.conversations];
        } else {
            this.filteredConversations = this.conversations.filter(conversation => 
                conversation.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
                conversation.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
                conversation.sentiment.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }
        this.renderConversations();
    }

    // Render conversations as cards
    renderConversations() {
        const container = document.getElementById('conversationsContainer');
        if (!container) return;

        if (this.filteredConversations.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-comments fa-3x mb-3"></i>
                    <h4>No conversations found</h4>
                    <p>No conversation logs match your search criteria.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.filteredConversations.map(conversation => `
            <div class="conversation-card mb-3">
                <div class="conversation-card-body">
                    <div class="conversation-header">
                        <div class="conversation-user">
                            <i class="fas fa-user-circle me-2"></i>
                            <span>${conversation.user}</span>
                        </div>
                        <div class="conversation-time">
                            Started: ${this.uiManager.formatDateTime(conversation.startTime)}
                        </div>
                    </div>
                    
                    <div class="conversation-details">
                        <div class="conversation-info">
                            <i class="fas fa-comments me-2"></i>
                            <span>${conversation.messages} messages</span>
                        </div>
                        <div class="conversation-info">
                            <i class="fas fa-clock me-2"></i>
                            <span>Duration: ${conversation.duration}</span>
                        </div>
                    </div>
                    
                    <div class="conversation-badges">
                        ${this.getSentimentBadge(conversation.sentiment)}
                        ${conversation.escalated ? this.getEscalatedBadge() : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Get sentiment badge
    getSentimentBadge(sentiment) {
        const badgeClass = sentiment === 'positive' ? 'badge-success' : 
                          sentiment === 'negative' ? 'badge-danger' : 'badge-warning';
        const badgeText = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
        return `<span class="badge ${badgeClass}">${badgeText}</span>`;
    }

    // Get escalated badge
    getEscalatedBadge() {
        return `<span class="badge badge-danger ms-1">Escalated</span>`;
    }

    // View conversation details
    viewConversation(id) {
        const conversation = this.conversations.find(c => c.id === id);
        if (!conversation) {
            this.uiManager.showError('Conversation not found');
            return;
        }

        // Populate view modal
        document.getElementById('viewConversationUser').textContent = conversation.user;
        document.getElementById('viewConversationStartTime').textContent = this.uiManager.formatDateTime(conversation.startTime);
        document.getElementById('viewConversationMessages').textContent = conversation.messages;
        document.getElementById('viewConversationDuration').textContent = conversation.duration;
        document.getElementById('viewConversationCategory').textContent = conversation.category;
        document.getElementById('viewConversationSentiment').innerHTML = this.uiManager.getSentimentBadge(conversation.sentiment);

        // Show/hide escalated badge
        const escalatedContainer = document.getElementById('viewConversationEscalatedContainer');
        if (conversation.escalated) {
            escalatedContainer.style.display = 'block';
        } else {
            escalatedContainer.style.display = 'none';
        }

        // Show modal
        this.uiManager.showModal('viewConversationModal');
    }

    // Get conversation by ID
    getConversationById(id) {
        return this.conversations.find(c => c.id === id);
    }

    // Get conversations by sentiment
    getConversationsBySentiment(sentiment) {
        return this.conversations.filter(c => c.sentiment === sentiment);
    }

    // Get conversations by category
    getConversationsByCategory(category) {
        return this.conversations.filter(c => c.category === category);
    }

    // Get escalated conversations
    getEscalatedConversations() {
        return this.conversations.filter(c => c.escalated);
    }

    // Get conversations by date range
    getConversationsByDateRange(startDate, endDate) {
        return this.conversations.filter(conversation => {
            const conversationDate = new Date(conversation.startTime);
            return conversationDate >= new Date(startDate) && conversationDate <= new Date(endDate);
        });
    }

    // Get recent conversations (last 7 days)
    getRecentConversations() {
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        
        return this.conversations.filter(conversation => 
            new Date(conversation.startTime) >= sevenDaysAgo
        );
    }

    // Get today's conversations
    getTodayConversations() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        return this.conversations.filter(conversation => {
            const conversationDate = new Date(conversation.startTime);
            return conversationDate >= today && conversationDate < tomorrow;
        });
    }

    // Export conversations to CSV
    exportConversations() {
        const exportData = this.conversations.map(conversation => ({
            User: conversation.user,
            'Start Time': this.uiManager.formatDateTime(conversation.startTime),
            Messages: conversation.messages,
            Duration: conversation.duration,
            Category: conversation.category,
            Sentiment: conversation.sentiment,
            Escalated: conversation.escalated ? 'Yes' : 'No'
        }));

        const success = this.uiManager.exportToCSV(exportData, 'conversations_export.csv');
        
        if (success) {
            this.uiManager.showSuccess('Conversations exported successfully!');
        } else {
            this.uiManager.showError('Failed to export conversations');
        }
    }

    // Get conversation statistics
    getConversationStats() {
        const total = this.conversations.length;
        const positive = this.getConversationsBySentiment('positive').length;
        const negative = this.getConversationsBySentiment('negative').length;
        const neutral = this.getConversationsBySentiment('neutral').length;
        const escalated = this.getEscalatedConversations().length;

        // Calculate average messages per conversation
        const totalMessages = this.conversations.reduce((sum, conv) => sum + conv.messages, 0);
        const avgMessages = total > 0 ? Math.round(totalMessages / total) : 0;

        // Calculate average duration
        const durations = this.conversations.map(conv => {
            const duration = conv.duration;
            const match = duration.match(/(\d+)m (\d+)s/);
            if (match) {
                return parseInt(match[1]) * 60 + parseInt(match[2]);
            }
            return 0;
        });
        const avgDurationSeconds = durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : 0;
        const avgDuration = `${Math.floor(avgDurationSeconds / 60)}m ${Math.round(avgDurationSeconds % 60)}s`;

        return {
            total,
            positive,
            negative,
            neutral,
            escalated,
            avgMessages,
            avgDuration,
            positivePercentage: total > 0 ? Math.round((positive / total) * 100) : 0,
            negativePercentage: total > 0 ? Math.round((negative / total) * 100) : 0,
            neutralPercentage: total > 0 ? Math.round((neutral / total) * 100) : 0,
            escalatedPercentage: total > 0 ? Math.round((escalated / total) * 100) : 0
        };
    }

    // Get conversations by time of day
    getConversationsByTimeOfDay() {
        const timeSlots = {
            '00:00-05:59': 0,
            '06:00-11:59': 0,
            '12:00-17:59': 0,
            '18:00-23:59': 0
        };

        this.conversations.forEach(conversation => {
            const hour = new Date(conversation.startTime).getHours();
            if (hour >= 0 && hour < 6) {
                timeSlots['00:00-05:59']++;
            } else if (hour >= 6 && hour < 12) {
                timeSlots['06:00-11:59']++;
            } else if (hour >= 12 && hour < 18) {
                timeSlots['12:00-17:59']++;
            } else {
                timeSlots['18:00-23:59']++;
            }
        });

        return timeSlots;
    }

    // Get top conversation categories
    getTopCategories() {
        const categories = {};
        this.conversations.forEach(conversation => {
            categories[conversation.category] = (categories[conversation.category] || 0) + 1;
        });

        return Object.entries(categories)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([category, count]) => ({ category, count }));
    }

    // Get conversation trends (daily for last 7 days)
    getConversationTrends() {
        const trends = [];
        const today = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateString = date.toISOString().split('T')[0];
            
            const dayConversations = this.conversations.filter(conversation => 
                conversation.startTime.startsWith(dateString)
            );
            
            trends.push({
                date: this.uiManager.formatDate(dateString),
                count: dayConversations.length,
                positive: dayConversations.filter(c => c.sentiment === 'positive').length,
                negative: dayConversations.filter(c => c.sentiment === 'negative').length,
                neutral: dayConversations.filter(c => c.sentiment === 'neutral').length
            });
        }
        
        return trends;
    }

    // Filter conversations by multiple criteria
    filterConversations(filters = {}) {
        let filtered = [...this.conversations];

        if (filters.sentiment) {
            filtered = filtered.filter(c => c.sentiment === filters.sentiment);
        }

        if (filters.category) {
            filtered = filtered.filter(c => c.category === filters.category);
        }

        if (filters.escalated !== undefined) {
            filtered = filtered.filter(c => c.escalated === filters.escalated);
        }

        if (filters.dateRange) {
            filtered = filtered.filter(conversation => {
                const conversationDate = new Date(conversation.startTime);
                return conversationDate >= new Date(filters.dateRange.start) && 
                       conversationDate <= new Date(filters.dateRange.end);
            });
        }

        if (filters.minMessages) {
            filtered = filtered.filter(c => c.messages >= filters.minMessages);
        }

        if (filters.maxMessages) {
            filtered = filtered.filter(c => c.messages <= filters.maxMessages);
        }

        return filtered;
    }

    // Get conversation insights
    getConversationInsights() {
        const stats = this.getConversationStats();
        const trends = this.getConversationTrends();
        const categories = this.getTopCategories();
        const timeSlots = this.getConversationsByTimeOfDay();

        return {
            stats,
            trends,
            categories,
            timeSlots,
            insights: {
                peakHour: Object.entries(timeSlots).reduce((a, b) => timeSlots[a] > timeSlots[b] ? a : b)[0],
                mostCommonCategory: categories[0]?.category || 'N/A',
                satisfactionRate: stats.total > 0 ? Math.round((stats.positive / stats.total) * 100) : 0,
                escalationRate: stats.total > 0 ? Math.round((stats.escalated / stats.total) * 100) : 0
            }
        };
    }
}

// Initialize global conversation manager
window.ConversationManager = ConversationManager;
