/**
 * app.js - Main application controller for EduChat Admin Portal
 * Integrates MongoDB authentication with UI components and manages application state
 */

class EduChatApp {
    constructor() {
        this.authManager = null;
        this.currentUser = null;
        this.isInitialized = false;
        this.config = {
            sessionWarningTime: 5 * 60 * 1000, // 5 minutes
            autoSaveInterval: 30 * 1000, // 30 seconds
            maxLoginAttempts: 5,
            lockoutDuration: 15 * 60 * 1000 // 15 minutes
        };
        
        // Bind methods to maintain context
        this.handleSessionWarning = this.handleSessionWarning.bind(this);
        this.handleBeforeUnload = this.handleBeforeUnload.bind(this);
        this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            console.log('Initializing EduChat Admin Portal...');
            
            // Initialize authentication manager
            this.authManager = new AuthManager();
            
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            } else {
                this.onDOMReady();
            }
            
            // Set up global event listeners
            this.setupGlobalEventListeners();
            
            console.log('EduChat Admin Portal initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
        }
    }

    /**
     * Handle DOM ready event
     */
    async onDOMReady() {
        try {
            // Initialize toast notifications
            this.initializeToast();
            
            // Initialize Bot Settings manager on settings page
            if (window.location.pathname.includes('settings')) {
                try {
                    this.botSettingsManager = new BotSettingsManager();
                } catch (e) {
                    console.error('BotSettingsManager init failed:', e);
                }
            }

            // Determine current page and initialize accordingly
            const currentPage = this.getCurrentPage();
            
            switch (currentPage) {
                case 'login':
                    await this.initializeLoginPage();
                    break;
                case 'dashboard':
                    await this.initializeDashboard();
                    break;
                case 'sub-dashboard':
                    await this.initializeSubDashboard();
                    break;
                default:
                    console.warn('Unknown page type:', currentPage);
            }
            
            this.isInitialized = true;
            
        } catch (error) {
            console.error('DOM initialization failed:', error);
            this.showError('Page initialization failed. Please refresh the page.');
        }
    }

    /**
     * Get current page type based on URL
     */
    getCurrentPage() {
        const path = window.location.pathname;
        const search = window.location.search;
        
        if (path.includes('login') || path === '/' || path === '/index.html') {
            return 'login';
        } else if (path.includes('dashboard')) {
            return search.includes('office=') ? 'sub-dashboard' : 'dashboard';
        } else if (path.includes('Sub-dashboard')) {
            return 'sub-dashboard';
        }
        
        return 'unknown';
    }

    /**
     * Initialize login page
     */
    async initializeLoginPage() {
        console.log('Initializing login page...');
        
        // Check if user is already authenticated
        if (this.authManager.isAuthenticated()) {
            const user = this.authManager.getCurrentUser();
            this.redirectToUserDashboard(user);
            return;
        }
        
        // Set up login form handlers
        this.setupLoginFormHandlers();
        
        // Check for login attempts tracking
        this.setupLoginAttemptTracking();
        
        // Focus on first input
        const firstInput = document.querySelector('#role');
        if (firstInput) {
            firstInput.focus();
        }
    }

    /**
     * Initialize main admin dashboard
     */
    async initializeDashboard() {
        console.log('Initializing admin dashboard...');
        
        // Validate admin access
        if (!this.authManager.validateAccess('admin')) {
            this.redirectToLogin();
            return;
        }
        
        this.currentUser = this.authManager.getCurrentUser();
        
        // Initialize dashboard components
        await this.loadDashboardData();
        this.setupDashboardEventListeners();
        this.setupAutoSave();
        
        // Update user interface
        this.updateUserInterface();
    }

    /**
     * Initialize sub-admin dashboard
     */
    async initializeSubDashboard() {
        console.log('Initializing sub-admin dashboard...');
        
        const office = this.authManager.getUrlParameter('office');
        
        // Validate sub-admin access
        if (!this.authManager.validateAccess('sub-admin', office)) {
            this.redirectToLogin();
            return;
        }
        
        this.currentUser = this.authManager.getCurrentUser();
        
        // Verify office access
        if (!this.authManager.hasOfficeAccess(office)) {
            this.showError('Access denied to this office');
            this.redirectToLogin();
            return;
        }
        
        // Initialize sub-dashboard components
        await this.loadSubDashboardData(office);
        this.setupSubDashboardEventListeners();
        this.setupAutoSave();
        
        // Update user interface
        this.updateUserInterface(office);
    }

    /**
     * Set up login form event handlers
     */
    setupLoginFormHandlers() {
        const loginForm = document.getElementById('login-form');
        const roleSelect = document.getElementById('role');
        const officeGroup = document.getElementById('office-group');
        const togglePassword = document.getElementById('toggle-password');
        
        if (!loginForm) return;

        // Role change handler
        if (roleSelect) {
            roleSelect.addEventListener('change', (e) => {
                this.handleRoleChange(e.target.value, officeGroup);
            });
        }

        // Password toggle handler
        if (togglePassword) {
            togglePassword.addEventListener('click', this.handlePasswordToggle.bind(this));
        }

        // Form submission handler
        loginForm.addEventListener('submit', this.handleLoginSubmit.bind(this));

        // Enter key support for better UX
        loginForm.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const submitButton = loginForm.querySelector('button[type="submit"]');
                if (submitButton && !submitButton.disabled) {
                    submitButton.click();
                }
            }
        });
    }

    /**
     * Handle role selection change
     */
    handleRoleChange(selectedRole, officeGroup) {
        if (!officeGroup) return;
        
        const officeSelect = document.getElementById('office');
        
        if (selectedRole === 'sub-admin') {
            // Show office selection with animation
            officeGroup.style.display = 'block';
            if (officeSelect) {
                officeSelect.required = true;
            }
            
            // Smooth animation
            requestAnimationFrame(() => {
                officeGroup.style.opacity = '0';
                officeGroup.style.transform = 'translateY(-10px)';
                officeGroup.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                
                requestAnimationFrame(() => {
                    officeGroup.style.opacity = '1';
                    officeGroup.style.transform = 'translateY(0)';
                });
            });
        } else {
            // Hide office selection
            officeGroup.style.display = 'none';
            if (officeSelect) {
                officeSelect.required = false;
                officeSelect.value = '';
            }
        }
    }

    /**
     * Handle password visibility toggle
     */
    handlePasswordToggle() {
        const passwordInput = document.getElementById('password');
        const passwordIcon = document.getElementById('password-icon');
        
        if (!passwordInput || !passwordIcon) return;
        
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            passwordIcon.classList.remove('fa-eye');
            passwordIcon.classList.add('fa-eye-slash');
        } else {
            passwordInput.type = 'password';
            passwordIcon.classList.remove('fa-eye-slash');
            passwordIcon.classList.add('fa-eye');
        }
    }

    /**
     * Handle login form submission
     */
    async handleLoginSubmit(event) {
        event.preventDefault();
        
        const submitButton = event.target.querySelector('button[type="submit"]');
        const formData = new FormData(event.target);
        
        const loginData = {
            role: formData.get('role'),
            office: formData.get('office'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        // Validate form data
        if (!this.validateLoginForm(loginData)) {
            return;
        }

        // Check login attempts
        if (!this.checkLoginAttempts(loginData.email)) {
            return;
        }

        // Show loading state
        this.showLoadingState(submitButton);

        try {
            // Use direct API call instead of AuthManager for login
            const result = await this.performLogin(loginData);

            if (result.success) {
                this.handleLoginSuccess(result.user, loginData.role, loginData.office);
            } else {
                this.handleLoginFailure(result.message, loginData.email);
            }
        } catch (error) {
            this.handleLoginError(error, loginData.email);
        } finally {
            this.hideLoadingState(submitButton);
        }
    }

    /**
     * Perform login via backend API
     */
    async performLogin(loginData) {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: loginData.email,
                    password: loginData.password,
                    role: loginData.role,
                    office: loginData.office
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Store user session data
                this.authManager.storeUserData(result.user, {
                    userId: result.user.id,
                    email: result.user.email,
                    role: result.user.role,
                    office: result.user.office,
                    loginTime: Date.now(),
                    lastActivity: Date.now(),
                    expiresAt: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
                });
                this.authManager.currentUser = result.user;
            }
            
            return result;
        } catch (error) {
            console.error('Login API error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    /**
     * Validate login form data
     */
    validateLoginForm(data) {
        if (!data.role) {
            this.showError('Please select a role');
            document.getElementById('role')?.focus();
            return false;
        }

        if (data.role === 'sub-admin' && !data.office) {
            this.showError('Please select an office for Sub-Admin role');
            document.getElementById('office')?.focus();
            return false;
        }

        if (!data.email) {
            this.showError('Please enter your email address');
            document.getElementById('email')?.focus();
            return false;
        }

        if (!this.isValidEmail(data.email)) {
            this.showError('Please enter a valid email address');
            document.getElementById('email')?.focus();
            return false;
        }

        if (!data.password) {
            this.showError('Please enter your password');
            document.getElementById('password')?.focus();
            return false;
        }

        return true;
    }

    /**
     * Handle successful login
     */
    handleLoginSuccess(user, role, office) {
        // Reset login attempts
        this.clearLoginAttempts(user.email);
        
        // Show success message
        this.showSuccess('Login successful! Redirecting...');
        
        // Log successful login
        this.authManager.logActivity('login_success', user.id, {
            role: role,
            office: office,
            user_agent: navigator.userAgent
        });
        
        // Redirect after short delay
        setTimeout(() => {
            this.redirectToUserDashboard(user);
        }, 1000);
    }

    /**
     * Handle login failure
     */
    handleLoginFailure(message, email) {
        this.recordLoginAttempt(email);
        this.showError(message || 'Invalid credentials');
        
        // Clear password field
        const passwordField = document.getElementById('password');
        if (passwordField) {
            passwordField.value = '';
            passwordField.focus();
        }
    }

    /**
     * Handle login error
     */
    handleLoginError(error, email) {
        console.error('Login error:', error);
        this.recordLoginAttempt(email);
        this.showError('Login failed. Please try again.');
        
        // Clear password field
        const passwordField = document.getElementById('password');
        if (passwordField) {
            passwordField.value = '';
        }
    }

    /**
     * Redirect user to appropriate dashboard
     */
    redirectToUserDashboard(user) {
        if (user.role === 'admin') {
            window.location.href = '/dashboard';
        } else if (user.role === 'sub-admin') {
            window.location.href = `/Sub-dashboard?office=${user.office}`;
        } else {
            console.error('Unknown user role:', user.role);
            this.showError('Invalid user role');
        }
    }

    /**
     * Redirect to login page
     */
    redirectToLogin() {
        window.location.href = '/';
    }

    /**
     * Set up login attempt tracking
     */
    setupLoginAttemptTracking() {
        this.loginAttempts = JSON.parse(localStorage.getItem('login_attempts') || '{}');
    }

    /**
     * Check if user can attempt login
     */
    checkLoginAttempts(email) {
        const attempts = this.loginAttempts[email];
        
        if (!attempts) return true;
        
        const now = Date.now();
        
        // Check if user is locked out
        if (attempts.count >= this.config.maxLoginAttempts) {
            const lockoutEnd = attempts.lastAttempt + this.config.lockoutDuration;
            
            if (now < lockoutEnd) {
                const remainingTime = Math.ceil((lockoutEnd - now) / 60000); // Minutes
                this.showError(`Too many failed attempts. Try again in ${remainingTime} minutes.`);
                return false;
            } else {
                // Lockout expired, reset attempts
                delete this.loginAttempts[email];
                localStorage.setItem('login_attempts', JSON.stringify(this.loginAttempts));
                return true;
            }
        }
        
        return true;
    }

    /**
     * Record login attempt
     */
    recordLoginAttempt(email) {
        const now = Date.now();
        
        if (!this.loginAttempts[email]) {
            this.loginAttempts[email] = { count: 0, lastAttempt: 0 };
        }
        
        this.loginAttempts[email].count++;
        this.loginAttempts[email].lastAttempt = now;
        
        localStorage.setItem('login_attempts', JSON.stringify(this.loginAttempts));
    }

    /**
     * Clear login attempts for user
     */
    clearLoginAttempts(email) {
        delete this.loginAttempts[email];
        localStorage.setItem('login_attempts', JSON.stringify(this.loginAttempts));
    }

    /**
     * Load dashboard data for admin
     */
    async loadDashboardData() {
        try {
            // Implement dashboard data loading logic here
            console.log('Loading admin dashboard data...');
            
            // Example: Load user statistics, recent activity, etc.
            // const stats = await this.authManager.mongoFind('users', {}, { projection: { role: 1, is_active: 1 } });
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    /**
     * Load sub-dashboard data for specific office
     */
    async loadSubDashboardData(office) {
        try {
            console.log(`Loading sub-dashboard data for office: ${office}`);
            
            // Implement office-specific data loading logic here
            // const officeData = await this.authManager.mongoFind('conversations', { office: office });
            
        } catch (error) {
            console.error('Failed to load sub-dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    /**
     * Set up dashboard event listeners
     */
    setupDashboardEventListeners() {
        // Implement dashboard-specific event listeners
        console.log('Setting up dashboard event listeners...');
        
        // Example: User management, settings, etc.
        this.setupUserManagementEvents();
        this.setupSettingsEvents();
    }

    /**
     * Set up sub-dashboard event listeners
     */
    setupSubDashboardEventListeners() {
        // Implement sub-dashboard-specific event listeners
        console.log('Setting up sub-dashboard event listeners...');
        
        // Example: FAQ management, conversation handling, etc.
        this.setupFAQManagementEvents();
        this.setupConversationEvents();
    }

    /**
     * Set up user management events
     */
    setupUserManagementEvents() {
        // Placeholder for user management event handlers
        // Implement based on your dashboard UI structure
    }

    /**
     * Set up settings events
     */
    setupSettingsEvents() {
        // Placeholder for settings event handlers
        // Implement based on your dashboard UI structure
    }

    /**
     * Set up FAQ management events
     */
    setupFAQManagementEvents() {
        // Placeholder for FAQ management event handlers
        // Implement based on your sub-dashboard UI structure
    }

    /**
     * Set up conversation events
     */
    setupConversationEvents() {
        // Placeholder for conversation event handlers
        // Implement based on your sub-dashboard UI structure
    }

    /**
     * Update user interface with current user info
     */
    updateUserInterface(office = null) {
        if (!this.currentUser) return;
        
        // Update user info displays
        const userNameElements = document.querySelectorAll('[data-user-name]');
        userNameElements.forEach(el => {
            el.textContent = this.currentUser.name || this.currentUser.email;
        });
        
        const userEmailElements = document.querySelectorAll('[data-user-email]');
        userEmailElements.forEach(el => {
            el.textContent = this.currentUser.email;
        });
        
        const userRoleElements = document.querySelectorAll('[data-user-role]');
        userRoleElements.forEach(el => {
            el.textContent = this.formatRole(this.currentUser.role);
        });
        
        if (office) {
            const officeElements = document.querySelectorAll('[data-user-office]');
            officeElements.forEach(el => {
                el.textContent = this.formatOffice(office);
            });
        }
        
        // Set up logout buttons
        this.setupLogoutButtons();
    }

    /**
     * Format role for display
     */
    formatRole(role) {
        const roleMap = {
            'admin': 'Administrator',
            'sub-admin': 'Sub-Administrator'
        };
        return roleMap[role] || role;
    }

    /**
     * Format office for display
     */
    formatOffice(office) {
        const officeMap = {
            'admissions': 'Admissions Office',
            'registrar': 'Registrar Office',
            'guidance': 'Guidance & Counseling',
            'ict': 'ICT Department',
            'osa': 'Office of Student Affairs'
        };
        return officeMap[office] || office;
    }

    /**
     * Set up logout buttons
     */
    setupLogoutButtons() {
        const logoutButtons = document.querySelectorAll('[data-action="logout"]');
        logoutButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleLogout();
            });
        });
    }

    /**
     * Handle logout
     */
    async handleLogout() {
        if (confirm('Are you sure you want to log out?')) {
            try {
                // Call Flask logout endpoint
                const response = await fetch('/logout', {
                    method: 'GET',
                    credentials: 'same-origin'
                });
                
                // Clear client-side data regardless of server response
                this.authManager.clearStoredData();
                this.authManager.currentUser = null;
                
                // Redirect to admin login
                window.location.href = '/admin';
                
            } catch (error) {
                console.error('Logout error:', error);
                // Still clear local data and redirect
                this.authManager.clearStoredData();
                this.authManager.currentUser = null;
                window.location.href = '/admin';
            }
        }
    }

    /**
     * Set up auto-save functionality
     */
    setupAutoSave() {
        // Implement auto-save for form data
        setInterval(() => {
            this.performAutoSave();
        }, this.config.autoSaveInterval);
    }

    /**
     * Perform auto-save
     */
    performAutoSave() {
        // Implement auto-save logic based on current page
        // Save form data, user preferences, etc.
    }

    /**
     * Set up global event listeners
     */
    setupGlobalEventListeners() {
        // Session warning handler
        window.showSessionWarning = this.handleSessionWarning;
        
        // Before unload handler
        window.addEventListener('beforeunload', this.handleBeforeUnload);
        
        // Visibility change handler (for session management)
        document.addEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Online/offline status
        window.addEventListener('online', () => {
            this.showInfo('Connection restored');
        });
        
        window.addEventListener('offline', () => {
            this.showWarning('Connection lost. Some features may not work properly.');
        });
    }

    /**
     * Handle session warning
     */
    handleSessionWarning(minutesRemaining) {
        const message = `Your session will expire in ${minutesRemaining} minutes. Would you like to extend it?`;
        
        if (confirm(message)) {
            const result = this.authManager.extendSession(60); // Extend by 1 hour
            if (result.success) {
                this.showSuccess('Session extended successfully');
            } else {
                this.showError('Failed to extend session');
            }
        }
    }

    /**
     * Handle before unload
     */
    handleBeforeUnload(event) {
        // Check if there are unsaved changes
        if (this.hasUnsavedChanges()) {
            event.preventDefault();
            event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        }
    }

    /**
     * Handle visibility change
     */
    handleVisibilityChange() {
        if (!document.hidden && this.authManager && this.authManager.isAuthenticated()) {
            // Refresh session when user returns to tab
            this.authManager.refreshSession();
        }
    }

    /**
     * Check for unsaved changes
     */
    hasUnsavedChanges() {
        // Implement logic to check for unsaved form data
        const forms = document.querySelectorAll('form[data-auto-save]');
        for (const form of forms) {
            if (form.dataset.modified === 'true') {
                return true;
            }
        }
        return false;
    }

    /**
     * Initialize toast notifications
     */
    initializeToast() {
        // Toast functionality is assumed to be available via external toast.js
        if (typeof window.toast === 'undefined') {
            console.warn('Toast notifications not available');
            
            // Create simple fallback toast system
            window.toast = {
                success: (msg) => this.showAlert(msg, 'success'),
                error: (msg) => this.showAlert(msg, 'error'),
                warning: (msg) => this.showAlert(msg, 'warning'),
                info: (msg) => this.showAlert(msg, 'info')
            };
        }
    }

    /**
     * Simple alert fallback for toast
     */
    showAlert(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        console.log(`[${type.toUpperCase()}] ${message}`);
        
        // You could create a more sophisticated notification system here
        alert(message);
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        if (window.toast) {
            window.toast.success(message);
        } else {
            this.showAlert(message, 'success');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        if (window.toast) {
            window.toast.error(message);
        } else {
            this.showAlert(message, 'error');
        }
    }

    /**
     * Show warning message
     */
    showWarning(message) {
        if (window.toast) {
            window.toast.warning(message);
        } else {
            this.showAlert(message, 'warning');
        }
    }

    /**
     * Show info message
     */
    showInfo(message) {
        if (window.toast) {
            window.toast.info(message);
        } else {
            this.showAlert(message, 'info');
        }
    }

    /**
     * Show loading state on element
     */
    showLoadingState(element) {
        if (!element) return;
        
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        element.classList.add('loading');
    }

    /**
     * Hide loading state from element
     */
    hideLoadingState(element) {
        if (!element) return;
        
        element.disabled = false;
        if (element.dataset.originalText) {
            element.textContent = element.dataset.originalText;
            delete element.dataset.originalText;
        }
        element.classList.remove('loading');
    }

    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Get application status
     */
    getStatus() {
        return {
            initialized: this.isInitialized,
            authenticated: this.authManager ? this.authManager.isAuthenticated() : false,
            currentUser: this.currentUser,
            page: this.getCurrentPage()
        };
    }

    /**
     * Cleanup application resources
     */
    cleanup() {
        // Remove event listeners
        window.removeEventListener('beforeunload', this.handleBeforeUnload);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        // Clear intervals and timeouts
        // (Implementation depends on what intervals you've set up)
        
        console.log('Application cleaned up');
    }
}

// Initialize application when script loads
const app = new EduChatApp();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// Make app globally available for debugging and external integration
window.EduChatApp = app;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EduChatApp;
}