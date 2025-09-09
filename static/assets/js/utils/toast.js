/**
 * ToastManager - Global toast notification system
 */
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    /**
     * Initialize toast container
     */
    init() {
        // Create toast container if it doesn't exist
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    /**
     * Show success toast
     */
    success(message, duration = 4000) {
        this.showToast(message, 'success', duration);
    }

    /**
     * Show error toast
     */
    error(message, duration = 6000) {
        this.showToast(message, 'error', duration);
    }

    /**
     * Show warning toast
     */
    warning(message, duration = 5000) {
        this.showToast(message, 'warning', duration);
    }

    /**
     * Show info toast
     */
    info(message, duration = 4000) {
        this.showToast(message, 'info', duration);
    }

    /**
     * Show toast with custom type and duration
     */
    showToast(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icon = this.getIcon(type);
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    ${icon}
                </div>
                <div class="toast-message">
                    ${message}
                </div>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="toast-progress"></div>
        `;

        this.container.appendChild(toast);

        // Add show class after a small delay for animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        }

        // Start progress bar animation
        const progressBar = toast.querySelector('.toast-progress');
        if (progressBar) {
            progressBar.style.transition = `width ${duration}ms linear`;
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 10);
        }
    }

    /**
     * Remove specific toast
     */
    removeToast(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    }

    /**
     * Get icon for toast type
     */
    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    /**
     * Clear all toasts
     */
    clearAll() {
        const toasts = this.container.querySelectorAll('.toast');
        toasts.forEach(toast => this.removeToast(toast));
    }
}

// Create global toast instance
const toast = new ToastManager();

// Add toast styles to document if not already present
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            min-width: 300px;
            max-width: 400px;
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease;
            overflow: hidden;
        }

        .toast.show {
            transform: translateX(0);
            opacity: 1;
        }

        .toast-content {
            display: flex;
            align-items: center;
            padding: 16px;
            gap: 12px;
        }

        .toast-icon {
            font-size: 20px;
            flex-shrink: 0;
        }

        .toast-message {
            flex: 1;
            font-size: 14px;
            line-height: 1.4;
            color: #2c3e50;
        }

        .toast-close {
            background: none;
            border: none;
            color: #6c757d;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            transition: color 0.2s ease;
        }

        .toast-close:hover {
            color: #2c3e50;
        }

        .toast-progress {
            height: 3px;
            width: 100%;
            background: #e9ecef;
        }

        .toast-success {
            border-left: 4px solid #28a745;
        }

        .toast-success .toast-icon {
            color: #28a745;
        }

        .toast-success .toast-progress {
            background: #28a745;
        }

        .toast-error {
            border-left: 4px solid #dc3545;
        }

        .toast-error .toast-icon {
            color: #dc3545;
        }

        .toast-error .toast-progress {
            background: #dc3545;
        }

        .toast-warning {
            border-left: 4px solid #ffc107;
        }

        .toast-warning .toast-icon {
            color: #ffc107;
        }

        .toast-warning .toast-progress {
            background: #ffc107;
        }

        .toast-info {
            border-left: 4px solid #17a2b8;
        }

        .toast-info .toast-icon {
            color: #17a2b8;
        }

        .toast-info .toast-progress {
            background: #17a2b8;
        }

        @media (max-width: 768px) {
            .toast-container {
                top: 10px;
                right: 10px;
                left: 10px;
            }

            .toast {
                min-width: auto;
                max-width: none;
            }
        }
    `;
    document.head.appendChild(style);
}
