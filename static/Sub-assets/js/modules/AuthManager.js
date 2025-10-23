/**
 * AuthManager.js
 * Sub Admin authentication manager for EduChat Portal with Office Access Control.
 * Uses Flask session + MongoDB (no localStorage).
 */

class AuthManager {
    constructor() {
        this.baseUrl = "/subadmin"; // Flask backend routes
        this.allowedOffices = [
            "Registrar's Office",
            "Admission Office", 
            "ICT Office",
            "Office of Student Affairs",
            "Guidance Office"
        ];
    }

    /**
     * Sub Admin Login
     */
    async loginSubAdmin(office, email, password) {
        try {
            const response = await fetch(`${this.baseUrl}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include", // ✅ keep Flask session cookies
                body: JSON.stringify({ office, email, password }),
            });

            let data = {};
            try {
                data = await response.json();
            } catch {
                data = {};
            }

            if (response.ok && data.success) {
                return { 
                    success: true, 
                    office: data.office,
                    name: data.name  // ✅ Include name in response
                };
            } else if (response.status === 401) {
                return { success: false, message: data.message || "Invalid credentials" };
            } else {
                return { success: false, message: data.message || "Login failed" };
            }
        } catch (error) {
            console.error("Login error:", error);
            return { success: false, message: "Server error. Try again later." };
        }
    }

    /**
     * Check if Sub Admin is authenticated
     */
    async isSubAdminAuthenticated() {
        try {
            const response = await fetch(`${this.baseUrl}/session`, {
                method: "GET",
                credentials: "include", // ✅ send session cookie
            });

            let data = {};
            try {
                data = await response.json();
            } catch {
                data = {};
            }

            return {
                authenticated: data.authenticated === true,
                role: data.role || null,
                office: data.office || null,
                name: data.name || null,  // ✅ Include name in session data
            };
        } catch (err) {
            console.error("Session check failed:", err);
            return { authenticated: false, role: null, office: null, name: null };
        }
    }

    /**
     * Get current Sub Admin user data
     */
    async getCurrentUser() {
        try {
            const response = await fetch(`${this.baseUrl}/session`, {
                method: "GET",
                credentials: "include",
            });

            let data = {};
            try {
                data = await response.json();
            } catch {
                data = {};
            }

            if (data.authenticated) {
                return {
                    email: data.email,
                    role: data.role,
                    office: data.office,
                    name: data.name,  // ✅ Include name
                };
            }
            return null;
        } catch (err) {
            console.error("Get current user failed:", err);
            return null;
        }
    }

    /**
     * Validate office access - check if user can access specific office pages
     */
    async validateOfficeAccess(requestedOffice = null) {
        try {
            const status = await this.isSubAdminAuthenticated();
            
            if (!status.authenticated || status.role !== "sub-admin") {
                return { valid: false, reason: "not_authenticated" };
            }

            const userOffice = status.office;
            
            // If no specific office requested, just check if user is authenticated
            if (!requestedOffice) {
                return { valid: true, userOffice: userOffice };
            }

            // Check if requested office matches user's office
            if (requestedOffice !== userOffice) {
                return { 
                    valid: false, 
                    reason: "office_mismatch", 
                    userOffice: userOffice, 
                    requestedOffice: requestedOffice 
                };
            }

            return { valid: true, userOffice: userOffice };
            
        } catch (err) {
            console.error("Office access validation failed:", err);
            return { valid: false, reason: "validation_error" };
        }
    }

    /**
     * Require Sub Admin authentication and office validation
     */
    async requireSubAdminAuth(expectedOffice = null) {
        try {
            const validation = await this.validateOfficeAccess(expectedOffice);
            
            if (!validation.valid) {
                console.log("Sub Admin authentication/office validation failed:", validation.reason);
                
                if (validation.reason === "office_mismatch") {
                    // Redirect to correct office dashboard
                    window.location.href = `/Sub-dashboard?office=${encodeURIComponent(validation.userOffice)}`;
                } else {
                    // Redirect to login
                    window.location.href = "/sub-index";
                }
                return false;
            }
            
            return true;
            
        } catch (err) {
            console.error("Auth check failed:", err);
            window.location.href = "/sub-index";
            return false;
        }
    }

    /**
     * Get office from current URL parameters
     */
    getOfficeFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('office');
    }

    /**
     * Redirect to Sub Admin Dashboard (or login page if not authenticated)
     */
    async redirectSubAdminToDashboard() {
        try {
            const status = await this.isSubAdminAuthenticated();
            if (status.authenticated && status.role === "sub-admin") {
                const office = status.office || "";
                window.location.href = `/Sub-dashboard?office=${encodeURIComponent(office)}`;
            } else {
                window.location.href = "/sub-index";
            }
        } catch (err) {
            console.error("Redirect failed:", err);
            window.location.href = "/sub-index";
        }
    }

    /**
     * Navigate to office-specific page with validation
     */
    async navigateToOfficePage(page, office = null) {
        try {
            const status = await this.isSubAdminAuthenticated();
            
            if (!status.authenticated || status.role !== "sub-admin") {
                window.location.href = "/sub-index";
                return false;
            }

            const userOffice = status.office;
            const targetOffice = office || userOffice;

            // Validate office access
            if (targetOffice !== userOffice) {
                console.warn(`Access denied: User from ${userOffice} trying to access ${targetOffice} page`);
                // Redirect to their own office's version of the page
                window.location.href = `/${page}?office=${encodeURIComponent(userOffice)}`;
                return false;
            }

            // Navigate to the requested page
            window.location.href = `/${page}?office=${encodeURIComponent(targetOffice)}`;
            return true;
            
        } catch (err) {
            console.error("Navigation failed:", err);
            window.location.href = "/sub-index";
            return false;
        }
    }

    /**
     * Logout Sub Admin with confirmation
     */
    async logoutSubAdmin() {
        try {
            // Show confirmation dialog
            const confirmed = confirm('Are you sure you want to logout?');
            
            if (confirmed) {
                await fetch(`${this.baseUrl}/logout`, {
                    method: "POST",
                    credentials: "include",
                });
                window.location.href = "/sub-index";
            }
            // If not confirmed, do nothing (user stays logged in)
        } catch (err) {
            console.error("Logout error:", err);
            // Even if logout request fails, redirect to login page
            window.location.href = "/sub-index";
        }
    }

    /**
     * Update UI elements with user info and enforce office-specific display
     */
    updateUserInfo(office, name) {
        // Update document title
        this.updatePageTitle(office);

        // Update office name in sidebar and headers
        const officeElements = document.querySelectorAll('.sidebar-title, .office-name');
        officeElements.forEach(element => {
            if (element.querySelector('i')) {
                // Preserve the icon
                const icon = element.querySelector('i').outerHTML;
                element.innerHTML = `${icon} ${office}`;
            } else {
                element.textContent = office;
            }
        });

        // Update user name in user profile sections
        const nameElements = document.querySelectorAll('.user-name');
        nameElements.forEach(element => {
            element.textContent = name;
        });

        // Update user role with office info
        const roleElements = document.querySelectorAll('.user-role');
        roleElements.forEach(element => {
            element.textContent = `${office} - Sub Admin`;
        });

        // Update page subtitle with office info
        const pageSubtitles = document.querySelectorAll('.page-subtitle');
        pageSubtitles.forEach(element => {
            const currentText = element.textContent;
            if (currentText.includes('Overview of') && currentText.includes('performance and metrics')) {
                element.textContent = `Overview of ${office} performance and metrics`;
            }
        });

        // Update chart titles with office info
        const chartTitles = document.querySelectorAll('.chart-title');
        chartTitles.forEach(element => {
            if (element.textContent.includes('Weekly Chatbot Usage')) {
                element.textContent = `Weekly Chatbot Usage - ${office}`;
            }
        });
    }

    /**
     * Update page title based on current page and office
     */
    updatePageTitle(office) {
        const currentPath = window.location.pathname;
        let pageTitle = '';

        switch(currentPath) {
            case '/Sub-dashboard':
                pageTitle = `Sub-Dashboard - ${office}`;
                break;
            case '/Sub-conversations':
                pageTitle = `Conversations - ${office}`;
                break;
            case '/Sub-faq':
                pageTitle = `FAQ Management - ${office}`;
                break;
            case '/Sub-announcements':
                pageTitle = `Announcements - ${office}`;
                break;
            case '/Sub-usage_stats':
                pageTitle = `Usage Statistics - ${office}`;
                break;
            case '/Sub-feedback':
                pageTitle = `User Feedback - ${office}`;
                break;
            default:
                pageTitle = `${office} - Sub Admin`;
        }

        document.title = pageTitle;
    }

    /**
     * Initialize office-specific navigation restrictions
     */
    initializeOfficeNavigation() {
        // Add click handlers to navigation links to enforce office access
        document.querySelectorAll('.nav-item[href*="Sub-"]').forEach(link => {
            link.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const href = link.getAttribute('href');
                const urlParts = href.split('?')[0]; // Get path without query params
                const pageName = urlParts.split('/').pop(); // Get the page name
                
                // Navigate with office validation
                await this.navigateToOfficePage(pageName);
            });
        });
    }

    /**
     * Get office-specific data from server
     */
    async getOfficeData() {
        try {
            const response = await fetch('/api/sub-admin/office-data', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    return result.data;
                }
            }
            
            console.error('Failed to load office data:', response.status);
            return null;
            
        } catch (error) {
            console.error('Error loading office data:', error);
            return null;
        }
    }
}

// Make AuthManager globally accessible
window.authManager = new AuthManager();