class UIManager {
    constructor() {
        this.toast = null;
        this.initializeToast();
    }

    // Initialize toast functionality
    initializeToast() {
        this.toast = new bootstrap.Toast(document.getElementById('toast'));
    }

    // Show toast notification
    showToast(title, message, type = 'info') {
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');
        const toastElement = document.getElementById('toast');

        toastTitle.textContent = title;
        toastMessage.textContent = message;

        // Remove existing classes
        toastElement.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');

        // Add appropriate class based on type
        switch (type) {
            case 'success':
                toastElement.classList.add('bg-success', 'text-white');
                break;
            case 'error':
                toastElement.classList.add('bg-danger', 'text-white');
                break;
            case 'warning':
                toastElement.classList.add('bg-warning', 'text-dark');
                break;
            default:
                toastElement.classList.add('bg-info', 'text-white');
        }

        this.toast.show();
    }

    // Show success toast
    showSuccess(message) {
        this.showToast('Success!', message, 'success');
    }

    // Show error toast
    showError(message) {
        this.showToast('Error!', message, 'error');
    }

    // Show warning toast
    showWarning(message) {
        this.showToast('Warning!', message, 'warning');
    }

    // Show info toast
    showInfo(message) {
        this.showToast('Info', message, 'info');
    }

    // Format date
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Format date and time
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Format relative time (e.g., "2 hours ago", "3 days ago")
    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 2592000) {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 31536000) {
            const months = Math.floor(diffInSeconds / 2592000);
            return `${months} month${months > 1 ? 's' : ''} ago`;
        } else {
            const years = Math.floor(diffInSeconds / 31536000);
            return `${years} year${years > 1 ? 's' : ''} ago`;
        }
    }
    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        }
    }

    // Get status badge HTML
    getStatusBadge(status) {
        const statusMap = {
            'published': { class: 'badge-success', text: 'Published' },
            'draft': { class: 'badge-warning', text: 'Draft' },
            'active': { class: 'badge-success', text: 'Active' },
            'scheduled': { class: 'badge-info', text: 'Scheduled' },
            'inactive': { class: 'badge-neutral', text: 'Inactive' },
            'positive': { class: 'badge-success', text: 'Positive' },
            'negative': { class: 'badge-danger', text: 'Negative' },
            'neutral': { class: 'badge-warning', text: 'Neutral' },
            'high': { class: 'badge-danger', text: 'High' },
            'medium': { class: 'badge-warning', text: 'Medium' },
            'low': { class: 'badge-success', text: 'Low' }
        };

        const statusInfo = statusMap[status] || { class: 'badge-neutral', text: status };
        return `<span class="badge ${statusInfo.class}">${statusInfo.text}</span>`;
    }

    // Get priority badge HTML
    getPriorityBadge(priority) {
        return this.getStatusBadge(priority);
    }

    // Get sentiment badge HTML
    getSentimentBadge(sentiment) {
        return this.getStatusBadge(sentiment);
    }

    // Create action buttons HTML
    getActionButtons(id, actions = ['edit', 'delete']) {
        let buttons = '';
        
        if (actions.includes('view')) {
            buttons += `<button class="action-btn view" onclick="uiManager.viewItem('${id}')" title="View">
                <i class="fas fa-eye"></i>
            </button>`;
        }
        
        if (actions.includes('edit')) {
            buttons += `<button class="action-btn edit" onclick="uiManager.editItem('${id}')" title="Edit">
                <i class="fas fa-edit"></i>
            </button>`;
        }
        
        if (actions.includes('delete')) {
            buttons += `<button class="action-btn delete" onclick="uiManager.deleteItem('${id}')" title="Delete">
                <i class="fas fa-trash"></i>
            </button>`;
        }
        
        return buttons;
    }

    // Show confirmation dialog
    showConfirmation(message, onConfirm, onCancel = null) {
        if (confirm(message)) {
            if (onConfirm) onConfirm();
        } else {
            if (onCancel) onCancel();
        }
    }

    // Show modal
    showModal(modalId) {
        const modal = new bootstrap.Modal(document.getElementById(modalId));
        modal.show();
        return modal;
    }

    // Hide modal
    hideModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
    }

    // Clear form
    clearForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
        }
    }

    // Set form data
    setFormData(formId, data) {
        const form = document.getElementById(formId);
        if (!form) return;

        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = data[key];
            }
        });
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

    // Validate form
    validateForm(formId, rules = {}) {
        const form = document.getElementById(formId);
        if (!form) return { isValid: false, errors: ['Form not found'] };

        const errors = [];
        const formData = this.getFormData(formId);

        Object.keys(rules).forEach(field => {
            const value = formData[field];
            const fieldRules = rules[field];

            if (fieldRules.required && (!value || value.trim() === '')) {
                errors.push(`${field} is required`);
            }

            if (fieldRules.minLength && value && value.length < fieldRules.minLength) {
                errors.push(`${field} must be at least ${fieldRules.minLength} characters`);
            }

            if (fieldRules.maxLength && value && value.length > fieldRules.maxLength) {
                errors.push(`${field} must be no more than ${fieldRules.maxLength} characters`);
            }

            if (fieldRules.pattern && value && !fieldRules.pattern.test(value)) {
                errors.push(`${field} format is invalid`);
            }
        });

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    // Show loading spinner
    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = '<div class="spinner"></div>';
        }
    }

    // Hide loading spinner
    hideLoading(elementId, originalContent) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = originalContent || '';
        }
    }

    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Search functionality
    searchItems(items, searchTerm, searchFields = []) {
        if (!searchTerm) return items;

        const term = searchTerm.toLowerCase();
        return items.filter(item => {
            return searchFields.some(field => {
                const value = item[field];
                return value && value.toString().toLowerCase().includes(term);
            });
        });
    }

    // Sort items
    sortItems(items, sortBy, sortOrder = 'asc') {
        return items.sort((a, b) => {
            let aVal = a[sortBy];
            let bVal = b[sortBy];

            // Handle date sorting
            if (aVal && bVal && !isNaN(new Date(aVal)) && !isNaN(new Date(bVal))) {
                aVal = new Date(aVal);
                bVal = new Date(bVal);
            }

            // Handle string sorting
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }

            if (sortOrder === 'asc') {
                return aVal > bVal ? 1 : -1;
            } else {
                return aVal < bVal ? 1 : -1;
            }
        });
    }

    // Paginate items
    paginateItems(items, page = 1, pageSize = 10) {
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        return {
            items: items.slice(startIndex, endIndex),
            total: items.length,
            page: page,
            pageSize: pageSize,
            totalPages: Math.ceil(items.length / pageSize)
        };
    }

    // Update pagination controls
    updatePagination(paginationData, onPageChange) {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;

        const { page, totalPages } = paginationData;
        let paginationHTML = '';

        // Previous button
        paginationHTML += `
            <li class="page-item ${page === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="uiManager.changePage(${page - 1}, onPageChange)">Previous</a>
            </li>
        `;

        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
                paginationHTML += `
                    <li class="page-item ${i === page ? 'active' : ''}">
                        <a class="page-link" href="#" onclick="uiManager.changePage(${i}, onPageChange)">${i}</a>
                    </li>
                `;
            } else if (i === page - 3 || i === page + 3) {
                paginationHTML += '<li class="page-item disabled"><span class="page-link">...</span></li>';
            }
        }

        // Next button
        paginationHTML += `
            <li class="page-item ${page === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="uiManager.changePage(${page + 1}, onPageChange)">Next</a>
            </li>
        `;

        paginationContainer.innerHTML = paginationHTML;
    }

    // Change page
    changePage(page, onPageChange) {
        if (onPageChange && typeof onPageChange === 'function') {
            onPageChange(page);
        }
    }

    // Export data to CSV
    exportToCSV(data, filename) {
        return window.storageManager.exportToCSV(data, filename);
    }

    // Placeholder methods for item actions
    viewItem(id) {
        console.log('View item:', id);
        // Override in specific modules
    }

    editItem(id) {
        console.log('Edit item:', id);
        // Override in specific modules
    }

    deleteItem(id) {
        console.log('Delete item:', id);
        // Override in specific modules
    }
}

// Initialize global UI manager
window.uiManager = new UIManager();
