class AuthManager {
    constructor() {
        this.storageManager = window.storageManager;
        this.currentUser = null;
        this.checkAuthStatus();
    }

    // Check if user is already logged in
    checkAuthStatus() {
        this.currentUser = this.storageManager.getCurrentUser();
        return this.currentUser !== null;
    }

    // Login method
    login(email, password) {
        const users = this.storageManager.getUsers();
        const user = users.find(u => u.email === email && u.password === password);
        
        if (user) {
            // Remove password from user object before storing
            const { password, ...userWithoutPassword } = user;
            this.currentUser = userWithoutPassword;
            this.storageManager.setCurrentUser(userWithoutPassword);
            return { success: true, user: userWithoutPassword };
        } else {
            return { success: false, message: 'Invalid credentials' };
        }
    }

    // Logout method
    logout() {
        this.currentUser = null;
        this.storageManager.clearCurrentUser();
        return { success: true };
    }

    // Get current user
    getCurrentUser() {
        return this.currentUser;
    }

    // Check if user is authenticated
    isAuthenticated() {
        return this.currentUser !== null;
    }

    // Validate login form
    validateLoginForm(email, password) {
        const errors = [];

        if (!email || email.trim() === '') {
            errors.push('Email is required');
        } else if (!this.isValidEmail(email)) {
            errors.push('Please enter a valid email address');
        }

        if (!password || password.trim() === '') {
            errors.push('Password is required');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    // Email validation helper
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Redirect to dashboard if authenticated
   // Redirect to dashboard if authenticated
redirectIfAuthenticated() {
    if (this.isAuthenticated()) {
        const role = this.getUserRole();
        const office = this.getUserOffice();

        // Admins go to main dashboard
        if (role === 'admin') {
            window.location.href = 'pages/dashboard.html';
        }
        // Sub-admins go to their office-specific dashboard
        else if (role === 'sub-admin' && office) {
            const officePage = `pages/${office.toLowerCase()}_dashboard.html`;
            window.location.href = officePage;
        }
        // Default fallback
        else {
            window.location.href = 'pages/dashboard.html';
        }
    }
}


    // Require authentication for protected pages
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '../index.html';
            return false;
        }
        return true;
    }

    // Update user profile
    updateProfile(updates) {
        if (!this.currentUser) return false;

        const users = this.storageManager.getUsers();
        const userIndex = users.findIndex(u => u.id === this.currentUser.id);
        
        if (userIndex !== -1) {
            users[userIndex] = { ...users[userIndex], ...updates };
            this.storageManager.setUsers(users);
            
            // Update current user
            this.currentUser = { ...this.currentUser, ...updates };
            this.storageManager.setCurrentUser(this.currentUser);
            
            return true;
        }
        
        return false;
    }

    // Change password
    changePassword(currentPassword, newPassword) {
        if (!this.currentUser) return { success: false, message: 'No user logged in' };

        const users = this.storageManager.getUsers();
        const userIndex = users.findIndex(u => u.id === this.currentUser.id);
        
        if (userIndex === -1) {
            return { success: false, message: 'User not found' };
        }

        if (users[userIndex].password !== currentPassword) {
            return { success: false, message: 'Current password is incorrect' };
        }

        users[userIndex].password = newPassword;
        this.storageManager.setUsers(users);
        
        return { success: true, message: 'Password updated successfully' };
    }

    // Get user permissions (for future use)
    getUserPermissions() {
        if (!this.currentUser) return [];
        
        // Default permissions for Sub Admin
        return [
            'view_dashboard',
            'manage_faqs',
            'manage_announcements',
            'view_conversations',
            'view_feedback',
            'view_usage_stats',
            'export_data'
        ];
    }

    // Check if user has specific permission
    hasPermission(permission) {
        const permissions = this.getUserPermissions();
        return permissions.includes(permission);
    }

    // Get user role
    getUserRole() {
        return this.currentUser ? this.currentUser.role : null;
    }

    // Get user office
    getUserOffice() {
        return this.currentUser ? this.currentUser.office : null;
    }
}

// Initialize global auth manager
window.authManager = new AuthManager();
