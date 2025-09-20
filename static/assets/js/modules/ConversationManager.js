/**
 * ConversationManager - Updated to work with Flask API backend and sender field
 * Maintains backward compatibility while integrating with API
 * (ConversationManager.js):
 */
class ConversationManager extends BaseManager {
    constructor() {
        super('conversations');
        this.API_BASE = "http://localhost:5000/api"; // Flask backend URL
        this.useAPI = true; // Set to false to use localStorage fallback
        this.initializeDefaultConversations();
    }

    /**
     * Load conversations from API or localStorage
     * @returns {Array} Array of conversations
     */
    async loadConversations() {
        if (this.useAPI) {
            try {
                const response = await fetch(`${this.API_BASE}/conversations`);
                if (!response.ok) throw new Error("Failed to fetch conversations");
                const apiConversations = await response.json();
                
                // Transform API data to match internal structure with sender support
                return apiConversations.map(conv => ({
                    id: conv._id || conv.id,
                    user: conv.user || conv.userName || "Guest",
                    email: conv.userEmail || `${(conv.user || "user").toLowerCase().replace(/\s+/g, '.')}@university.edu`,
                    userType: conv.userType || "student",
                    message: conv.message || "",
                    sender: conv.sender || "unknown", // NEW: Include sender field
                    date: conv.date || new Date().toISOString(),
                    office: conv.office || conv.department || "General",
                    createdAt: conv.createdAt || new Date().toISOString(),
                    updatedAt: conv.updatedAt
                }));
            } catch (error) {
                console.error("Error loading conversations from API:", error);
                console.log("Falling back to localStorage...");
                this.useAPI = false;
                return this.getAll(); // Fallback to localStorage
            }
        } else {
            return this.getAll(); // Use localStorage
        }
    }

