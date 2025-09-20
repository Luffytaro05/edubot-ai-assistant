/**
 * UserManager.js
 * Handles frontend user management requests and communicates with Flask backend.
 */
class UserManager {
    constructor() {
        this.baseUrl = "/api/users";
    }

    async getAll() {
        try {
            const res = await fetch(this.baseUrl);
            return await res.json();
        } catch (err) {
            console.error("Error fetching users:", err);
            return [];
        }
    }

    async addUser(userData) {
        try {
            const res = await fetch(this.baseUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(userData)
            });
            return await res.json();
        } catch (err) {
            console.error("Error adding user:", err);
            return { success: false, message: "Error adding user" };
        }
    }

    async getById(userId) {
        try {
            const res = await fetch(`${this.baseUrl}/${userId}`);
            return await res.json();
        } catch (err) {
            console.error("Error fetching user:", err);
            return null;
        }
    }

    async updateUser(userId, updates) {
        try {
            const res = await fetch(`${this.baseUrl}/${userId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
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
            const res = await fetch(`${this.baseUrl}/${userId}/toggle`, {
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
            const res = await fetch(`${this.baseUrl}/${userId}`, {
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
}

async function loadUsers() {
    try {
        const response = await fetch("/api/users");  // Flask endpoint
        const users = await response.json();

        const tableBody = document.getElementById("users-table-body");
        tableBody.innerHTML = ""; // Clear existing rows

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
    const result = await userManager.delete(userId);
    if (result.success) {
        alert("User deleted successfully!");
        loadUsersTable();
    } else {
        alert("Error deleting user");
    }
}

// Call this when page loads
document.addEventListener("DOMContentLoaded", loadUsers);
