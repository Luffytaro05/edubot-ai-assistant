/**
 * UserManager.js - Enhanced with Session Management
 * Handles frontend user management and session persistence
 */
class UserManager {
    constructor() {
        this.baseUrl = "/api/users";
        this.currentUser = null;
        this.sessionChecked = false;
        this.initializeSession();
    }

    // ===========================
    // SESSION MANAGEMENT
    // ===========================

    async initializeSession() {
        try {
            // First check localStorage for existing session
            const storedSession = localStorage.getItem('educhat_session');
            if (storedSession) {
                try {
                    const session = JSON.parse(storedSession);
                    if (session.user && session.expiresAt) {
                        const expiresAt = new Date(session.expiresAt);
                        if (expiresAt > new Date()) {
                            this.currentUser = session.user;
                            console.log('Session restored from localStorage:', session.user);
                            
                            // If we're on login page and user is authenticated, redirect
                            if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
                                this.redirectToDashboard(session.user);
                            }
                            
                            this.sessionChecked = true;
                            return;
                        } else {
                            console.log('Stored session expired, clearing...');
                            localStorage.removeItem('educhat_session');
                        }
                    }
                } catch (error) {
                    console.error('Error parsing stored session:', error);
                    localStorage.removeItem('educhat_session');
                }
            }
            
            // Check server-side session status
            const response = await fetch('/api/auth/session-status', {
                credentials: 'include' // Important for session cookies
            });
            
            // Only parse as JSON if response is OK and content-type is JSON
            let data = { authenticated: false };
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    data = await response.json();
                } else {
                    console.warn('Session status endpoint returned non-JSON response');
                }
            } else {
                console.warn(`Session status endpoint not available (${response.status})`);
            }
            
            if (data.authenticated && data.user) {
                this.currentUser = data.user;
                console.log('Server session restored:', data.user);
                
                // Save server session to localStorage for consistency
                const session = {
                    user: data.user,
                    token: 'server-session',
                    loginTime: new Date().toISOString(),
                    expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() // 24 hours
                };
                localStorage.setItem('educhat_session', JSON.stringify(session));
                
                // If we're on login page and user is authenticated, redirect
                if (window.location.pathname === '/' || window.location.pathname === '/index.html') {
                    this.redirectToDashboard(data.user);
                }
            } else {
                this.currentUser = null;
                
                // If on protected page without session, redirect to login
                if (this.isProtectedPage()) {
                    this.redirectToLogin();
                }
            }
            
            this.sessionChecked = true;
        } catch (error) {
            console.error('Session initialization error:', error);
            this.sessionChecked = true;
            
            if (this.isProtectedPage()) {
                this.redirectToLogin();
            }
        }
    }

    isProtectedPage() {
        const protectedPaths = [
            '/Sub-dashboard',
            '/Sub-dashboard.html',
            '/Sub-conversations',
            '/Sub-conversations.html',
            '/Sub-faq',
            '/Sub-faq.html',
            '/Sub-announcements',
            '/Sub-announcements.html',
            '/Sub-usage',
            '/Sub-usage.html',
            '/Sub-feedback',
            '/Sub-feedback.html',
            '/dashboard.html',
            '/users.html',
            '/conversations.html'
        ];
        
        return protectedPaths.some(path => window.location.pathname.includes(path));
    }

    redirectToDashboard(user) {
        const role = user.role.toLowerCase().replace(/[_\s]/g, '-');
        
        if (role.includes('sub-admin') || role.includes('subadmin')) {
            const office = encodeURIComponent(user.office || 'General');
            window.location.href = `/Sub-dashboard.html?office=${office}`;
        } else if (role.includes('admin')) {
            window.location.href = '/dashboard.html';
        } else {
            window.location.href = '/';
        }
    }

    redirectToLogin() {
        if (window.location.pathname !== '/' && window.location.pathname !== '/index.html') {
            window.location.href = '/';
        }
    }

    async waitForSessionCheck() {
        while (!this.sessionChecked) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        return this.isAuthenticated();
    }

    isAuthenticated() {
        return this.currentUser !== null;
    }

    getCurrentUser() {
        return this.currentUser;
    }

    hasRole(role) {
        if (!this.currentUser) return false;
        const userRole = this.currentUser.role.toLowerCase().replace(/[_\s]/g, '-');
        const checkRole = role.toLowerCase().replace(/[_\s]/g, '-');
        return userRole.includes(checkRole);
    }

    isSubAdmin() {
        return this.hasRole('sub-admin') || this.hasRole('subadmin');
    }

    isAdmin() {
        return this.hasRole('admin') && !this.isSubAdmin();
    }

    getUserOffice() {
        return this.currentUser?.office || 'General';
    }

    // ===========================
    // AUTHENTICATION METHODS
    // ===========================

    async login(email, password, role, office = null) {
        try {
            console.log('Login attempt:', { email, role, office });

            const loginData = {
                email: email.trim(),
                password: password,
                role: role
            };

            if (role.toLowerCase().includes('sub') && office) {
                loginData.office = office;
            }

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginData)
            });

            const result = await response.json();
            console.log('Login response:', result);

            if (result.success) {
                // Store user data
                this.currentUser = result.user;
                
                // Store session data in localStorage as backup
                const sessionData = {
                    user: result.user,
                    role: result.role,
                    office: result.office,
                    loginTime: result.loginTime,
                    token: result.token
                };
                localStorage.setItem('educhat_session', JSON.stringify(sessionData));
                localStorage.setItem('auth_token', result.token);

                console.log('Login successful, redirecting to:', result.redirect);
                
                return {
                    success: true,
                    user: result.user,
                    redirect: result.redirect,
                    message: result.message
                };
            } else {
                return {
                    success: false,
                    message: result.message
                };
            }

        } catch (error) {
            console.error('Login error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    async logout() {
        try {
            console.log('Logging out...');
            
            // Call server logout endpoint
            const response = await fetch('/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            // Clear client-side data regardless of server response
            this.currentUser = null;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('educhat_session');

            console.log('Logout successful, redirecting to login');
            window.location.href = '/';

            return {
                success: true,
                message: 'Logged out successfully'
            };

        } catch (error) {
            console.error('Logout error:', error);
            
            // Clear client data even if server call fails
            this.currentUser = null;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('educhat_session');
            window.location.href = '/';

            return {
                success: false,
                message: 'Logout completed with errors'
            };
        }
    }

    // Session monitoring
    startSessionMonitoring(intervalMinutes = 30) {
        setInterval(async () => {
            try {
                const response = await fetch('/api/auth/session-status');
                const data = await response.json();

                if (!data.authenticated) {
                    console.log('Session expired, logging out');
                    await this.logout();
                }
            } catch (error) {
                console.error('Session validation error:', error);
            }
        }, intervalMinutes * 60 * 1000);
    }

    // Get auth headers for API calls
    getAuthHeaders() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            return {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    }

    // Make authenticated API call
    async apiCall(url, options = {}) {
        const headers = {
            ...this.getAuthHeaders(),
            ...options.headers
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        // Check if token expired
        if (response.status === 401) {
            await this.logout();
            throw new Error('Session expired');
        }

        return response;
    }

    // ===========================
    // USER MANAGEMENT METHODS
    // ===========================

    async getAll() {
        try {
            const res = await this.apiCall(this.baseUrl);
            return await res.json();
        } catch (err) {
            console.error("Error fetching users:", err);
            return [];
        }
    }

    async addUser(userData) {
        try {
            const res = await this.apiCall(this.baseUrl, {
                method: "POST",
                body: JSON.stringify(userData)
            });
            return await res.json();
        } catch (err) {
            console.error("Error adding user:", err);
            return { success: false, message: "Error adding user" };
        }
    }

    async createSubAdmin(name, email, password, office) {
        const userData = {
            name: name,
            email: email,
            password: password,
            role: "Sub-Admin",
            office: office,
            status: "Active"
        };
        
        try {
            const result = await this.addUser(userData);
            if (result.success) {
                console.log(`Sub-Admin created successfully: ${name} (${email})`);
            }
            return result;
        } catch (err) {
            console.error("Error creating Sub-Admin:", err);
            return { success: false, message: "Error creating Sub-Admin" };
        }
    }

    async getById(userId) {
        try {
            const res = await this.apiCall(`${this.baseUrl}/${userId}`);
            return await res.json();
        } catch (err) {
            console.error("Error fetching user:", err);
            return null;
        }
    }

    async updateUser(userId, updates) {
        try {
            const res = await this.apiCall(`${this.baseUrl}/${userId}`, {
                method: "PUT",
                body: JSON.stringify(updates)
            });
            return await res.json();
        } catch (err) {
            console.error("Error updating user:", err);
            return { success: false, message: "Error updating user" };
        }
    }

    async toggleStatus(userId) {
        try {
            const res = await this.apiCall(`${this.baseUrl}/${userId}/toggle`, {
                method: "PATCH"
            });
            return await res.json();
        } catch (err) {
            console.error("Error toggling user status:", err);
            return { success: false, message: "Error toggling user status" };
        }
    }

    async delete(userId) {
        try {
            const res = await this.apiCall(`${this.baseUrl}/${userId}`, {
                method: "DELETE"
            });
            return await res.json();
        } catch (err) {
            console.error("Error deleting user:", err);
            return { success: false, message: "Error deleting user" };
        }
    }

    searchUsers(query) {
        query = query.toLowerCase();
        return currentUsers.filter(user =>
            user.name.toLowerCase().includes(query) ||
            user.email.toLowerCase().includes(query) ||
            (user.role && user.role.toLowerCase().includes(query)) ||
            (user.office && user.office.toLowerCase().includes(query))
        );
    }

    // Legacy method for backward compatibility
    async subAdminLogin(email, password) {
        try {
            const response = await fetch('/api/users/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email.trim(),
                    password: password
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.currentUser = result.user;
                const sessionData = {
                    user: result.user,
                    role: result.role,
                    office: result.office,
                    loginTime: new Date().toISOString()
                };
                
                localStorage.setItem('educhat_session', JSON.stringify(sessionData));
                
                return {
                    success: true,
                    user: result.user,
                    redirect: result.redirect,
                    message: result.message
                };
            } else {
                return {
                    success: false,
                    message: result.message
                };
            }

        } catch (error) {
            console.error('Sub-admin login error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }
}

// ===========================
// UTILITY FUNCTIONS
// ===========================

async function loadUsers() {
    try {
        const response = await window.userManager.apiCall("/api/users");
        const users = await response.json();

        const tableBody = document.getElementById("users-table-body");
        if (!tableBody) return;

        tableBody.innerHTML = "";

        users.forEach(user => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>
                    <div><strong>${user.name || "N/A"}</strong></div>
                    <div style="font-size: 0.85em; color: gray;">${user.email || "N/A"}</div>
                </td>
                <td>${user.role || "User"} / ${user.office || "-"}</td>
                <td>${user.status || "Active"}</td>
                <td>${user.last_login || "Never"}</td>
                <td>
                    <button onclick="editUser('${user.id}')">Edit</button>
                    <button onclick="deleteUser('${user.id}')">Delete</button>
                </td>
            `;
            tableBody.appendChild(row);
        });

    } catch (err) {
        console.error("Error loading users:", err);
    }
}

function editUser(userId) {
    console.log("Edit user:", userId);
    // TODO: open modal or form for editing
}

async function deleteUser(userId) {
    if (!confirm("Are you sure you want to delete this user?")) return;
    const result = await window.userManager.delete(userId);
    if (result.success) {
        showMessage("User deleted successfully!", 'success');
        loadUsers();
    } else {
        showMessage("Error deleting user", 'error');
    }
}

// ===========================
// FORM HANDLERS
// ===========================

function setupLoginForm() {
    const loginForm = document.querySelector('#loginForm, .login-form, [data-form="login"]');
    if (!loginForm) {
        console.log('Login form not found');
        return;
    }

    console.log('Setting up login form...');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const email = loginForm.querySelector('#email, [name="email"], input[type="email"]').value.trim();
        const password = loginForm.querySelector('#password, [name="password"], input[type="password"]').value;
        const role = loginForm.querySelector('#role, [name="role"], select').value;
        const officeElement = loginForm.querySelector('#office, [name="office"], select[data-field="office"]');
        const office = officeElement ? officeElement.value : null;

        console.log('Login form submission:', { email, role, office });

        if (!email || !password || !role) {
            showMessage('Please fill in all required fields.', 'error');
            return;
        }

        if (role.toLowerCase().includes('sub') && !office) {
            showMessage('Please select an office for Sub-Admin login.', 'error');
            return;
        }

        const submitBtn = loginForm.querySelector('button[type="submit"], .login-btn, [data-action="login"]');
        const originalText = submitBtn ? submitBtn.textContent : '';
        
        if (submitBtn) {
            submitBtn.textContent = 'Logging in...';
            submitBtn.disabled = true;
        }

        try {
            const result = await window.userManager.login(email, password, role, office);
            
            if (result.success) {
                showMessage('Login successful! Redirecting...', 'success');
                
                setTimeout(() => {
                    if (result.redirect) {
                        console.log('Redirecting to:', result.redirect);
                        window.location.href = result.redirect;
                    } else {
                        window.location.href = '/dashboard.html';
                    }
                }, 1000);
                
            } else {
                showMessage(result.message || 'Login failed. Please check your credentials.', 'error');
            }
            
        } catch (error) {
            console.error('Login error:', error);
            showMessage('An error occurred during login. Please try again.', 'error');
        } finally {
            if (submitBtn) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        }
    });
}

// ===========================
// UTILITY FUNCTIONS
// ===========================

function showMessage(message, type = 'info') {
    // Try existing toast systems
    if (typeof showToast === 'function') {
        showToast(message, type);
        return;
    }
    
    if (window.uiManager && typeof window.uiManager.showToast === 'function') {
        window.uiManager.showToast(message, type);
        return;
    }

    // Try Bootstrap toast
    const toastElement = document.getElementById('toast');
    if (toastElement) {
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');
        
        if (toastTitle) toastTitle.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        if (toastMessage) toastMessage.textContent = message;
        
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        return;
    }
    
    // Fallback to alert
    alert(message);
}

function requireAuth(requiredRole = null) {
    const sessionData = window.userManager.getCurrentUser();
    
    if (!sessionData) {
        console.log('No authentication found, redirecting to login...');
        window.location.href = '/';
        return false;
    }
    
    if (requiredRole) {
        const userRole = sessionData.role.toLowerCase();
        const required = requiredRole.toLowerCase();
        
        if (required === 'admin' && !userRole.includes('admin')) {
            showMessage('Access denied. Admin privileges required.', 'error');
            setTimeout(() => window.location.href = '/', 2000);
            return false;
        }
        
        if (required === 'sub-admin' && !userRole.includes('sub')) {
            showMessage('Access denied. Sub-Admin privileges required.', 'error');
            setTimeout(() => window.location.href = '/', 2000);
            return false;
        }
    }
    
    return sessionData;
}

// ===========================
// INITIALIZATION
// ===========================

// Create global instance
window.userManager = new UserManager();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async function() {
    console.log('UserManager initializing...');
    
    // Wait for session check
    await window.userManager.waitForSessionCheck();
    
    // Set up login form
    setupLoginForm();
    
    // Load users table if on users page
    if (document.getElementById('users-table-body')) {
        loadUsers();
    }
    
    // Set up logout handlers
    document.querySelectorAll('[data-logout], [data-action="logout"], .logout-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            if (confirm('Are you sure you want to logout?')) {
                await window.userManager.logout();
            }
        });
    });
    
    console.log('UserManager initialization complete');
});

// Export for global access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UserManager;
}