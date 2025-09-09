class FAQManager {
    constructor() {
        this.faqs = [];
        this.filteredFAQs = [];
        this.currentEditId = null;
        this.initializeManagers();
    }

    initializeManagers() {
        // Get managers from global scope
        this.storageManager = window.storageManager || new StorageManager();
        this.uiManager = window.uiManager || new UIManager();
        
        // Set global references for backward compatibility
        if (!window.storageManager) window.storageManager = this.storageManager;
        if (!window.uiManager) window.uiManager = this.uiManager;
    }

    initialize() {
        console.log('FAQManager initializing...');
        this.loadFAQs();
        this.renderFAQs();
        this.initializeEventListeners();
        console.log('FAQManager initialized with', this.faqs.length, 'FAQs');
    }

    // Load FAQs from storage
    loadFAQs() {
        try {
            this.faqs = this.storageManager.getFAQs();
            this.filteredFAQs = [...this.faqs];
            console.log('Loaded FAQs:', this.faqs);
        } catch (error) {
            console.error('Error loading FAQs:', error);
            this.faqs = [];
            this.filteredFAQs = [];
        }
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('faqSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchFAQs(e.target.value);
            });
        }

        // Override UI manager methods for FAQ-specific actions
        if (this.uiManager) {
            this.uiManager.viewItem = (id) => this.viewFAQ(id);
            this.uiManager.editItem = (id) => this.editFAQ(id);
            this.uiManager.deleteItem = (id) => this.deleteFAQ(id);
        }
    }

    // Search FAQs
    searchFAQs(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredFAQs = [...this.faqs];
        } else {
            this.filteredFAQs = this.faqs.filter(faq => 
                faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
                faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }
        this.renderFAQs();
    }

    // Render FAQs table
    renderFAQs() {
        const tableBody = document.getElementById('faqTableBody');
        if (!tableBody) {
            console.error('FAQ table body not found');
            return;
        }

        if (this.filteredFAQs.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-muted py-4">
                        <i class="fas fa-inbox fa-2x mb-2"></i>
                        <br>No FAQs found
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = this.filteredFAQs.map(faq => `
            <tr>
                <td>
                    <div class="fw-bold">${this.truncate(faq.question, 60)}</div>
                </td>
                <td>
                    <div>${this.truncate(faq.answer, 80)}</div>
                </td>
                <td>
                    ${this.getStatusBadge(faq.status)}
                </td>
                <td>
                    <div class="d-flex gap-2">
                        <button class="action-btn view" onclick="viewFAQ('${faq.id}')" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="action-btn edit" onclick="editFAQ('${faq.id}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="deleteFAQ('${faq.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    // Helper method to truncate text
    truncate(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // Helper method to get status badge
    getStatusBadge(status) {
        const statusMap = {
            'published': { class: 'badge bg-success', text: 'Published' },
            'draft': { class: 'badge bg-warning', text: 'Draft' }
        };

        const statusInfo = statusMap[status] || { class: 'badge bg-secondary', text: status };
        return `<span class="${statusInfo.class}">${statusInfo.text}</span>`;
    }

    // View FAQ details
    viewFAQ(id) {
        console.log('Viewing FAQ with ID:', id);
        const faq = this.faqs.find(f => f.id === id);
        if (!faq) {
            this.showError('FAQ not found');
            return;
        }

        // Populate view modal
        document.getElementById('viewFAQQuestion').textContent = faq.question;
        document.getElementById('viewFAQAnswer').textContent = faq.answer;
        document.getElementById('viewFAQStatus').innerHTML = this.getStatusBadge(faq.status);
        document.getElementById('viewFAQCreated').textContent = this.formatDateTime(faq.createdAt);
        document.getElementById('viewFAQUpdated').textContent = this.formatDateTime(faq.updatedAt);

        // Show modal
        this.showModal('viewFAQModal');
    }

    // Edit FAQ
    editFAQ(id) {
        console.log('Editing FAQ with ID:', id);
        const faq = this.faqs.find(f => f.id === id);
        if (!faq) {
            this.showError('FAQ not found');
            return;
        }

        this.currentEditId = id;

        // Populate form
        document.getElementById('faqModalLabel').textContent = 'Edit FAQ';
        document.getElementById('faqId').value = faq.id;
        document.getElementById('faqQuestion').value = faq.question;
        document.getElementById('faqAnswer').value = faq.answer;
        document.getElementById('faqStatus').value = faq.status;
        document.querySelector('#faqModal .btn-primary').textContent = 'Update';

        // Show modal
        this.showModal('faqModal');
    }

    // Save FAQ (create or update)
    saveFAQ() {
        console.log('Saving FAQ...');
        const formData = this.getFormData('faqForm');
        
        // Validate form
        const validation = this.validateFAQData(formData);
        if (!validation.isValid) {
            this.showError(validation.errors.join(', '));
            return;
        }

        if (this.currentEditId) {
            // Update existing FAQ
            const success = this.storageManager.updateFAQ(this.currentEditId, {
                question: formData.question,
                answer: formData.answer,
                status: formData.status
            });

            if (success) {
                this.showSuccess('FAQ Updated Successfully!');
                this.hideModal('faqModal');
                this.refreshData();
            } else {
                this.showError('Failed to update FAQ');
            }
        } else {
            // Create new FAQ
            const success = this.storageManager.addFAQ({
                question: formData.question,
                answer: formData.answer,
                status: formData.status
            });

            if (success) {
                this.showSuccess('FAQ Added Successfully!');
                this.hideModal('faqModal');
                this.refreshData();
            } else {
                this.showError('Failed to add FAQ');
            }
        }

        this.currentEditId = null;
    }

    // Delete FAQ
    deleteFAQ(id) {
        console.log('Deleting FAQ with ID:', id);
        const faq = this.faqs.find(f => f.id === id);
        if (!faq) {
            this.showError('FAQ not found');
            return;
        }

        if (confirm(`Are you sure you want to delete the FAQ "${faq.question}"?`)) {
            const success = this.storageManager.deleteFAQ(id);
            if (success) {
                this.showSuccess('FAQ Deleted Successfully!');
                this.refreshData();
            } else {
                this.showError('Failed to delete FAQ');
            }
        }
    }

    // Refresh data and re-render
    refreshData() {
        this.loadFAQs();
        this.renderFAQs();
    }

    // Get form data
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};

        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    }

    // Validate FAQ data
    validateFAQData(data) {
        const errors = [];

        if (!data.question || data.question.trim().length < 10) {
            errors.push('Question must be at least 10 characters long');
        }

        if (!data.answer || data.answer.trim().length < 20) {
            errors.push('Answer must be at least 20 characters long');
        }

        if (!data.status || !['draft', 'published'].includes(data.status)) {
            errors.push('Status must be either draft or published');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    // Format date and time
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Show modal
    showModal(modalId) {
        try {
            if (this.uiManager && this.uiManager.showModal) {
                this.uiManager.showModal(modalId);
            } else {
                const modal = new bootstrap.Modal(document.getElementById(modalId));
                modal.show();
            }
        } catch (error) {
            console.error('Error showing modal:', error);
            // Fallback to Bootstrap modal
            const modal = new bootstrap.Modal(document.getElementById(modalId));
            modal.show();
        }
    }

    // Hide modal
    hideModal(modalId) {
        try {
            if (this.uiManager && this.uiManager.hideModal) {
                this.uiManager.hideModal(modalId);
            } else {
                const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
                if (modal) {
                    modal.hide();
                }
            }
        } catch (error) {
            console.error('Error hiding modal:', error);
        }
    }

    // Show success message
    showSuccess(message) {
        try {
            if (this.uiManager && this.uiManager.showSuccess) {
                this.uiManager.showSuccess(message);
            } else {
                alert('Success: ' + message);
            }
        } catch (error) {
            console.error('Error showing success:', error);
            alert('Success: ' + message);
        }
    }

    // Show error message
    showError(message) {
        try {
            if (this.uiManager && this.uiManager.showError) {
                this.uiManager.showError(message);
            } else {
                alert('Error: ' + message);
            }
        } catch (error) {
            console.error('Error showing error:', error);
            alert('Error: ' + message);
        }
    }

    // Get FAQ by ID
    getFAQById(id) {
        return this.faqs.find(f => f.id === id);
    }

    // Get FAQs by status
    getFAQsByStatus(status) {
        return this.faqs.filter(f => f.status === status);
    }

    // Get published FAQs
    getPublishedFAQs() {
        return this.getFAQsByStatus('published');
    }

    // Get draft FAQs
    getDraftFAQs() {
        return this.getFAQsByStatus('draft');
    }

    // Get FAQ statistics
    getFAQStats() {
        const total = this.faqs.length;
        const published = this.getPublishedFAQs().length;
        const draft = this.getDraftFAQs().length;

        return {
            total,
            published,
            draft,
            publishedPercentage: total > 0 ? Math.round((published / total) * 100) : 0,
            draftPercentage: total > 0 ? Math.round((draft / total) * 100) : 0
        };
    }
}

// Initialize global FAQ manager
window.FAQManager = FAQManager;
