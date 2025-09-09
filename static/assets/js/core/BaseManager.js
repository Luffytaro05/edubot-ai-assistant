/**
 * BaseManager - Core class for managing data with localStorage persistence
 * Provides common CRUD operations and data management functionality
 */
class BaseManager {
    constructor(storageKey) {
        this.storageKey = storageKey;
        this.data = [];
        this.loadData();
    }

    /**
     * Load data from localStorage
     */
    loadData() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            this.data = stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error(`Error loading data for ${this.storageKey}:`, error);
            this.data = [];
        }
    }

    /**
     * Save data to localStorage
     */
    saveData() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.data));
        } catch (error) {
            console.error(`Error saving data for ${this.storageKey}:`, error);
        }
    }

    /**
     * Get all items
     */
    getAll() {
        return [...this.data];
    }

    /**
     * Get item by ID
     */
    getById(id) {
        return this.data.find(item => item.id === id);
    }

    /**
     * Add new item
     */
    add(item) {
        const newItem = {
            ...item,
            id: this.generateId(),
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        
        this.data.push(newItem);
        this.saveData();
        return newItem;
    }

    /**
     * Update existing item
     */
    update(id, updates) {
        const index = this.data.findIndex(item => item.id === id);
        if (index === -1) {
            return null;
        }

        this.data[index] = {
            ...this.data[index],
            ...updates,
            updatedAt: new Date().toISOString()
        };

        this.saveData();
        return this.data[index];
    }

    /**
     * Delete item by ID
     */
    delete(id) {
        const index = this.data.findIndex(item => item.id === id);
        if (index === -1) {
            return false;
        }

        this.data.splice(index, 1);
        this.saveData();
        return true;
    }

    /**
     * Search items by field and value
     */
    search(field, value) {
        return this.data.filter(item => {
            const fieldValue = item[field];
            if (typeof fieldValue === 'string') {
                return fieldValue.toLowerCase().includes(value.toLowerCase());
            }
            return fieldValue === value;
        });
    }

    /**
     * Filter items by criteria
     */
    filter(criteria) {
        return this.data.filter(item => {
            return Object.keys(criteria).every(key => {
                const itemValue = item[key];
                const criteriaValue = criteria[key];
                
                if (typeof itemValue === 'string' && typeof criteriaValue === 'string') {
                    return itemValue.toLowerCase().includes(criteriaValue.toLowerCase());
                }
                return itemValue === criteriaValue;
            });
        });
    }

    /**
     * Generate unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * Clear all data
     */
    clear() {
        this.data = [];
        this.saveData();
    }

    /**
     * Get count of items
     */
    getCount() {
        return this.data.length;
    }
}
