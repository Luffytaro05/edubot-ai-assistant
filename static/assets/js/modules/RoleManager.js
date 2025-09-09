/**
 * RoleManager - Manages user roles and permissions
 */
class RoleManager extends BaseManager {
    constructor() {
        super('educhat_roles');
        this.initializeDefaultRoles();
    }

    /**
     * Initialize with default roles
     */
    initializeDefaultRoles() {
        if (this.data.length === 0) {
            const defaultRoles = [
                {
                    office: 'Registrar Office',
                    permissions: [
                        'Manage Office Content',
                        'View Office Analytics',
                        'Handle Escalations',
                        'View Logs'
                    ]
                },
                {
                    office: 'Admissions Office',
                    permissions: [
                        'Manage Office Content',
                        'View Office Analytics',
                        'Handle Escalations',
                        'View Logs'
                    ]
                },
                {
                    office: 'Guidance Office',
                    permissions: [
                        'Manage Office Content',
                        'View Office Analytics',
                        'Handle Escalations',
                        'View Logs'
                    ]
                }
            ];

            defaultRoles.forEach(role => this.addRole(role));
        }
    }

    /**
     * Add new role with validation
     */
    addRole(roleData) {
        // Validation
        if (!roleData.office || !roleData.permissions || roleData.permissions.length === 0) {
            return {
                success: false,
                message: 'Office and permissions are required'
            };
        }

        // Check if office already exists
        const existingRole = this.data.find(role => role.office === roleData.office);
        if (existingRole) {
            return {
                success: false,
                message: 'Role for this office already exists'
            };
        }

        // Create role object
        const role = {
            office: roleData.office.trim(),
            permissions: roleData.permissions.map(p => p.trim()),
            createdAt: new Date().toISOString()
        };

        const newRole = this.add(role);
        return {
            success: true,
            role: newRole
        };
    }

    /**
     * Update role with validation
     */
    updateRole(id, updates) {
        const role = this.getById(id);
        if (!role) {
            return {
                success: false,
                message: 'Role not found'
            };
        }

        // Check if office is being changed and if it already exists
        if (updates.office && updates.office !== role.office) {
            const existingRole = this.data.find(r => r.office === updates.office && r.id !== id);
            if (existingRole) {
                return {
                    success: false,
                    message: 'Role for this office already exists'
                };
            }
        }

        // Validate permissions
        if (updates.permissions && updates.permissions.length === 0) {
            return {
                success: false,
                message: 'At least one permission is required'
            };
        }

        const updatedRole = this.update(id, updates);
        return {
            success: true,
            role: updatedRole
        };
    }

    /**
     * Delete role
     */
    deleteRole(id) {
        const role = this.getById(id);
        if (!role) {
            return {
                success: false,
                message: 'Role not found'
            };
        }

        this.delete(id);
        return {
            success: true,
            message: 'Role deleted successfully'
        };
    }

    /**
     * Get role by office
     */
    getRoleByOffice(office) {
        return this.data.find(role => role.office === office);
    }

    /**
     * Get roles with permission count
     */
    getRolesWithPermissionCount() {
        return this.data.map(role => ({
            ...role,
            permissionCount: role.permissions.length
        }));
    }

    /**
     * Search roles by office or permissions
     */
    searchRoles(query) {
        const searchTerm = query.toLowerCase();
        return this.data.filter(role => 
            role.office.toLowerCase().includes(searchTerm) ||
            role.permissions.some(permission => 
                permission.toLowerCase().includes(searchTerm)
            )
        );
    }

    /**
     * Get all permissions
     */
    getAllPermissions() {
        const allPermissions = new Set();
        this.data.forEach(role => {
            role.permissions.forEach(permission => {
                allPermissions.add(permission);
            });
        });
        return Array.from(allPermissions);
    }

    /**
     * Get roles by permission
     */
    getRolesByPermission(permission) {
        return this.data.filter(role => 
            role.permissions.includes(permission)
        );
    }

    /**
     * Add permission to role
     */
    addPermissionToRole(roleId, permission) {
        const role = this.getById(roleId);
        if (!role) {
            return {
                success: false,
                message: 'Role not found'
            };
        }

        if (role.permissions.includes(permission)) {
            return {
                success: false,
                message: 'Permission already exists for this role'
            };
        }

        const updatedPermissions = [...role.permissions, permission];
        const updatedRole = this.update(roleId, { permissions: updatedPermissions });
        
        return {
            success: true,
            role: updatedRole
        };
    }

    /**
     * Remove permission from role
     */
    removePermissionFromRole(roleId, permission) {
        const role = this.getById(roleId);
        if (!role) {
            return {
                success: false,
                message: 'Role not found'
            };
        }

        if (!role.permissions.includes(permission)) {
            return {
                success: false,
                message: 'Permission does not exist for this role'
            };
        }

        const updatedPermissions = role.permissions.filter(p => p !== permission);
        
        if (updatedPermissions.length === 0) {
            return {
                success: false,
                message: 'Cannot remove all permissions from a role'
            };
        }

        const updatedRole = this.update(roleId, { permissions: updatedPermissions });
        
        return {
            success: true,
            role: updatedRole
        };
    }

    /**
     * Get role statistics
     */
    getStats() {
        const totalRoles = this.data.length;
        const totalPermissions = this.getAllPermissions().length;
        const averagePermissionsPerRole = totalRoles > 0 ? 
            this.data.reduce((sum, role) => sum + role.permissions.length, 0) / totalRoles : 0;

        const permissionsByRole = {};
        this.data.forEach(role => {
            permissionsByRole[role.office] = role.permissions.length;
        });

        return {
            totalRoles,
            totalPermissions,
            averagePermissionsPerRole: Math.round(averagePermissionsPerRole * 100) / 100,
            permissionsByRole
        };
    }

    /**
     * Check if user has permission
     */
    hasPermission(userOffice, permission) {
        const role = this.getRoleByOffice(userOffice);
        if (!role) return false;
        
        return role.permissions.includes(permission);
    }

    /**
     * Get user permissions
     */
    getUserPermissions(userOffice) {
        const role = this.getRoleByOffice(userOffice);
        return role ? role.permissions : [];
    }
}
