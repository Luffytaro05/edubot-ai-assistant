/**
 * SubAdminNotificationManager.js
 * Manages sub-admin notifications from all content areas
 */

class SubAdminNotificationManager {
    constructor() {
        this.notifications = [];
        this.unreadCount = 0;
        this.isDropdownOpen = false;
        this.refreshInterval = 60000; // Refresh every 60 seconds
        this.intervalId = null;
    }

    /**
     * Initialize the notification manager
     */
    async initialize() {
        try {
            console.log('Initializing SubAdminNotificationManager...');
            
            // Set up event listeners
            this.setupEventListeners();
            
            // Load notifications
            await this.loadNotifications();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            console.log('SubAdminNotificationManager initialized successfully');
        } catch (error) {
            console.error('Error initializing SubAdminNotificationManager:', error);
        }
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Notification bell click
        const notificationBell = document.querySelector('.notification-bell');
        if (notificationBell) {
            notificationBell.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const notificationDropdown = document.getElementById('subAdminNotificationDropdown');
            const notificationBell = document.querySelector('.notification-bell');
            
            if (notificationDropdown && 
                !notificationDropdown.contains(e.target) && 
                !notificationBell.contains(e.target)) {
                this.closeDropdown();
            }
        });

        // Refresh button
        const refreshBtn = document.getElementById('subAdminNotificationRefreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadNotifications();
            });
        }

        // Mark all as read button
        const markAllReadBtn = document.getElementById('subAdminNotificationMarkAllReadBtn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
    }

    /**
     * Load notifications from backend
     */
    async loadNotifications() {
        try {
            const response = await fetch('/api/sub-admin/notifications', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    console.warn('Unauthorized - session may be expired');
                }
                throw new Error('Failed to fetch notifications');
            }

            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications || [];
                this.unreadCount = data.unread_count || 0;
                this.updateUI();
            } else {
                console.error('Error loading notifications:', data.message);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            // Show default state if error
            this.notifications = [];
            this.unreadCount = 0;
            this.updateUI();
        }
    }

    /**
     * Update the UI with current notifications
     */
    updateUI() {
        // Update badge count
        this.updateBadge();
        
        // Update dropdown content
        this.updateDropdownContent();
    }

    /**
     * Update notification badge
     */
    updateBadge() {
        const badge = document.querySelector('.notification-dot');
        if (badge) {
            if (this.unreadCount > 0) {
                badge.style.display = 'block';
                badge.setAttribute('data-count', this.unreadCount > 99 ? '99+' : this.unreadCount);
            } else {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * Update dropdown content
     */
    updateDropdownContent() {
        const notificationList = document.getElementById('subAdminNotificationList');
        if (!notificationList) return;

        if (this.notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>No new notifications</p>
                </div>
            `;
            return;
        }

        notificationList.innerHTML = this.notifications.map(notification => {
            return this.createNotificationHTML(notification);
        }).join('');

        // Add click listeners to notification items
        const notificationItems = notificationList.querySelectorAll('.notification-item');
        notificationItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const link = item.dataset.link;
                if (link) {
                    window.location.href = link;
                }
            });
        });
    }

    /**
     * Create HTML for a single notification
     */
    createNotificationHTML(notification) {
        const colorClass = this.getColorClass(notification.color);
        const icon = notification.icon || 'fa-bell';
        const timeAgo = this.getTimeAgo(notification.time);

        return `
            <div class="notification-item ${colorClass}" data-id="${notification.id}" data-link="${notification.link}">
                <div class="notification-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }

    /**
     * Get color class based on notification color
     */
    getColorClass(color) {
        const colorMap = {
            'success': 'notification-success',
            'warning': 'notification-warning',
            'danger': 'notification-danger',
            'info': 'notification-info',
            'primary': 'notification-primary'
        };
        return colorMap[color] || 'notification-default';
    }

    /**
     * Get time ago string
     */
    getTimeAgo(timeString) {
        try {
            const time = new Date(timeString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - time) / 1000);

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
        } catch (error) {
            return timeString;
        }
    }

    /**
     * Toggle notification dropdown
     */
    toggleDropdown() {
        if (this.isDropdownOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    /**
     * Open notification dropdown
     */
    openDropdown() {
        const dropdown = document.getElementById('subAdminNotificationDropdown');
        if (dropdown) {
            dropdown.classList.add('show');
            this.isDropdownOpen = true;
            
            // Refresh notifications when opening
            this.loadNotifications();
        }
    }

    /**
     * Close notification dropdown
     */
    closeDropdown() {
        const dropdown = document.getElementById('subAdminNotificationDropdown');
        if (dropdown) {
            dropdown.classList.remove('show');
            this.isDropdownOpen = false;
        }
    }

    /**
     * Mark all notifications as read
     */
    markAllAsRead() {
        this.unreadCount = 0;
        this.updateBadge();
        this.closeDropdown();
        
        console.log('All notifications marked as read');
    }

    /**
     * Start auto-refresh timer
     */
    startAutoRefresh() {
        // Clear existing interval if any
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        // Set up new interval
        this.intervalId = setInterval(() => {
            this.loadNotifications();
        }, this.refreshInterval);

        console.log('Auto-refresh started (every 60 seconds)');
    }

    /**
     * Stop auto-refresh timer
     */
    stopAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('Auto-refresh stopped');
        }
    }

    /**
     * Destroy the notification manager
     */
    destroy() {
        this.stopAutoRefresh();
        this.notifications = [];
        this.unreadCount = 0;
    }
}

// Export for use in other files
if (typeof window !== 'undefined') {
    window.SubAdminNotificationManager = SubAdminNotificationManager;
}

