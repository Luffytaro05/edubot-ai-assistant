/**
 * FAQManager - Manages FAQ operations for Sub-Admin
 * Handles adding, editing, deleting, and viewing FAQs
 */

class FAQManager {
    constructor() {
        this.faqs = [];
        this.currentFaqId = null;
        this.apiBaseUrl = '/api/sub-faq';
    }

    /**
     * Initialize the FAQ manager
     */
    async initialize() {
        console.log('Initializing FAQ Manager...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load FAQs
        await this.loadFAQs();
        
        console.log('FAQ Manager initialized successfully');
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('faqSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterFAQs(e.target.value);
            });
        }

        // Form submission
        const faqForm = document.getElementById('faqForm');
        if (faqForm) {
            faqForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveFAQ();
            });
        }
    }

    /**
     * Load all FAQs from the server
     */
    async loadFAQs() {
        try {
            console.log('Loading FAQs...');
            
            const response = await fetch(`${this.apiBaseUrl}/list`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.faqs = data.faqs || [];
                console.log(`Loaded ${this.faqs.length} FAQs`);
                this.renderFAQs();
            } else {
                console.error('Failed to load FAQs:', data.message);
                this.showToast('Error', data.message || 'Failed to load FAQs', 'error');
            }
        } catch (error) {
            console.error('Error loading FAQs:', error);
            this.showToast('Error', 'Failed to load FAQs', 'error');
        }
    }

    /**
     * Render FAQs in the table
     */
    renderFAQs(faqs = null) {
        const tbody = document.getElementById('faqTableBody');
        if (!tbody) {
            console.error('FAQ table body not found');
            return;
        }

        const faqsToRender = faqs || this.faqs;

        if (faqsToRender.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4 text-muted">
                        <i class="fas fa-inbox fa-2x mb-2"></i>
                        <p>No FAQs found. Click "Add New FAQ" to create one.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = faqsToRender.map(faq => `
            <tr>
                <td style="max-width: 300px;">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" 
                         title="${this.escapeHtml(faq.question)}">
                        ${this.escapeHtml(faq.question)}
                    </div>
                </td>
                <td style="max-width: 400px;">
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" 
                         title="${this.escapeHtml(faq.answer)}">
                        ${this.escapeHtml(faq.answer)}
                    </div>
                </td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(faq.status)}">
                        ${this.capitalizeFirst(faq.status || 'published')}
                    </span>
                </td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" 
                                class="btn btn-sm btn-secondary" 
                                onclick="viewFAQHistory('${faq._id}')"
                                title="View History">
                            <i class="fas fa-history"></i>
                        </button>
                        <button type="button" 
                                class="btn btn-sm btn-info" 
                                onclick="viewFAQ('${faq._id}')"
                                title="View FAQ">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button type="button" 
                                class="btn btn-sm btn-warning" 
                                onclick="editFAQ('${faq._id}')"
                                title="Edit FAQ">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" 
                                class="btn btn-sm btn-danger" 
                                onclick="deleteFAQ('${faq._id}')"
                                title="Delete FAQ">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Filter FAQs based on search query
     */
    filterFAQs(query) {
        if (!query || query.trim() === '') {
            this.renderFAQs();
            return;
        }

        const lowerQuery = query.toLowerCase();
        const filtered = this.faqs.filter(faq => 
            faq.question.toLowerCase().includes(lowerQuery) ||
            faq.answer.toLowerCase().includes(lowerQuery)
        );

        this.renderFAQs(filtered);
    }

    /**
     * Save FAQ (add or update)
     */
    async saveFAQ() {
        try {
            const faqId = document.getElementById('faqId').value;
            const question = document.getElementById('faqQuestion').value.trim();
            const answer = document.getElementById('faqAnswer').value.trim();
            const status = document.getElementById('faqStatus').value;

            // Validation
            if (!question) {
                this.showToast('Validation Error', 'Question is required', 'warning');
                return;
            }

            if (!answer) {
                this.showToast('Validation Error', 'Answer is required', 'warning');
                return;
            }

            const faqData = {
                question: question,
                answer: answer,
                status: status
            };

            let response;
            let successMessage;

            if (faqId) {
                // Update existing FAQ
                response = await fetch(`${this.apiBaseUrl}/${faqId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(faqData)
                });
                successMessage = 'FAQ updated successfully';
            } else {
                // Add new FAQ
                response = await fetch(`${this.apiBaseUrl}/add`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify(faqData)
                });
                successMessage = 'FAQ added successfully and synced to chatbot';
            }

            const data = await response.json();

            if (data.success) {
                this.showToast('Success', data.message || successMessage, 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('faqModal'));
                if (modal) {
                    modal.hide();
                }

                // Reload FAQs
                await this.loadFAQs();
            } else {
                this.showToast('Error', data.message || 'Failed to save FAQ', 'error');
            }
        } catch (error) {
            console.error('Error saving FAQ:', error);
            this.showToast('Error', 'Failed to save FAQ', 'error');
        }
    }

    /**
     * View FAQ details
     */
    async viewFAQ(faqId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${faqId}`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success && data.faq) {
                const faq = data.faq;
                
                // Populate view modal
                document.getElementById('viewFAQQuestion').textContent = faq.question;
                document.getElementById('viewFAQAnswer').textContent = faq.answer;
                
                const statusBadge = document.getElementById('viewFAQStatus');
                statusBadge.className = `badge ${this.getStatusBadgeClass(faq.status)}`;
                statusBadge.textContent = this.capitalizeFirst(faq.status || 'published');
                
                document.getElementById('viewFAQCreated').textContent = 
                    this.formatDate(faq.created_at);
                document.getElementById('viewFAQUpdated').textContent = 
                    this.formatDate(faq.updated_at);

                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('viewFAQModal'));
                modal.show();
            } else {
                this.showToast('Error', data.message || 'FAQ not found', 'error');
            }
        } catch (error) {
            console.error('Error viewing FAQ:', error);
            this.showToast('Error', 'Failed to load FAQ details', 'error');
        }
    }

    /**
     * Edit FAQ
     */
    async editFAQ(faqId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${faqId}`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success && data.faq) {
                const faq = data.faq;
                
                // Populate form
                document.getElementById('faqId').value = faq._id;
                document.getElementById('faqQuestion').value = faq.question;
                document.getElementById('faqAnswer').value = faq.answer;
                document.getElementById('faqStatus').value = faq.status || 'published';

                // Update modal title and button
                document.getElementById('faqModalLabel').textContent = 'Edit FAQ';
                document.querySelector('#faqModal .btn-primary').textContent = 'Update';

                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('faqModal'));
                modal.show();
            } else {
                this.showToast('Error', data.message || 'FAQ not found', 'error');
            }
        } catch (error) {
            console.error('Error loading FAQ for editing:', error);
            this.showToast('Error', 'Failed to load FAQ', 'error');
        }
    }

    /**
     * Delete FAQ
     */
    async deleteFAQ(faqId) {
        if (!confirm('Are you sure you want to delete this FAQ? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/${faqId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Success', data.message || 'FAQ deleted successfully', 'success');
                
                // Reload FAQs
                await this.loadFAQs();
            } else {
                this.showToast('Error', data.message || 'Failed to delete FAQ', 'error');
            }
        } catch (error) {
            console.error('Error deleting FAQ:', error);
            this.showToast('Error', 'Failed to delete FAQ', 'error');
        }
    }

    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');

        if (!toast || !toastTitle || !toastMessage) {
            alert(`${title}: ${message}`);
            return;
        }

        toastTitle.textContent = title;
        toastMessage.textContent = message;

        // Set color based on type
        toast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
        switch (type) {
            case 'success':
                toast.classList.add('bg-success', 'text-white');
                break;
            case 'error':
                toast.classList.add('bg-danger', 'text-white');
                break;
            case 'warning':
                toast.classList.add('bg-warning', 'text-dark');
                break;
            default:
                toast.classList.add('bg-info', 'text-white');
        }

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    /**
     * Get status badge class
     */
    getStatusBadgeClass(status) {
        switch (status) {
            case 'published':
                return 'bg-success';
            case 'draft':
                return 'bg-secondary';
            default:
                return 'bg-info';
        }
    }

    /**
     * Capitalize first letter
     */
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * Format date to readable string
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
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
     * Get version history for an FAQ
     */
    async getFAQVersions(faqId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${faqId}/versions`, {
                method: 'GET',
                credentials: 'include'
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching FAQ versions:', error);
            return { success: false, message: 'Failed to fetch version history', versions: [] };
        }
    }

    /**
     * Rollback FAQ to a specific version
     */
    async rollbackFAQ(faqId, versionNumber) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${faqId}/rollback/${versionNumber}`, {
                method: 'POST',
                credentials: 'include'
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error rolling back FAQ:', error);
            return { success: false, message: 'Failed to rollback FAQ' };
        }
    }

    /**
     * Format version timestamp for display
     */
    formatVersionTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return timestamp;
        }
    }
}

// Make FAQManager available globally if window exists
if (typeof window !== 'undefined') {
    window.FAQManager = FAQManager;
}

