/**
 * UserManager - Manages sub-admin user accounts
 */
class UserManager extends BaseManager {
    constructor() {
        super('educhat_users');
        this.initializeDefaultUsers();
    }

    /**
     * Initialize with default users
     */
    initializeDefaultUsers() {
        if (this.data.length === 0) {
            const defaultUsers = [
                {
                    name: 'Jelson Umpacan',
                    email: 'jelson.umpacan@example.com',
                    office: 'Registrar Office',
                    role: 'Sub Admin',
                    status: 'Active',
                    lastLogin: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() // 2 hours ago
                },
                {
                    name: 'Lawrence Ignacio',
                    email: 'lawrence.ignacio@example.com',
                    office: 'Accounting Office',
                    role: 'Sub Admin',
                    status: 'Active',
                    lastLogin: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString() // 4 hours ago
                },
                {
                    name: 'Dexter Zapico',
                    email: 'dexter.zapico@example.com',
                    office: 'Guidance Office',
                    role: 'Sub Admin',
                    status: 'Inactive',
                    lastLogin: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // 1 day ago
                },
                {
                    name: 'Gerald Diasanta',
                    email: 'gerald.diasanta@example.com',
                    office: 'Admissions Office',
                    role: 'Sub Admin',
                    status: 'Active',
                    lastLogin: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString() // 1 hour ago
                }
            ];

            defaultUsers.forEach(user => this.addUser(user));
        }
    }

    /**
     * Add new user with validation
     */
    addUser(userData) {
        // Validation
        if (!userData.name || !userData.email || !userData.office || !userData.role) {
            return {
                success: false,
                message: 'All fields are required'
            };
        }

        // Check if email already exists
        const existingUser = this.data.find(user => user.email === userData.email);
        if (existingUser) {
            return {
                success: false,
                message: 'Email already exists'
            };
        }

        // Create user object
        const user = {
            name: userData.name.trim(),
            email: userData.email.trim().toLowerCase(),
            office: userData.office,
            role: userData.role,
            status: userData.status || 'Active',
            password: userData.password || 'default123', // In real app, hash the password
            lastLogin: null
        };

        const newUser = this.add(user);
        return {
            success: true,
            user: newUser
        };
    }

    /**
     * Update user with validation
     */
    updateUser(id, updates) {
        const user = this.getById(id);
        if (!user) {
            return {
                success: false,
                message: 'User not found'
            };
        }

        // Check if email is being changed and if it already exists
        if (updates.email && updates.email !== user.email) {
            const existingUser = this.data.find(u => u.email === updates.email && u.id !== id);
            if (existingUser) {
                return {
                    success: false,
                    message: 'Email already exists'
                };
            }
        }

        // Update password if provided
        if (updates.password) {
            updates.password = updates.password; // In real app, hash the password
        }

        const updatedUser = this.update(id, updates);
        return {
            success: true,
            user: updatedUser
        };
    }

    /**
     * Toggle user status
     */
    toggleStatus(id) {
        const user = this.getById(id);
        if (!user) {
            return {
                success: false,
                message: 'User not found'
            };
        }

        const newStatus = user.status === 'Active' ? 'Inactive' : 'Active';
        const updatedUser = this.update(id, { status: newStatus });
        
        return {
            success: true,
            newStatus: newStatus,
            user: updatedUser
        };
    }

    /**
     * Get users by office
     */
    getUsersByOffice(office) {
        return this.data.filter(user => user.office === office);
    }

    /**
     * Get users by status
     */
    getUsersByStatus(status) {
        return this.data.filter(user => user.status === status);
    }

    /**
     * Search users by name or email
     */
    searchUsers(query) {
        const searchTerm = query.toLowerCase();
        return this.data.filter(user => 
            user.name.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm) ||
            user.office.toLowerCase().includes(searchTerm)
        );
    }

    /**
     * Get active users count
     */
    getActiveUsersCount() {
        return this.data.filter(user => user.status === 'Active').length;
    }

    /**
     * Get user statistics
     */
    getStats() {
        const totalUsers = this.data.length;
        const activeUsers = this.data.filter(user => user.status === 'Active').length;
        const inactiveUsers = totalUsers - activeUsers;

        const usersByOffice = {};
        const offices = ['Registrar Office', 'Accounting Office', 'Guidance Office', 'Admissions Office', 'ICT Office'];
        
        offices.forEach(office => {
            usersByOffice[office] = this.data.filter(user => user.office === office).length;
        });

        const usersByRole = {};
        const roles = ['Sub Admin', 'Manager', 'Staff'];
        
        roles.forEach(role => {
            usersByRole[role] = this.data.filter(user => user.role === role).length;
        });

        return {
            totalUsers,
            activeUsers,
            inactiveUsers,
            usersByOffice,
            usersByRole
        };
    }

    /**
     * Update last login time
     */
    updateLastLogin(id) {
        const user = this.getById(id);
        if (user) {
            this.update(id, { lastLogin: new Date().toISOString() });
        }
    }

    /**
     * Get recent users
     */
    getRecentUsers(limit = 5) {
        return this.data
            .filter(user => user.lastLogin)
            .sort((a, b) => new Date(b.lastLogin) - new Date(a.lastLogin))
            .slice(0, limit);
    }
}
