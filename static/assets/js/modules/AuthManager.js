/**
 * AuthManager - Handles authentication and session management with MongoDB backend
 */
class AuthManager {
    constructor() {
        this.sessionKey = 'educhat_session';
        this.apiBaseUrl = '/api/auth'; // Backend API endpoint
        this.sessionTimeout = 24 * 60 * 60 * 1000; // 24 hours
        this.init();
    }

    /**
     * Initialize authentication system
     */
    init() {
        // Check if session is still valid
        this.refreshSession();
    }

    /**
     * Login with email, password, role, and office
     */
    async login(email, password, role, office = null) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    role: role,
                    office: office
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

                localStorage.setItem(this.sessionKey, JSON.stringify(session));
                
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
     * Register a new user
     */
    async register(userData) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Registration error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    /**
     * Logout current user
     */
    async logout() {
        try {
            const session = this.getSession();
            if (session && session.token) {
                // Notify backend about logout
                await fetch(`${this.apiBaseUrl}/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${session.token}`,
                        'Content-Type': 'application/json',
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Always clear local session
            localStorage.removeItem(this.sessionKey);
        }
        
        return { success: true };
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        const session = this.getSession();
        return session ? session.user : null;
    }

    /**
     * Get current session token
     */
    getToken() {
        const session = this.getSession();
        return session ? session.token : null;
    }

    /**
     * Check if user is authenticated
     */
    checkAuth() {
        const session = this.getSession();
        if (!session) return false;

        // Check if session has expired
        const now = new Date();
        const expiresAt = new Date(session.expiresAt);
        
        if (now > expiresAt) {
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
     * Refresh session timeout
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
     * Get session info
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
     * Get all users (admin only)
     */
    async getAllUsers() {
        try {
            const token = this.getToken();
            if (!token) {
                return { success: false, message: 'Not authenticated' };
            }

            const response = await fetch(`${this.apiBaseUrl}/users`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Get users error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    /**
     * Delete user (admin only)
     */
    async deleteUser(userId) {
        try {
            const token = this.getToken();
            if (!token) {
                return { success: false, message: 'Not authenticated' };
            }

            const response = await fetch(`${this.apiBaseUrl}/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Delete user error:', error);
            return {
                success: false,
                message: 'Network error. Please try again.'
            };
        }
    }

    /**
     * Reset password (admin only)
     */
    async resetUserPassword(userId, newPassword) {
        try {
            const token = this.getToken();
            if (!token) {
                return { success: false, message: 'Not authenticated' };
            }

            const response = await fetch(`${this.apiBaseUrl}/reset-password`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    userId: userId,
                    newPassword: newPassword
                })
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Reset password error:', error);
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
}