    /**
     * Render conversations in the table with sender column
     * @param {Array} conversations - Optional array of conversations to render
     */
    async renderConversationsTable(conversations = null) {
        try {
            const conversationsData = conversations || await this.loadConversations();
            const tableBody = document.getElementById("conversations-table-body");
            
            if (!tableBody) {
                console.error("Table body element not found");
                return;
            }

            tableBody.innerHTML = ""; // Clear existing rows

            if (conversationsData.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center">No conversations found</td>
                    </tr>
                `;
                return;
            }

            conversationsData.forEach(conv => {
                const row = document.createElement("tr");
                const formattedDate = new Date(conv.date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });

                // Format sender display
                const sender = conv.sender || 'unknown';
                const senderDisplay = sender.toLowerCase() === 'user' ? 'User' : 
                                   sender.toLowerCase() === 'bot' ? 'Bot' : 'Unknown';
                const senderIcon = sender.toLowerCase() === 'user' ? 'fa-user' : 
                                 sender.toLowerCase() === 'bot' ? 'fa-robot' : 'fa-question';

                row.innerHTML = `
                    <td title="${conv.email || ''}">${conv.user}</td>
                    <td title="${conv.message}" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${conv.message}
                    </td>
                    <td>
                        <span class="sender-badge sender-${sender.toLowerCase()}">
                            <i class="fas ${senderIcon}"></i>
                            ${senderDisplay}
                        </span>
                    </td>
                    <td>${conv.office}</td>
                    <td>${formattedDate}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-primary me-1" onclick="conversationManager.viewConversation('${conv.id}')" title="View Details">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-warning me-1" onclick="conversationManager.editConversation('${conv.id}')" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="conversationManager.deleteConversation('${conv.id}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        } catch (error) {
            console.error("Error rendering conversations table:", error);
            const tableBody = document.getElementById("conversations-table-body");
            if (tableBody) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-danger">
                            Error loading conversations. Please try again.
                        </td>
                    </tr>
                `;
            }
        }
    }

    /**
     * Delete a conversation by ID (API or localStorage)
     * @param {string} id - Conversation ID
     */
    async deleteConversation(id) {
        if (!confirm("Are you sure you want to delete this conversation?")) return;
        
        try {
            if (this.useAPI) {
                const response = await fetch(`${this.API_BASE}/conversations/${id}`, {
                    method: "DELETE",
                });
                
                if (response.ok) {
                    console.log("Conversation deleted successfully!");
                    await this.renderConversationsTable(); // Reload the table
                } else {
                    throw new Error("Failed to delete conversation from API");
                }
            } else {
                // Use localStorage method
                const result = super.deleteConversation ? super.deleteConversation(id) : this.deleteConversationLocal(id);
                if (result.success) {
                    console.log("Conversation deleted successfully!");
                    await this.renderConversationsTable(); // Reload the table
                } else {
                    console.error(result.message || "Failed to delete conversation");
                }
            }
        } catch (error) {
            console.error("Error deleting conversation:", error);
        }
    }

    /**
     * Add a new conversation (API or localStorage)
     * @param {Object} conversationData - Conversation data
     */
    async addConversation(conversationData) {
        try {
            if (this.useAPI) {
                const response = await fetch(`${this.API_BASE}/conversations`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        user: conversationData.user,
                        userEmail: conversationData.email,
                        userType: conversationData.userType,
                        message: conversationData.message,
                        sender: conversationData.sender, // NEW: Include sender
                        office: conversationData.office,
                        date: conversationData.date || new Date().toISOString()
                    })
                });

                if (response.ok) {
                    return { success: true, message: 'Conversation added successfully' };
                } else {
                    throw new Error("Failed to add conversation to API");
                }
            } else {
                // Use localStorage method from parent class
                return super.addConversation(conversationData);
            }
        } catch (error) {
            console.error('Error adding conversation:', error);
            return { success: false, message: 'Failed to add conversation' };
        }
    }

    /**
     * Update a conversation (API or localStorage)
     * @param {string} id - Conversation ID
     * @param {Object} updates - Updates to apply
     */
    async updateConversation(id, updates) {
        try {
            if (this.useAPI) {
                const response = await fetch(`${this.API_BASE}/conversations/${id}`, {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        user: updates.user,
                        userEmail: updates.email,
                        userType: updates.userType,
                        message: updates.message,
                        sender: updates.sender, // NEW: Include sender in updates
                        office: updates.office,
                        date: updates.date
                    })
                });

                if (response.ok) {
                    return { success: true, message: 'Conversation updated successfully' };
                } else {
                    throw new Error("Failed to update conversation in API");
                }
            } else {
                // Use localStorage method from parent class
                return super.updateConversation(id, updates);
            }
        } catch (error) {
            console.error('Error updating conversation:', error);
            return { success: false, message: 'Failed to update conversation' };
        }
    }

    /**
     * Get filtered conversations with sender support
     * @param {Object} filters - Filter criteria
     */
    async getFilteredConversations(filters) {
        try {
            const conversations = await this.loadConversations();
            
            // Apply filters
            let filtered = [...conversations];

            // Apply date range filter
            if (filters.dateRange) {
                const now = new Date();
                let startDate;

                switch (filters.dateRange) {
                    case 'today':
                        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                        break;
                    case 'week':
                        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        break;
                    case 'month':
                        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
                        break;
                    case 'quarter':
                        startDate = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
                        break;
                    case 'year':
                        startDate = new Date(now.getFullYear(), 0, 1);
                        break;
                }

                if (startDate) {
                    filtered = filtered.filter(conv => 
                        new Date(conv.date) >= startDate
                    );
                }
            }

            // Apply office filter
            if (filters.office) {
                const officeMap = {
                    'admissions': 'Admissions Office',
                    'registrar': 'Registrar Office',
                    'library': 'Library',
                    'financial-aid': 'Financial Aid Office',
                    'faculty-affairs': 'Faculty Affairs',
                    'guidance': 'Guidance Office',
                    'transportation': 'Transportation Services',
                    'hr': 'Human Resources',
                    'dining': 'Dining Services',
                    'it': 'IT Services'
                };

                const officeName = officeMap[filters.office] || filters.office;
                filtered = filtered.filter(conv => 
                    conv.office.toLowerCase() === officeName.toLowerCase()
                );
            }

            // NEW: Apply sender filter
            if (filters.sender) {
                filtered = filtered.filter(conv => 
                    conv.sender.toLowerCase() === filters.sender.toLowerCase()
                );
            }

            // Apply user type filter
            if (filters.userType) {
                filtered = filtered.filter(conv => 
                    conv.userType.toLowerCase() === filters.userType.toLowerCase()
                );
            }

            return filtered;
        } catch (error) {
            console.error('Error filtering conversations:', error);
            return [];
        }
    }

    /**
     * Search conversations including sender field
     * @param {string} query - Search query
     */
    async searchConversations(query) {
        try {
            const conversations = await this.loadConversations();
            const lowerQuery = query.toLowerCase();

            return conversations.filter(conversation => {
                // Search in user info
                if (conversation.user.toLowerCase().includes(lowerQuery) ||
                    (conversation.email && conversation.email.toLowerCase().includes(lowerQuery))) {
                    return true;
                }

                // Search in message content
                if (conversation.message.toLowerCase().includes(lowerQuery)) {
                    return true;
                }

                // Search in office
                if (conversation.office.toLowerCase().includes(lowerQuery)) {
                    return true;
                }

                // NEW: Search in sender
                if (conversation.sender.toLowerCase().includes(lowerQuery)) {
                    return true;
                }

                return false;
            });
        } catch (error) {
            console.error('Error searching conversations:', error);
            return [];
        }
    }

    /**
     * Get statistics including sender breakdown
     * @returns {Object} Statistics object
     */
    async getStats() {
        const conversations = await this.loadConversations();
        const stats = {
            total: conversations.length,
            byUserType: {
                student: 0,
                faculty: 0,
                staff: 0
            },
            byOffice: {},
            bySender: { // NEW: Sender statistics
                user: 0,
                bot: 0,
                unknown: 0
            }
        };

        conversations.forEach(conversation => {
            const userType = conversation.userType.toLowerCase();
            if (stats.byUserType[userType] !== undefined) {
                stats.byUserType[userType]++;
            }

            const office = conversation.office;
            stats.byOffice[office] = (stats.byOffice[office] || 0) + 1;

            // NEW: Count by sender
            const sender = conversation.sender.toLowerCase();
            if (stats.bySender[sender] !== undefined) {
                stats.bySender[sender]++;
            } else {
                stats.bySender.unknown++;
            }
        });

        return stats;
    }

    /**
     * Get conversations by sender
     * @param {string} sender - The sender to filter by ('user' or 'bot')
     * @returns {Array} Array of conversations for the specified sender
     */
    async getBySender(sender) {
        const conversations = await this.loadConversations();
        return conversations.filter(conv => 
            conv.sender.toLowerCase() === sender.toLowerCase()
        );
    }

    /**
     * Export conversations to CSV with sender column
     * @param {Array} conversations - Conversations to export (optional, defaults to all)
     * @returns {string} CSV content
     */
    async exportToCSV(conversations = null) {
        try {
            const data = conversations || await this.loadConversations();
            
            if (data.length === 0) {
                return null;
            }

            // Define CSV headers with sender column
            const headers = [
                'ID',
                'User Name',
                'User Email',
                'User Type',
                'Message',
                'Sender', // NEW: Sender column
                'Office',
                'Date'
            ];

            // Create CSV content
            let csvContent = headers.join(',') + '\n';

            data.forEach(conversation => {
                const row = [
                    conversation.id,
                    `"${conversation.user}"`,
                    conversation.email || '',
                    conversation.userType,
                    `"${conversation.message.replace(/"/g, '""')}"`,
                    conversation.sender, // NEW: Include sender in CSV
                    `"${conversation.office}"`,
                    new Date(conversation.date).toISOString()
                ];
                csvContent += row.join(',') + '\n';
            });

            return csvContent;
        } catch (error) {
            console.error('Error exporting conversations to CSV:', error);
            return null;
        }
    }

    /**
     * Get conversation by ID
     * @param {string} id - Conversation ID
     * @returns {Object|null} Conversation object or null if not found
     */
    async getById(id) {
        const conversations = await this.loadConversations();
        return conversations.find(conv => conv.id === id) || null;
    }

    // Helper methods
    viewConversation(id) {
        // This will be handled by the global viewConversation function
        console.log('View conversation:', id);
    }

    editConversation(id) {
        // Implement edit conversation modal/page
        console.log('Edit conversation:', id);
    }

    escalateConversation(id) {
        // Placeholder for escalation logic
        console.log('Escalate conversation:', id);
        return { success: true, message: 'Conversation escalated successfully' };
    }

    // Initialize default conversations (only for localStorage fallback)
    initializeDefaultConversations() {
        if (!this.useAPI && this.getAll().length === 0) {
            const defaultConversations = [
                {
                    id: 'conv-1',
                    user: 'John Doe',
                    email: 'john.doe@university.edu',
                    userType: 'student',
                    message: 'What are the admission requirements for the Computer Science program?',
                    sender: 'user',
                    date: new Date('2024-01-15T10:30:00').toISOString(),
                    office: 'Admissions Office'
                },
                {
                    id: 'conv-2',
                    user: 'John Doe',
                    email: 'john.doe@university.edu',
                    userType: 'student',
                    message: 'To be admitted to the Computer Science program, you need a high school diploma with at least 85% in Mathematics and English, SAT scores of 1200+, and a completed application form.',
                    sender: 'bot',
                    date: new Date('2024-01-15T10:31:00').toISOString(),
                    office: 'Admissions Office'
                },
                {
                    id: 'conv-3',
                    user: 'Sarah Johnson',
                    email: 'sarah.johnson@university.edu',
                    userType: 'student',
                    message: 'I need help with my course registration. The system keeps showing an error.',
                    sender: 'user',
                    date: new Date('2024-01-15T14:20:00').toISOString(),
                    office: 'Registrar Office'
                },
                {
                    id: 'conv-4',
                    user: 'Sarah Johnson',
                    email: 'sarah.johnson@university.edu',
                    userType: 'student',
                    message: 'I understand you\'re having trouble with course registration. Please check your student portal for any holds, and contact the Registrar\'s Office if the problem persists.',
                    sender: 'bot',
                    date: new Date('2024-01-15T14:21:00').toISOString(),
                    office: 'Registrar Office'
                }
            ];

            defaultConversations.forEach(conversation => {
                super.addConversation(conversation);
            });
        }
    }
}

// Global function for easy access (maintains compatibility with existing onclick handlers)
let conversationManager;

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", async () => {
    conversationManager = new ConversationManager();
    await conversationManager.renderConversationsTable();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConversationManager;
}