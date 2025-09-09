class AnnouncementManager {
    constructor() {
        this.announcements = [];
        this.filteredAnnouncements = [];
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
        console.log('AnnouncementManager initializing...');
        this.loadAnnouncements();
        this.renderAnnouncements();
        this.initializeEventListeners();
        console.log('AnnouncementManager initialized with', this.announcements.length, 'announcements');
    }

    // Load announcements from storage
    loadAnnouncements() {
        try {
            this.announcements = this.storageManager.getAnnouncements();
            this.filteredAnnouncements = [...this.announcements];
            console.log('Loaded announcements:', this.announcements);
        } catch (error) {
            console.error('Error loading announcements:', error);
            this.announcements = [];
            this.filteredAnnouncements = [];
        }
    }

    // Initialize event listeners
    initializeEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('announcementSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchAnnouncements(e.target.value);
            });
        }

        // Override UI manager methods for announcement-specific actions
        if (this.uiManager) {
            this.uiManager.viewItem = (id) => this.viewAnnouncement(id);
            this.uiManager.editItem = (id) => this.editAnnouncement(id);
            this.uiManager.deleteItem = (id) => this.deleteAnnouncement(id);
        }
    }

    // Search announcements
    searchAnnouncements(searchTerm) {
        if (!searchTerm.trim()) {
            this.filteredAnnouncements = [...this.announcements];
        } else {
            this.filteredAnnouncements = this.announcements.filter(announcement => 
                announcement.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                announcement.content.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }
        this.renderAnnouncements();
    }

    // Render announcements table
    renderAnnouncements() {
        const tableBody = document.getElementById('announcementTableBody');
        if (!tableBody) {
            console.error('Announcement table body not found');
            return;
        }

        if (this.filteredAnnouncements.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-muted py-4">
                        <i class="fas fa-inbox fa-2x mb-2"></i>
                        <br>No announcements found
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = this.filteredAnnouncements.map(announcement => `
            <tr>
                <td>
                    <div class="fw-bold">${this.truncate(announcement.title, 50)}</div>
                    <small class="text-muted">${this.truncate(announcement.content, 60)}</small>
                </td>
                <td>
                    <div>${this.formatDate(announcement.startDate)} - ${this.formatDate(announcement.endDate)}</div>
                </td>
                <td>
                    ${this.getPriorityBadge(announcement.priority)}
                </td>
                <td>
                    ${this.getStatusBadge(announcement.status)}
                </td>
                <td>
                    <div class="d-flex gap-2">
                        <button class="action-btn edit" onclick="editAnnouncement('${announcement.id}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn view" onclick="viewAnnouncement('${announcement.id}')" title="View">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="action-btn delete" onclick="deleteAnnouncement('${announcement.id}')" title="Delete">
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

    // Helper method to get priority badge
    getPriorityBadge(priority) {
        const priorityMap = {
            'high': { class: 'badge bg-danger', text: 'High' },
            'medium': { class: 'badge bg-warning', text: 'Medium' },
            'low': { class: 'badge bg-success', text: 'Low' }
        };

        const priorityInfo = priorityMap[priority] || { class: 'badge bg-secondary', text: priority };
        return `<span class="${priorityInfo.class}">${priorityInfo.text}</span>`;
    }

    // Helper method to get status badge
    getStatusBadge(status) {
        const statusMap = {
            'active': { class: 'badge bg-success', text: 'Active' },
            'scheduled': { class: 'badge bg-info', text: 'Scheduled' },
            'draft': { class: 'badge bg-warning', text: 'Draft' },
            'inactive': { class: 'badge bg-secondary', text: 'Inactive' }
        };

        const statusInfo = statusMap[status] || { class: 'badge bg-secondary', text: status };
        return `<span class="${statusInfo.class}">${statusInfo.text}</span>`;
    }

    // Helper method to format date
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'numeric',
            day: 'numeric',
            year: 'numeric'
        });
    }

    // View announcement details
    viewAnnouncement(id) {
        console.log('Viewing announcement with ID:', id);
        const announcement = this.announcements.find(a => a.id === id);
        if (!announcement) {
            this.showError('Announcement not found');
            return;
        }

        // Populate view modal
        document.getElementById('viewAnnouncementTitle').textContent = announcement.title;
        document.getElementById('viewAnnouncementContent').textContent = announcement.content;
        document.getElementById('viewAnnouncementStartDate').textContent = this.formatDate(announcement.startDate);
        document.getElementById('viewAnnouncementEndDate').textContent = this.formatDate(announcement.endDate);
        document.getElementById('viewAnnouncementPriority').innerHTML = this.getPriorityBadge(announcement.priority);
        document.getElementById('viewAnnouncementStatus').innerHTML = this.getStatusBadge(announcement.status);
        document.getElementById('viewAnnouncementCreated').textContent = this.formatDateTime(announcement.createdAt);
        document.getElementById('viewAnnouncementUpdated').textContent = this.formatDateTime(announcement.updatedAt);

        // Show modal
        this.showModal('viewAnnouncementModal');
    }

    // Edit announcement
    editAnnouncement(id) {
        console.log('Editing announcement with ID:', id);
        const announcement = this.announcements.find(a => a.id === id);
        if (!announcement) {
            this.showError('Announcement not found');
            return;
        }

        this.currentEditId = id;

        // Populate form
        document.getElementById('announcementModalLabel').textContent = 'Edit Announcement';
        document.getElementById('announcementId').value = announcement.id;
        document.getElementById('announcementTitle').value = announcement.title;
        document.getElementById('announcementContent').value = announcement.content;
        document.getElementById('announcementStartDate').value = announcement.startDate;
        document.getElementById('announcementEndDate').value = announcement.endDate;
        document.getElementById('announcementPriority').value = announcement.priority;
        document.getElementById('announcementStatus').value = announcement.status;
        document.querySelector('#announcementModal .btn-primary').textContent = 'Update';

        // Show modal
        this.showModal('announcementModal');
    }

    // Save announcement (create or update)
    saveAnnouncement() {
        console.log('Saving announcement...');
        const formData = this.getFormData('announcementForm');
        
        // Validate form
        const validation = this.validateAnnouncementData(formData);
        if (!validation.isValid) {
            this.showError(validation.errors.join(', '));
            return;
        }

        if (this.currentEditId) {
            // Update existing announcement
            const success = this.storageManager.updateAnnouncement(this.currentEditId, {
                title: formData.title,
                content: formData.content,
                startDate: formData.startDate,
                endDate: formData.endDate,
                priority: formData.priority,
                status: formData.status
            });

            if (success) {
                this.showSuccess('Announcement Updated Successfully!');
                this.hideModal('announcementModal');
                this.refreshData();
            } else {
                this.showError('Failed to update announcement');
            }
        } else {
            // Create new announcement
            const success = this.storageManager.addAnnouncement({
                title: formData.title,
                content: formData.content,
                startDate: formData.startDate,
                endDate: formData.endDate,
                priority: formData.priority,
                status: formData.status
            });

            if (success) {
                this.showSuccess('Announcement Added Successfully!');
                this.hideModal('announcementModal');
                this.refreshData();
            } else {
                this.showError('Failed to add announcement');
            }
        }

        this.currentEditId = null;
    }

    // Delete announcement
    deleteAnnouncement(id) {
        console.log('Deleting announcement with ID:', id);
        const announcement = this.announcements.find(a => a.id === id);
        if (!announcement) {
            this.showError('Announcement not found');
            return;
        }

        if (confirm(`Are you sure you want to delete the announcement "${announcement.title}"?`)) {
            const success = this.storageManager.deleteAnnouncement(id);
            if (success) {
                this.showSuccess('Announcement Deleted Successfully!');
                this.refreshData();
            } else {
                this.showError('Failed to delete announcement');
            }
        }
    }

    // Refresh data and re-render
    refreshData() {
        this.loadAnnouncements();
        this.renderAnnouncements();
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

    // Validate announcement data
    validateAnnouncementData(data) {
        const errors = [];

        if (!data.title || data.title.trim().length < 5) {
            errors.push('Title must be at least 5 characters long');
        }

        if (!data.content || data.content.trim().length < 10) {
            errors.push('Content must be at least 10 characters long');
        }

        if (!data.startDate) {
            errors.push('Start date is required');
        }

        if (!data.endDate) {
            errors.push('End date is required');
        }

        if (data.startDate && data.endDate && new Date(data.startDate) >= new Date(data.endDate)) {
            errors.push('End date must be after start date');
        }

        if (!data.priority || !['low', 'medium', 'high'].includes(data.priority)) {
            errors.push('Priority must be low, medium, or high');
        }

        if (!data.status || !['draft', 'scheduled', 'active', 'inactive'].includes(data.status)) {
            errors.push('Status must be draft, scheduled, active, or inactive');
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

    // Get announcement by ID
    getAnnouncementById(id) {
        return this.announcements.find(a => a.id === id);
    }

    // Get announcements by status
    getAnnouncementsByStatus(status) {
        return this.announcements.filter(a => a.status === status);
    }

    // Get active announcements
    getActiveAnnouncements() {
        return this.getAnnouncementsByStatus('active');
    }

    // Get scheduled announcements
    getScheduledAnnouncements() {
        return this.getAnnouncementsByStatus('scheduled');
    }

    // Get draft announcements
    getDraftAnnouncements() {
        return this.getAnnouncementsByStatus('draft');
    }

    // Get announcements by priority
    getAnnouncementsByPriority(priority) {
        return this.announcements.filter(a => a.priority === priority);
    }

    // Get current announcements (active and within date range)
    getCurrentAnnouncements() {
        const today = new Date().toISOString().split('T')[0];
        return this.announcements.filter(announcement => 
            announcement.status === 'active' &&
            announcement.startDate <= today &&
            announcement.endDate >= today
        );
    }

    // Get upcoming announcements
    getUpcomingAnnouncements() {
        const today = new Date().toISOString().split('T')[0];
        return this.announcements.filter(announcement => 
            announcement.startDate > today
        );
    }

    // Get expired announcements
    getExpiredAnnouncements() {
        const today = new Date().toISOString().split('T')[0];
        return this.announcements.filter(announcement => 
            announcement.endDate < today
        );
    }

    // Get announcement statistics
    getAnnouncementStats() {
        const total = this.announcements.length;
        const active = this.getActiveAnnouncements().length;
        const scheduled = this.getScheduledAnnouncements().length;
        const draft = this.getDraftAnnouncements().length;
        const current = this.getCurrentAnnouncements().length;
        const upcoming = this.getUpcomingAnnouncements().length;
        const expired = this.getExpiredAnnouncements().length;

        return {
            total,
            active,
            scheduled,
            draft,
            current,
            upcoming,
            expired,
            activePercentage: total > 0 ? Math.round((active / total) * 100) : 0,
            scheduledPercentage: total > 0 ? Math.round((scheduled / total) * 100) : 0,
            draftPercentage: total > 0 ? Math.round((draft / total) * 100) : 0
        };
    }
}

// Initialize global announcement manager
window.AnnouncementManager = AnnouncementManager;
