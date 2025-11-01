/**
 * ConversationManager.js
 * Handles fetching, rendering, and managing conversation logs per Sub Admin office
 */

class ConversationManager {
    constructor() {
        this.baseUrl = "/subadmin/conversations"; // Flask route
        this.tableBody = document.getElementById("conversations-table-body");
        this.searchInput = document.getElementById("conversationSearch");
        this.loader = document.getElementById("conversationLoader"); // optional spinner element
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalItems = 0;
        this.searchTimeout = null; // for debounce
        this.subAdminName = null; // Store sub admin name
    }

    async initialize() {
        // Get sub admin info first
        const user = await window.authManager.getCurrentUser();
        if (user && user.name) {
            this.subAdminName = user.name;
        }

        await this.loadConversations();

        // Debounced search for performance
        if (this.searchInput) {
            this.searchInput.addEventListener("input", () => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.currentPage = 1;
                    this.loadConversations(this.searchInput.value);
                }, 400);
            });
        }
    }

    async loadConversations(search = "") {
        try {
            const user = await window.authManager.getCurrentUser();
            if (!user || !user.office) {
                console.error("No Sub Admin office detected.");
                return;
            }

            if (this.loader) this.loader.style.display = "block";

            const response = await fetch(
                `${this.baseUrl}?office=${encodeURIComponent(user.office)}&page=${this.currentPage}&limit=${this.pageSize}&search=${encodeURIComponent(search)}`,
                { credentials: "include" }
            );

            if (!response.ok) throw new Error("Failed to load conversations");

            const data = await response.json();
            
            // Transform MongoDB data to match our structure
            const transformedConversations = (data.conversations || []).map(conv => {
                return {
                    _id: conv._id,
                    id: conv._id,
                    user: conv.user || "Guest",
                    sender: conv.sender || "unknown",
                    message: conv.message || "",
                    office: conv.office || "General",
                    status: conv.status || "active",
                    // Check multiple possible date fields from MongoDB
                    date: conv.date || conv.timestamp || conv.created_at || conv.createdAt || conv.createdDate,
                    email: conv.email || null
                };
            });

            this.renderConversations(transformedConversations);
            this.updatePagination(data.total || transformedConversations.length);

        } catch (error) {
            console.error("Error loading conversations:", error);
            this.tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-5">
                <i class="fas fa-exclamation-circle fa-2x mb-3 d-block"></i>
                <div>Failed to load conversations</div>
                <small class="text-muted mt-2">${error.message}</small>
            </td></tr>`;
        } finally {
            if (this.loader) this.loader.style.display = "none";
        }
    }

    renderConversations(conversations) {
        this.tableBody.innerHTML = "";
        if (!conversations || conversations.length === 0) {
            this.tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-5">
                <i class="fas fa-comments-slash fa-3x mb-3 d-block"></i>
                <div class="fs-5">No conversations found</div>
                <small class="text-muted">Conversations will appear here once users interact with the chatbot</small>
            </td></tr>`;
            return;
        }

        conversations.forEach(conversation => {
            const row = document.createElement("tr");
            row.className = "conversation-row";

            // --- Sender handling ---
            const sender = conversation.sender || "unknown";
            const message = conversation.message || "";

            // Map sender → label
            let senderDisplay = "Unknown";
            let senderClass = "unknown";
            let senderIcon = "fa-question";

            if (sender.toLowerCase() === "user") {
                senderDisplay = "User";
                senderClass = "user";
                senderIcon = "fa-user";
            } else if (sender.toLowerCase() === "bot") {
                senderDisplay = "Bot Response";
                senderClass = "bot";
                senderIcon = "fa-robot";
            }

            // --- User column ---
            let userDisplay = conversation.user || "Guest";
            let userAvatarLetter = userDisplay.charAt(0).toUpperCase();
            let userRoleDisplay = "";

            if (sender.toLowerCase() === "bot") {
                // Display "Guest" for bot responses
                userDisplay = "Guest";
                userAvatarLetter = "G";
                userRoleDisplay = `<div class="user-role text-muted small"><i class="fas fa-robot me-1"></i>Bot Response</div>`;
            } else {
                // For user messages, show email if available
                if (conversation.email) {
                    userRoleDisplay = `<div class="user-email text-muted small"><i class="far fa-envelope me-1"></i>${conversation.email}</div>`;
                }
            }

            // Message truncation
            const truncatedMessage = message.length > 150 ? message.substring(0, 150) + "..." : message;
            const fullMessage = message.replace(/'/g, "&apos;").replace(/"/g, "&quot;");

            row.innerHTML = `
                <!-- User Column -->
                <td class="user-column">
                    <div class="d-flex align-items-center">
                        <div class="user-avatar-circle ${senderClass}-avatar" style="width:40px;height:40px;min-width:40px;">
                            ${userAvatarLetter}
                        </div>
                        <div class="ms-3">
                            <div class="user-name-display fw-semibold">${userDisplay}</div>
                            ${userRoleDisplay}
                        </div>
                    </div>
                </td>

                <!-- Message Column -->
                <td class="message-column">
                    <div class="message-wrapper ${senderClass}-message-wrapper">
                        <div class="message-content" data-full-message="${fullMessage}">
                            ${truncatedMessage}
                        </div>
                        ${message.length > 150 ? `
                            <button class="btn btn-link btn-sm p-0 mt-1 toggle-message-btn" onclick="conversationManager.toggleMessage(this)">
                                <i class="fas fa-chevron-down me-1"></i>Show more
                            </button>
                        ` : ''}
                    </div>
                </td>

                <!-- Sender Column -->
                <td class="sender-column text-center">
                    <span class="badge sender-badge-${senderClass}">
                        <i class="fas ${senderIcon} me-1"></i>
                        ${senderDisplay}
                    </span>
                </td>

                <!-- Date Column -->
                <td class="date-column">
                    <div class="date-info">
                        <div class="date">
                            <i class="far fa-calendar me-1"></i>
                            ${this.formatDate(conversation.date || conversation.timestamp || conversation.created_at)}
                        </div>
                        <div class="time text-muted small">
                            <i class="far fa-clock me-1"></i>
                            ${this.formatTime(conversation.date || conversation.timestamp || conversation.created_at)}
                        </div>
                    </div>
                </td>

                <!-- Actions Column -->
                <td class="actions-column">
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="conversationManager.viewConversation('${conversation._id || conversation.id}')" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="conversationManager.escalateConversation('${conversation._id || conversation.id}')" title="Escalate">
                            <i class="fas fa-flag"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="conversationManager.deleteConversation('${conversation._id || conversation.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;

            this.tableBody.appendChild(row);
        });
    }

    toggleMessage(button) {
        const messageContent = button.parentElement.querySelector('.message-content');
        const fullMessage = messageContent.getAttribute('data-full-message');
        const isExpanded = button.classList.contains('expanded');

        if (isExpanded) {
            messageContent.textContent = fullMessage.substring(0, 150) + "...";
            button.innerHTML = '<i class="fas fa-chevron-down me-1"></i>Show more';
            button.classList.remove('expanded');
        } else {
            messageContent.textContent = fullMessage;
            button.innerHTML = '<i class="fas fa-chevron-up me-1"></i>Show less';
            button.classList.add('expanded');
        }
    }

    async viewConversation(conversationId) {
        try {
            const response = await fetch(`${this.baseUrl}/${conversationId}`, { credentials: "include" });
            if (!response.ok) throw new Error("Failed to fetch conversation details");
            const conv = await response.json();

            // Fill modal fields with actual stored data
            document.getElementById("viewConversationUser").textContent = conv.user || "Anonymous";
            
            // Use available date field
            const dateField = conv.date || conv.timestamp || conv.start_time;
            document.getElementById("viewConversationStartTime").textContent = dateField ? this.formatDateTime(dateField) : "N/A";
            
            // Show 1 message for individual conversation items
            document.getElementById("viewConversationMessages").textContent = conv.messages && Array.isArray(conv.messages) ? conv.messages.length : "1";
            document.getElementById("viewConversationDuration").textContent = conv.duration || "N/A";
            
            // Use office as category since it's more accurate
            document.getElementById("viewConversationCategory").textContent = conv.office || conv.category || "General";
            document.getElementById("viewConversationSentiment").textContent = conv.sentiment || "Neutral";

            const msgList = document.getElementById("viewConversationMessageList");
            if (msgList) {
                msgList.innerHTML = "";
                
                // If conv.messages exists and is an array, use it
                if (conv.messages && Array.isArray(conv.messages) && conv.messages.length > 0) {
                    conv.messages.forEach(m => {
                        const li = document.createElement("li");
                        li.className = `list-group-item ${m.sender === "bot" ? "list-group-item-light" : ""}`;
                        const messageText = m.text || m.message || "";
                        li.innerHTML = `<strong>${m.sender === "bot" ? "Bot Response" : "User"}:</strong> ${messageText}`;
                        msgList.appendChild(li);
                    });
                } else {
                    // Otherwise show the single message from the conversation
                    const li = document.createElement("li");
                    li.className = `list-group-item ${conv.sender === "bot" ? "list-group-item-light" : ""}`;
                    const messageText = conv.message || "";
                    const senderLabel = conv.sender === "bot" ? "Bot Response" : conv.sender === "user" ? "User" : "Unknown";
                    li.innerHTML = `<strong>${senderLabel}:</strong> ${messageText}`;
                    msgList.appendChild(li);
                }
            }

            // Show escalated badge based on status or escalated field
            const isEscalated = conv.status === "escalated" || conv.escalated === true;
            document.getElementById("viewConversationEscalatedContainer").style.display = isEscalated ? "block" : "none";

            const modal = new bootstrap.Modal(document.getElementById("viewConversationModal"));
            modal.show();
        } catch (error) {
            console.error("Error viewing conversation:", error);
            alert("Unable to load conversation details.");
        }
    }

    async escalateConversation(conversationId) {
        if (confirm("Escalate this conversation to a higher authority?")) {
            try {
                // Add your escalation API call here
                console.log("Escalated:", conversationId);
                this.showToast("Success", "Conversation escalated successfully", "success");
            } catch (error) {
                console.error("Error escalating conversation:", error);
                this.showToast("Error", "Failed to escalate conversation", "danger");
            }
        }
    }

    async deleteConversation(conversationId) {
        if (confirm("Are you sure you want to delete this conversation? This action cannot be undone.")) {
            try {
                // Add your delete API call here
                console.log("Deleted:", conversationId);
                await this.loadConversations(this.searchInput?.value || "");
                this.showToast("Success", "Conversation deleted successfully", "success");
            } catch (error) {
                console.error("Error deleting conversation:", error);
                this.showToast("Error", "Failed to delete conversation", "danger");
            }
        }
    }

    showToast(title, message, type = "info") {
        const toastEl = document.getElementById("toast");
        const toastTitle = document.getElementById("toastTitle");
        const toastMessage = document.getElementById("toastMessage");
        
        if (toastEl && toastTitle && toastMessage) {
            toastTitle.textContent = title;
            toastMessage.textContent = message;
            toastEl.className = `toast bg-${type} text-white`;
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        }
    }

    updatePagination(total) {
        this.totalItems = total;
        const startItem = (this.currentPage - 1) * this.pageSize + 1;
        const endItem = Math.min(this.currentPage * this.pageSize, total);

        document.getElementById("start-item").textContent = total > 0 ? startItem : 0;
        document.getElementById("end-item").textContent = total > 0 ? endItem : 0;
        document.getElementById("total-items").textContent = total;

        document.getElementById("prev-btn").disabled = this.currentPage <= 1;
        document.getElementById("next-btn").disabled = this.currentPage * this.pageSize >= total;
    }

    async nextPage() {
        if (this.currentPage * this.pageSize < this.totalItems) {
            this.currentPage++;
            await this.loadConversations(this.searchInput?.value || "");
        }
    }

    async previousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            await this.loadConversations(this.searchInput?.value || "");
        }
    }

    // Helper functions for date/time formatting
    formatDate(dateString) {
        if (!dateString) {
            console.log('formatDate: No date provided');
            return 'N/A';
        }
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                console.log('formatDate: Invalid date:', dateString);
                return 'Invalid Date';
            }
            return date.toLocaleDateString();
        } catch (e) {
            console.error('formatDate error:', e, dateString);
            return 'Error';
        }
    }

    formatTime(dateString) {
        if (!dateString) {
            return '';
        }
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return '';
            }
            return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } catch (e) {
            console.error('formatTime error:', e);
            return '';
        }
    }

    // Combined format for modal/detail views
    formatDateTime(timestamp) {
        if (!timestamp) return 'N/A';
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                return 'Invalid Date';
            }
            return date.toLocaleString();
        } catch (e) {
            console.error('formatDateTime error:', e);
            return 'Error';
        }
    }
}

window.ConversationManager = ConversationManager;