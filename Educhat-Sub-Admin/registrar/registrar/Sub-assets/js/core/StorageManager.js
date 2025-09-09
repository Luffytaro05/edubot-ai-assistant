class StorageManager {
    constructor() {
        this.initializeStorage();
    }

    // Initialize storage with default data if empty
    initializeStorage() {
        console.log('StorageManager: Initializing storage...');
        
        // Initialize FAQs
        const faqs = this.getFAQs();
        console.log('StorageManager: Current FAQs:', faqs);
        
        if (!faqs.length) {
            console.log('StorageManager: No FAQs found, loading defaults...');
            const defaultFAQs = this.getDefaultFAQs();
            this.setFAQs(defaultFAQs);
            console.log('StorageManager: Default FAQs loaded:', defaultFAQs);
        }

        // Initialize Announcements
        const announcements = this.getAnnouncements();
        if (!announcements.length) {
            this.setAnnouncements(this.getDefaultAnnouncements());
        }

        // Initialize Conversations
        const conversations = this.getConversations();
        if (!conversations.length) {
            this.setConversations(this.getDefaultConversations());
        }

        // Initialize Feedback
        const feedback = this.getFeedback();
        if (!feedback.length) {
            this.setFeedback(this.getDefaultFeedback());
        }

        // Initialize Usage Stats
        const usageStats = this.getUsageStats();
        if (!usageStats.length) {
            this.setUsageStats(this.getDefaultUsageStats());
        }

        // Initialize Users
        const users = this.getUsers();
        if (!users.length) {
            this.setUsers(this.getDefaultUsers());
        }
        
        console.log('StorageManager: Storage initialization complete');
    }

    // Generic storage methods
    setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    }

    getItem(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    }

    removeItem(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    }

    // FAQs Management
    getFAQs() {
        const faqs = this.getItem('registrar_faqs') || [];
        console.log('StorageManager: getFAQs() called, returning:', faqs);
        return faqs;
    }

    setFAQs(faqs) {
        console.log('StorageManager: setFAQs() called with:', faqs);
        return this.setItem('registrar_faqs', faqs);
    }

    addFAQ(faq) {
        console.log('StorageManager: addFAQ() called with:', faq);
        const faqs = this.getFAQs();
        faq.id = this.generateId();
        faq.createdAt = new Date().toISOString();
        faq.updatedAt = new Date().toISOString();
        faqs.push(faq);
        const result = this.setFAQs(faqs);
        console.log('StorageManager: addFAQ() result:', result);
        return result;
    }

    updateFAQ(id, updatedFAQ) {
        console.log('StorageManager: updateFAQ() called with id:', id, 'and updates:', updatedFAQ);
        const faqs = this.getFAQs();
        const index = faqs.findIndex(faq => faq.id === id);
        if (index !== -1) {
            faqs[index] = { ...faqs[index], ...updatedFAQ, updatedAt: new Date().toISOString() };
            const result = this.setFAQs(faqs);
            console.log('StorageManager: updateFAQ() result:', result);
            return result;
        }
        console.log('StorageManager: updateFAQ() failed - FAQ not found with id:', id);
        return false;
    }

    deleteFAQ(id) {
        console.log('StorageManager: deleteFAQ() called with id:', id);
        const faqs = this.getFAQs();
        const filteredFAQs = faqs.filter(faq => faq.id !== id);
        const result = this.setFAQs(filteredFAQs);
        console.log('StorageManager: deleteFAQ() result:', result);
        return result;
    }

    // Announcements Management
    getAnnouncements() {
        return this.getItem('registrar_announcements') || [];
    }

    setAnnouncements(announcements) {
        return this.setItem('registrar_announcements', announcements);
    }

    addAnnouncement(announcement) {
        const announcements = this.getAnnouncements();
        announcement.id = this.generateId();
        announcement.createdAt = new Date().toISOString();
        announcement.updatedAt = new Date().toISOString();
        announcements.push(announcement);
        return this.setAnnouncements(announcements);
    }

    updateAnnouncement(id, updatedAnnouncement) {
        const announcements = this.getAnnouncements();
        const index = announcements.findIndex(announcement => announcement.id === id);
        if (index !== -1) {
            announcements[index] = { ...announcements[index], ...updatedAnnouncement, updatedAt: new Date().toISOString() };
            return this.setAnnouncements(announcements);
        }
        return false;
    }

    deleteAnnouncement(id) {
        const announcements = this.getAnnouncements();
        const filteredAnnouncements = announcements.filter(announcement => announcement.id !== id);
        return this.setAnnouncements(filteredAnnouncements);
    }

    // Conversations Management (Read-only)
    getConversations() {
        return this.getItem('registrar_conversations') || [];
    }

    setConversations(conversations) {
        return this.setItem('registrar_conversations', conversations);
    }

    // Feedback Management (Read-only)
    getFeedback() {
        return this.getItem('registrar_feedback') || [];
    }

    setFeedback(feedback) {
        return this.setItem('registrar_feedback', feedback);
    }

    // Usage Stats Management
    getUsageStats() {
        return this.getItem('registrar_usage_stats') || [];
    }

    setUsageStats(stats) {
        return this.setItem('registrar_usage_stats', stats);
    }

    addUsageStat(stat) {
        const stats = this.getUsageStats();
        stat.id = this.generateId();
        stat.date = new Date().toISOString().split('T')[0];
        stats.push(stat);
        return this.setUsageStats(stats);
    }

    // Users Management
    getUsers() {
        return this.getItem('registrar_users') || [];
    }

    setUsers(users) {
        return this.setItem('registrar_users', users);
    }

    // Authentication
    setCurrentUser(user) {
        return this.setItem('current_user', user);
    }

    getCurrentUser() {
        return this.getItem('current_user');
    }

    clearCurrentUser() {
        return this.removeItem('current_user');
    }

    // Utility methods
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Default data generators
    getDefaultFAQs() {
        return [
            {
                id: '1',
                question: 'How do I request an official transcript?',
                answer: 'Official transcripts can be requested through the student portal or by visiting the registrar office in person. You can also request them online through our secure system.',
                status: 'published',
                createdAt: '2023-06-01T10:00:00.000Z',
                updatedAt: '2023-06-01T10:00:00.000Z'
            },
            {
                id: '2',
                question: 'How do I change my major?',
                answer: 'Visit the registrar and fill out a Change of Major form. You will need approval from your current department and the new department.',
                status: 'published',
                createdAt: '2023-06-01T10:00:00.000Z',
                updatedAt: '2023-06-01T10:00:00.000Z'
            }
        ];
    }

    getDefaultAnnouncements() {
        return [
            {
                id: '1',
                title: 'System Maintenance Notice',
                content: 'The student portal will be undergoing maintenance on July 15-16, 2023. Please plan accordingly.',
                startDate: '2023-07-15',
                endDate: '2023-07-16',
                priority: 'high',
                status: 'scheduled',
                createdAt: '2023-06-01T10:00:00.000Z',
                updatedAt: '2023-06-01T10:00:00.000Z'
            },
            {
                id: '2',
                title: 'New Financial Aid Applications',
                content: 'Financial aid applications for the Fall semester are now open. Please submit your applications by August 30, 2023.',
                startDate: '2023-07-01',
                endDate: '2023-08-30',
                priority: 'medium',
                status: 'active',
                createdAt: '2023-06-01T10:00:00.000Z',
                updatedAt: '2023-06-01T10:00:00.000Z'
            },
            {
                id: '3',
                title: 'Library Hours Extended',
                content: 'Library hours have been extended during finals week. The library will be open until 2 AM.',
                startDate: '2023-07-10',
                endDate: '2023-07-20',
                priority: 'low',
                status: 'active',
                createdAt: '2023-06-01T10:00:00.000Z',
                updatedAt: '2023-06-01T10:00:00.000Z'
            }
        ];
    }

    getDefaultConversations() {
        return [
            {
                id: '1',
                user: 'Anonymous User',
                startTime: '2023-06-15T09:30:00.000Z',
                messages: 8,
                duration: '5m 23s',
                sentiment: 'positive',
                category: 'Academic Records'
            },
            {
                id: '2',
                user: 'Anonymous User',
                startTime: '2023-06-15T10:15:00.000Z',
                messages: 5,
                duration: '3m 45s',
                sentiment: 'neutral',
                category: 'Financial Aid'
            },
            {
                id: '3',
                user: 'Anonymous User',
                startTime: '2023-06-15T10:45:00.000Z',
                messages: 12,
                duration: '8m 12s',
                sentiment: 'negative',
                escalated: true,
                category: 'Course Registration'
            }
        ];
    }

    getDefaultFeedback() {
        return [
            {
                id: '1',
                user: 'User',
                rating: 5,
                comment: 'Very helpful! The chatbot quickly answered my questions about transcript requests.',
                timestamp: '2023-06-15T09:30:00.000Z',
                category: 'Academic Records',
                sentiment: 'positive'
            },
            {
                id: '2',
                user: 'User',
                rating: 2,
                comment: 'Could not get a clear answer about my financial aid status. Had to contact the office directly.',
                timestamp: '2023-06-14T14:45:00.000Z',
                category: 'Financial Aid',
                sentiment: 'negative'
            },
            {
                id: '3',
                user: 'User',
                rating: 5,
                comment: 'Good experience overall. Quick and accurate responses.',
                timestamp: '2023-06-14T11:20:00.000Z',
                category: 'General',
                sentiment: 'positive'
            }
        ];
    }

    getDefaultUsageStats() {
        const today = new Date();
        const stats = [];
        
        for (let i = 30; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            
            stats.push({
                id: `stat_${i}`,
                date: date.toISOString().split('T')[0],
                logins: Math.floor(Math.random() * 50) + 20,
                faqsViewed: Math.floor(Math.random() * 100) + 50,
                announcementsPosted: Math.floor(Math.random() * 5) + 1,
                feedbackSubmitted: Math.floor(Math.random() * 20) + 5,
                conversationsStarted: Math.floor(Math.random() * 30) + 10
            });
        }
        
        return stats;
    }

    getDefaultUsers() {
        return [
            {
                id: '1',
                email: 'admin@registrar.edu',
                password: 'admin123',
                name: 'Registrar Office',
                role: 'Sub Admin',
                office: 'Registrar'
            }
        ];
    }

    // Export to CSV
    exportToCSV(data, filename) {
        if (!data || !data.length) return false;

        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    return typeof value === 'string' && value.includes(',') 
                        ? `"${value}"` 
                        : value;
                }).join(',')
            )
        ].join('\n');

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
            return true;
        }
        
        return false;
    }
}

// Initialize global storage manager
window.storageManager = new StorageManager();
