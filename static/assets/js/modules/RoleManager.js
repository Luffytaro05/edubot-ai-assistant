class RoleManager {
    constructor() {
        this.baseUrl = "/api/roles";
    }

    /**
     * Get all sub-admins with their permissions
     */
    async getAllSubAdmins() {
        try {
            const response = await fetch(`${this.baseUrl}/sub-admins`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching sub-admins:', error);
            return {
                success: false,
                message: error.message,
                subAdmins: []
            };
        }
    }

    /**
     * Update permissions for a specific sub-admin
     */
    async updateSubAdminPermissions(subAdminId, permissions) {
        try {
            const response = await fetch(`${this.baseUrl}/sub-admins/${subAdminId}/permissions`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ permissions })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error updating sub-admin permissions:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Get permissions for a specific sub-admin
     */
    async getSubAdminPermissions(subAdminId) {
        try {
            const response = await fetch(`${this.baseUrl}/sub-admins/${subAdminId}/permissions`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching sub-admin permissions:', error);
            return {
                success: false,
                message: error.message,
                permissions: {}
            };
        }
    }

    /**
     * Create a new role (for future use)
     */
    async createRole(roleData) {
        try {
            const response = await fetch(`${this.baseUrl}/create`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(roleData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error creating role:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Update an existing role (for future use)
     */
    async updateRole(roleId, roleData) {
        try {
            const response = await fetch(`${this.baseUrl}/update/${roleId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(roleData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error updating role:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Delete a role (for future use)
     */
    async deleteRole(roleId) {
        try {
            const response = await fetch(`${this.baseUrl}/delete/${roleId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error deleting role:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Get all roles (for future use)
     */
    async getAllRoles() {
        try {
            const response = await fetch(`${this.baseUrl}/all`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching roles:', error);
            return {
                success: false,
                message: error.message,
                roles: []
            };
        }
    }

    /**
     * Get role by ID (for future use)
     */
    async getRoleById(roleId) {
        try {
            const response = await fetch(`${this.baseUrl}/get/${roleId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching role:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Check if current user has permission for a specific feature
     */
    async checkPermission(feature) {
        try {
            const response = await fetch(`${this.baseUrl}/check-permission/${feature}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error checking permission:', error);
            return {
                success: false,
                hasPermission: false,
                message: error.message
            };
        }
    }

    /**
     * Get current user's permissions
     */
    async getCurrentUserPermissions() {
        try {
            const response = await fetch(`${this.baseUrl}/my-permissions`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching current user permissions:', error);
            return {
                success: false,
                message: error.message,
                permissions: {}
            };
        }
    }

    /**
     * Bulk update permissions for multiple sub-admins
     */
    async bulkUpdatePermissions(updates) {
        try {
            const response = await fetch(`${this.baseUrl}/bulk-update-permissions`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ updates })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error bulk updating permissions:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Search sub-admins by name, email, or office
     */
    async searchSubAdmins(query) {
        try {
            const response = await fetch(`${this.baseUrl}/sub-admins/search?q=${encodeURIComponent(query)}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error searching sub-admins:', error);
            return {
                success: false,
                message: error.message,
                subAdmins: []
            };
        }
    }

    /**
     * Get permission statistics
     */
    async getPermissionStats() {
        try {
            const response = await fetch(`${this.baseUrl}/permission-stats`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching permission stats:', error);
            return {
                success: false,
                message: error.message,
                stats: {}
            };
        }
    }

    /**
     * Reset permissions to default for a sub-admin
     */
    async resetSubAdminPermissions(subAdminId) {
        try {
            const response = await fetch(`${this.baseUrl}/sub-admins/${subAdminId}/reset-permissions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error resetting sub-admin permissions:', error);
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Get default permissions for an office
     */
    async getDefaultPermissions(office) {
        try {
            const response = await fetch(`${this.baseUrl}/default-permissions/${encodeURIComponent(office)}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error fetching default permissions:', error);
            return {
                success: false,
                message: error.message,
                permissions: {}
            };
        }
    }

    /**
     * Validate permissions object
     */
    validatePermissions(permissions) {
        const validPermissions = [
            'dashboard',
            'conversations',
            'faq',
            'announcements',
            'usage',
            'feedback'
        ];

        if (!permissions || typeof permissions !== 'object') {
            return false;
        }

        // Check if all permission keys are valid
        for (const key in permissions) {
            if (!validPermissions.includes(key)) {
                return false;
            }
            if (typeof permissions[key] !== 'boolean') {
                return false;
            }
        }

        return true;
    }

    /**
     * Get permission labels for display
     */
    getPermissionLabels() {
        return {
            'dashboard': 'Dashboard',
            'conversations': 'Conversations',
            'faq': 'FAQ Management',
            'announcements': 'Announcements',
            'usage': 'Usage Statistics',
            'feedback': 'User Feedback'
        };
    }

    /**
     * Get all available permissions
     */
    getAvailablePermissions() {
        return [
            'dashboard',
            'conversations',
            'faq',
            'announcements',
            'usage',
            'feedback'
        ];
    }
}