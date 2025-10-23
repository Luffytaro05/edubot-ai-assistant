/**
 * AuthManager - Handles authentication and session management with MongoDB backend
 * AuthManager.js - Simplified for Super Admin Login
 */
class AuthManager {
    constructor() {
        this.sessionKey = 'educhat_session';
        this.tokenKey = 'admin_token';
        this.userKey = 'admin_user';
        this.apiBaseUrl = '/api/auth';
        this.sessionTimeout = 24 * 60 * 60 * 1000; // 24 hours
        this.init();
    }

    /**
     * Initialize authentication system
     */
    init() {
        // Check if session is still valid (but don't refresh on init)
        // Only verify expiration, don't extend it automatically
        this.checkSessionExpiration();
    }

    /**
     * Super Admin login - simplified for admin access
     */
    async login(email, password) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    role: 'admin' // Always admin for Super Admin login
                })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // Store session locally
                const session = {
                    user: result.user,
                    token: result.token,
                    loginTime: new Date().toISOString(),
                    expiresAt: new Date(Date.now() + this.sessionTimeout).toISOString()
                };

                // Store in both formats for backward compatibility
                localStorage.setItem(this.sessionKey, JSON.stringify(session));
                localStorage.setItem(this.tokenKey, result.token);
                localStorage.setItem(this.userKey, JSON.stringify(result.user));
                
                return {
                    success: true,
                    user: result.user,
                    token: result.token
                };
            } else {
                return {
                    success: false,
                    message: result.message || 'Login failed'
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

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = this.getToken();
        const user = this.getCurrentUser();
        
        if (!token || !user) {
            return false;
        }

        // Check if session has expired
        const session = this.getSession();
        if (session && session.expiresAt) {
            const now = new Date();
            const expiresAt = new Date(session.expiresAt);
            
            if (now > expiresAt) {
                this.logout();
                return false;
            }
        }

        return true;
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        try {
            const userData = localStorage.getItem(this.userKey);
            return userData ? JSON.parse(userData) : null;
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    }

    /**
     * Get current user role
     */
    getUserRole() {
        const user = this.getCurrentUser();
        return user ? user.role : null;
    }

    /**
     * Get current session token
     */
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    /**
     * Check authentication and require admin role
     */
    checkAuth() {
        if (!this.isAuthenticated()) {
            return false;
        }

        const user = this.getCurrentUser();
        if (!user || user.role !== 'admin') {
            this.logout();
            return false;
        }

        return true;
    }

    /**
     * Verify token with backend
     */
    async verifyToken() {
        try {
            const token = this.getToken();
            if (!token) return false;

            const response = await fetch(`${this.apiBaseUrl}/verify`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const result = await response.json();
                return result.valid;
            }
            return false;
        } catch (error) {
            console.error('Token verification error:', error);
            return false;
        }
    }

    /**
     * Require authentication - redirect if not authenticated
     */
    requireAuth() {
        if (!this.checkAuth()) {
            window.location.href = "/";
            return false;
        }
        return true;
    }

    /**
     * Logout current user
     */
    async logout() {
        try {
            const token = this.getToken();
            if (token) {
                // Notify backend about logout
                await fetch(`${this.apiBaseUrl}/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Always clear local session
            localStorage.removeItem(this.sessionKey);
            localStorage.removeItem(this.tokenKey);
            localStorage.removeItem(this.userKey);
        }
        
        return { success: true };
    }

    /**
     * Check if session has expired (without refreshing it)
     */
    checkSessionExpiration() {
        const session = this.getSession();
        if (session && session.expiresAt) {
            const now = new Date();
            const expiresAt = new Date(session.expiresAt);
            
            if (now > expiresAt) {
                console.log('Session has expired after 24 hours');
                this.logout();
            }
        }
    }

    /**
     * Refresh session timeout (only call this on explicit user actions, not on page load)
     * This method should NOT be called automatically - session should expire after 24 hours
     */
    refreshSession() {
        const session = this.getSession();
        if (session) {
            session.expiresAt = new Date(Date.now() + this.sessionTimeout).toISOString();
            localStorage.setItem(this.sessionKey, JSON.stringify(session));
        }
    }

    /**
     * Get current session
     */
    getSession() {
        try {
            const sessionData = localStorage.getItem(this.sessionKey);
            return sessionData ? JSON.parse(sessionData) : null;
        } catch (error) {
            console.error('Error getting session:', error);
            return null;
        }
    }

    /**
     * Change password
     */
    async changePassword(currentPassword, newPassword) {
        try {
            const token = this.getToken();
            if (!token) {
                return { success: false, message: 'Not authenticated' };
            }

            const response = await fetch(`${this.apiBaseUrl}/change-password`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    currentPassword: currentPassword,
                    newPassword: newPassword
                })
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Password change error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    /**
     * Update user profile
     */
    async updateProfile(profileData) {
        try {
            const token = this.getToken();
            if (!token) {
                return { success: false, message: 'Not authenticated' };
            }

            const response = await fetch(`${this.apiBaseUrl}/profile`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(profileData)
            });

            const result = await response.json();
            
            // Update local session with new user data
            if (result.success && result.user) {
                localStorage.setItem(this.userKey, JSON.stringify(result.user));
                
                const session = this.getSession();
                if (session) {
                    session.user = { ...session.user, ...result.user };
                    localStorage.setItem(this.sessionKey, JSON.stringify(session));
                }
            }

            return result;
        } catch (error) {
            console.error('Profile update error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    /**
     * Make authenticated API request helper
     */
    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            throw new Error('Not authenticated');
        }

        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            // Handle token expiration
            if (response.status === 401) {
                this.logout();
                window.location.href = "/";
                return null;
            }

            return response;
        } catch (error) {
            console.error('Authenticated request error:', error);
            throw error;
        }
    }

    /**
     * Get session info for debugging
     */
    getSessionInfo() {
        const session = this.getSession();
        if (!session) return null;

        const now = new Date();
        const expiresAt = new Date(session.expiresAt);
        const timeLeft = expiresAt - now;

        return {
            user: session.user,
            loginTime: session.loginTime,
            expiresAt: session.expiresAt,
            timeLeft: timeLeft,
            isExpired: timeLeft <= 0
        };
    }
}

// Make AuthManager globally available
window.AuthManager = AuthManager;