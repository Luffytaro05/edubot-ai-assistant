// AnnouncementManager.js - Handles announcement operations for Sub-Admin
class AnnouncementManager {
    constructor() {
        this.announcements = [];
        this.currentAnnouncementId = null;
        this.searchTimeout = null;
    }

    initialize() {
        console.log('Initializing AnnouncementManager...');
        this.setupEventListeners();
        this.loadAnnouncements();
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('announcementSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.filterAnnouncements(e.target.value);
                }, 300);
            });
        }

        // Form submission
        const form = document.getElementById('announcementForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveAnnouncement();
            });
        }
    }

    async loadAnnouncements() {
        try {
            console.log('Loading announcements...');
            const response = await fetch('/api/sub-announcements/list', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.announcements = data.announcements || [];
                this.renderAnnouncements();
                console.log(`Loaded ${this.announcements.length} announcements`);
            } else {
                console.error('Error loading announcements:', data.message);
                this.showToast('Error', data.message || 'Failed to load announcements', 'error');
            }
        } catch (error) {
            console.error('Error loading announcements:', error);
            this.showToast('Error', 'Failed to load announcements', 'error');
        }
    }

    renderAnnouncements(announcementsToRender = null) {
        const tbody = document.getElementById('announcementTableBody');
        if (!tbody) {
            console.error('Announcement table body not found');
            return;
        }

        const announcements = announcementsToRender || this.announcements;

        if (announcements.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No announcements found. Create your first announcement!</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = announcements.map(announcement => {
            const priorityBadge = this.getPriorityBadge(announcement.priority);
            const statusBadge = this.getStatusBadge(announcement.status);
            const dateRange = `${this.formatDate(announcement.start_date)} - ${this.formatDate(announcement.end_date)}`;

            return `
                <tr>
                    <td>
                        <strong>${this.escapeHtml(announcement.title)}</strong>
                        <br>
                        <small class="text-muted">${this.truncateText(announcement.description, 60)}</small>
                    </td>
                    <td>${dateRange}</td>
                    <td>${priorityBadge}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="viewAnnouncement('${announcement._id}')" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="editAnnouncement('${announcement._id}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="deleteAnnouncement('${announcement._id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    filterAnnouncements(searchTerm) {
        if (!searchTerm) {
            this.renderAnnouncements();
            return;
        }

        const term = searchTerm.toLowerCase();
        const filtered = this.announcements.filter(announcement => {
            return announcement.title.toLowerCase().includes(term) ||
                   announcement.description.toLowerCase().includes(term) ||
                   announcement.priority.toLowerCase().includes(term) ||
                   announcement.status.toLowerCase().includes(term);
        });

        this.renderAnnouncements(filtered);
    }

    async saveAnnouncement() {
        try {
            const announcementId = document.getElementById('announcementId').value;
            const title = document.getElementById('announcementTitle').value.trim();
            const content = document.getElementById('announcementContent').value.trim();
            const startDate = document.getElementById('announcementStartDate').value;
            const endDate = document.getElementById('announcementEndDate').value;
            const priority = document.getElementById('announcementPriority').value;
            const status = document.getElementById('announcementStatus').value;

            // Validation
            if (!title || !content || !startDate || !endDate) {
                this.showToast('Validation Error', 'Please fill in all required fields', 'error');
                return;
            }

            // Check date validity
            if (new Date(startDate) > new Date(endDate)) {
                this.showToast('Validation Error', 'End date must be after start date', 'error');
                return;
            }

            const announcementData = {
                title,
                content,
                startDate,
                endDate,
                priority,
                status
            };

            let response;
            let successMessage;

            if (announcementId) {
                // Update existing announcement
                response = await fetch(`/api/sub-announcements/update/${announcementId}`, {
                    method: 'PUT',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(announcementData)
                });
                successMessage = 'Announcement updated successfully!';
            } else {
                // Create new announcement
                response = await fetch('/api/sub-announcements/add', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(announcementData)
                });
                successMessage = 'Announcement created successfully and synced to chatbot!';
            }

            const data = await response.json();

            if (data.success) {
                this.showToast('Success', successMessage, 'success');
                this.closeModal('announcementModal');
                this.loadAnnouncements(); // Reload announcements
            } else {
                this.showToast('Error', data.message || 'Failed to save announcement', 'error');
            }
        } catch (error) {
            console.error('Error saving announcement:', error);
            this.showToast('Error', 'Failed to save announcement', 'error');
        }
    }

    async viewAnnouncement(id) {
        try {
            const response = await fetch(`/api/sub-announcements/get/${id}`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success && data.announcement) {
                const ann = data.announcement;
                
                // Populate view modal
                document.getElementById('viewAnnouncementTitle').textContent = ann.title;
                document.getElementById('viewAnnouncementContent').textContent = ann.description;
                document.getElementById('viewAnnouncementStartDate').textContent = this.formatDate(ann.start_date);
                document.getElementById('viewAnnouncementEndDate').textContent = this.formatDate(ann.end_date);
                document.getElementById('viewAnnouncementPriority').innerHTML = this.getPriorityBadge(ann.priority);
                document.getElementById('viewAnnouncementStatus').innerHTML = this.getStatusBadge(ann.status);
                document.getElementById('viewAnnouncementCreated').textContent = this.formatDateTime(ann.created_at);
                document.getElementById('viewAnnouncementUpdated').textContent = this.formatDateTime(ann.updated_at);

                this.showModal('viewAnnouncementModal');
            } else {
                this.showToast('Error', 'Failed to load announcement details', 'error');
            }
        } catch (error) {
            console.error('Error viewing announcement:', error);
            this.showToast('Error', 'Failed to load announcement details', 'error');
        }
    }

    async editAnnouncement(id) {
        try {
            const response = await fetch(`/api/sub-announcements/get/${id}`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success && data.announcement) {
                const ann = data.announcement;
                
                // Populate edit modal
                document.getElementById('announcementModalLabel').textContent = 'Edit Announcement';
                document.getElementById('announcementId').value = ann._id;
                document.getElementById('announcementTitle').value = ann.title;
                document.getElementById('announcementContent').value = ann.description;
                document.getElementById('announcementStartDate').value = ann.start_date;
                document.getElementById('announcementEndDate').value = ann.end_date;
                document.getElementById('announcementPriority').value = ann.priority;
                document.getElementById('announcementStatus').value = ann.status;

                this.showModal('announcementModal');
            } else {
                this.showToast('Error', 'Failed to load announcement for editing', 'error');
            }
        } catch (error) {
            console.error('Error loading announcement for edit:', error);
            this.showToast('Error', 'Failed to load announcement for editing', 'error');
        }
    }

    async deleteAnnouncement(id) {
        if (!confirm('Are you sure you want to delete this announcement? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/sub-announcements/delete/${id}`, {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Success', 'Announcement deleted successfully', 'success');
                this.loadAnnouncements(); // Reload announcements
            } else {
                this.showToast('Error', data.message || 'Failed to delete announcement', 'error');
            }
        } catch (error) {
            console.error('Error deleting announcement:', error);
            this.showToast('Error', 'Failed to delete announcement', 'error');
        }
    }

    // Utility methods
    getPriorityBadge(priority) {
        const badges = {
            'high': '<span class="badge bg-danger">High</span>',
            'medium': '<span class="badge bg-warning">Medium</span>',
            'low': '<span class="badge bg-info">Low</span>'
        };
        return badges[priority.toLowerCase()] || badges['medium'];
    }

    getStatusBadge(status) {
        const badges = {
            'active': '<span class="badge bg-success">Active</span>',
            'inactive': '<span class="badge bg-secondary">Inactive</span>',
            'scheduled': '<span class="badge bg-primary">Scheduled</span>',
            'draft': '<span class="badge bg-dark">Draft</span>'
        };
        return badges[status.toLowerCase()] || badges['draft'];
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }

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

    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return this.escapeHtml(text);
        return this.escapeHtml(text.substring(0, maxLength)) + '...';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
    }

    closeModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }
    }

    showToast(title, message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');

        if (toast && toastTitle && toastMessage) {
            toastTitle.textContent = title;
            toastMessage.textContent = message;

            // Remove previous color classes
            toast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');

            // Add appropriate color based on type
            switch (type) {
                case 'success':
                    toast.classList.add('bg-success', 'text-white');
                    break;
                case 'error':
                    toast.classList.add('bg-danger', 'text-white');
                    break;
                case 'warning':
                    toast.classList.add('bg-warning');
                    break;
                default:
                    toast.classList.add('bg-info', 'text-white');
            }

            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
    }
}

// Make AnnouncementManager available globally
if (typeof window !== 'undefined') {
    window.AnnouncementManager = AnnouncementManager;
}

